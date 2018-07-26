from typing import (
    NamedTuple,
    List,
)

import logging
log = logging.getLogger(__name__)


def as_seconds(seconds=0, nanos=0):
    return seconds + nanos * 1e-9


class WordInfo(NamedTuple):
    word: str
    start_time: float
    end_time: float

    punctuation_characters = ',.!?'

    @classmethod
    def from_google_cloud_speech_word_info_dict(cls, data):
        return cls(
            word=data['word'],
            start_time=as_seconds(
                seconds=data['start_time'].get('seconds', 0),
                nanos=data['start_time'].get('nanos', 0),
            ),
            end_time=as_seconds(
                seconds=data['end_time'].get('seconds', 0),
                nanos=data['end_time'].get('nanos', 0),
            ),
        )

    @classmethod
    def from_google_cloud_speech_word_info(cls, gc_word_info):
        return cls(
            word=gc_word_info.word,
            start_time=as_seconds(
                seconds=gc_word_info.start_time.seconds,
                nanos=gc_word_info.start_time.nanos,
            ),
            end_time=as_seconds(
                seconds=gc_word_info.end_time.seconds,
                nanos=gc_word_info.end_time.nanos,
            ),
        )

    def __str__(self):
        return f'Word: "{self.word}" start_time: {self.start_time} end_time: {self.end_time}'

    @property
    def is_punctuation(self):
        return self.word in self.punctuation_characters

    @property
    def ends_sentence(self):
        sentence_ending_strings = ('.', '!', '?', '."', '!"', '?"')
        misleading_strings = ('...', )
        return (self.word.endswith(sentence_ending_strings)
                and not self.word.endswith(misleading_strings))

    @property
    def without_punctuation(self):
        return self.word.strip(self.punctuation_characters)

    @property
    def capitalized(self):
        return WordInfo(
            word=self.word[0].upper() + self.word[1:],
            start_time=self.start_time,
            end_time=self.end_time,
        )


class WordSequence:
    word_info_list = []

    def __init__(self, word_info_list: List[WordInfo]):
        if not word_info_list:
            raise ValueError('Cannot create a WordSequence with an empty word_info_list')
        self.word_info_list = word_info_list

    def __str__(self):
        return ' '.join((word_info.word for word_info in self.word_info_list))

    def __len__(self):
        words = [
            word_info for word_info in self.word_info_list
            if not word_info.is_punctuation
        ]
        return len(words)

    def __eq__(self, other):
        if isinstance(other, WordSequence):
            return (len(self.word_info_list) == len(other.word_info_list)
                    and all(my_word == their_word
                            for (my_word, their_word) in zip(
                                self.word_info_list, other.word_info_list)))
        return False

    def transform(self, func):
        """Accepts a transform function that accepts a `WordSequence` as a parameter
        and returns a list of `WordInfo`s
        Returns a generator of new `WordSequences` built from the list of `WordInfo`s
        """
        return (WordSequence(word_info_list) for word_info_list in func(self))

    @property
    def start_time(self):
        return self.word_info_list[0].start_time

    @property
    def end_time(self):
        return self.word_info_list[-1].end_time

    @property
    def duration(self):
        return self.end_time - self.start_time

    def wrap(self, width=0):
        """Split the sequence into a list of sequences, all with less than x characters"""
        if width <= 0:
            return [WordSequence(self.word_info_list)]

        sequences = []
        current_word_info_list = []

        for word in self.word_info_list:

            # Create a new sequence with one more word, and test its length
            # (Not a very efficient algorithm)
            new_sequence = WordSequence(current_word_info_list + [word])

            if len(str(new_sequence)) > width:
                # We're past the max line length now

                # If a single word is longer than the max, just put it on a line by itself.
                if len(new_sequence) == 1:
                    sequences.append(new_sequence)
                    # sequences.append(current_sequence)

                # If we have words in the current word list already, add that sequence to the list
                # Reset the current word list to just the new word.
                else:
                    sequence_without_extra_word = WordSequence(current_word_info_list)
                    sequences.append(sequence_without_extra_word)
                    current_word_info_list = [word]

            else:
                # The word fits on the line, so add it to the current word list
                current_word_info_list.append(word)

        # Catch the last one
        if current_word_info_list:
            sequences.append(WordSequence(current_word_info_list))

        return sequences


class Transcript:
    word_info_list = []

    def __init__(self, word_info_list=None):
        self.word_info_list = word_info_list or []

    @classmethod
    def from_google_cloud_speech_recognize_response_json(cls, response_json):
        word_info_list = [
            WordInfo.from_google_cloud_speech_word_info_dict(
                data=word_info_data, )
            for word_info_data in response_json['alternatives'][0]['words']
        ]
        return cls(word_info_list=word_info_list)

    def _find_end_of_next_sentence(self, starting_from=0):
        for index, word_info in enumerate(
                self.word_info_list[starting_from:],
                start=starting_from,
        ):
            # log.debug(f'{index}: {word_info}')
            if word_info.ends_sentence:
                # Found the end of the sentence by punctuation
                return index + 1
        # Reached the end of the list without sentence-ending punctuation
        return len(self.word_info_list) + 1

    def _get_word_sequence(self, start, end):
        return WordSequence(self.word_info_list[start:end])

    @property
    def sentences(self):
        next_index = 0

        while next_index < len(self.word_info_list):
            end_of_next_sentence = self._find_end_of_next_sentence(
                starting_from=next_index, )
            log.debug(f'Found end of next sentence at {end_of_next_sentence}')
            next_sentence = self._get_word_sequence(
                start=next_index,
                end=end_of_next_sentence,
            )
            log.debug(
                f'Got next sentence from {next_index} to {end_of_next_sentence}: {next_sentence}'
            )
            next_index = end_of_next_sentence
            yield next_sentence


def build_word_info_list_from_cloud_speech_recognize_response(
    recognize_response,
):
    word_info_list = []
    for result in recognize_response.results:
        alternative = result.alternatives[0]
        log.debug(f'Transcript: {alternative.transcript}')
        log.debug(f'Confidence: {alternative.confidence}')

        word_info_list += [
            WordInfo.from_google_cloud_speech_word_info(word_info)
            for word_info in alternative.words
        ]

    return word_info_list


# Guidelines from http://translationjournal.net/journal/04stndrd.htm:
# Target number of characters per line: <35
# Number of simultaneous lines: 1-2
# Max rate of display: 150-180 words per minute = 2.5-3 words per second
# Target duration of a full two-line subtitle containing 14-16 words: 6 seconds
# Target duration of a full single-line subtitle of 7-8 words: 3.5 seconds
# Target duration of a single-word subtitle: 1.5 seconds
# Leading-in time (delay between speaking and subtitle display): 0.25 seconds
# Lagging-out time (delay between end of speech and subtitle disappearance): <2 sec
# Gap between consecutive subtitles: 0.25 seconds
# It is better to segment a long single-line subtitle into a two-line subtitle,
#   distributing the words on each line.
# Subtitled text should appear segmented at the highest syntactic nodes possible.
#   This means that each subtitle flash should ideally contain one complete sentence.

MAX_CHARACTERS_PER_LINE = 35
MAX_LINES_VISIBLE = 2
