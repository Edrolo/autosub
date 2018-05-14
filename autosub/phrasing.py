print('importing phrasing.py')
from typing import NamedTuple

import logging
log = logging.getLogger(__name__)


class WordInfo(NamedTuple):
    word: str
    start_time: float
    end_time: float

    @classmethod
    def from_google_cloud_speech_word_info_dict(cls, data):
        return cls(
            word=data['word'],
            start_time=data['start_time'].get('seconds', 0) + data['start_time'].get('nanos', 0) * 1e-9,
            end_time=data['end_time'].get('seconds', 0) + data['end_time'].get('nanos', 0) * 1e-9,
        )

    @classmethod
    def from_google_cloud_speech_word_info(cls, gc_word_info):
        return cls(
            word=gc_word_info.word,
            start_time=gc_word_info.start_time.seconds + gc_word_info.start_time.nanos * 1e-9,
            end_time=gc_word_info.end_time.seconds + gc_word_info.end_time.nanos * 1e-9,
        )

    def __str__(self):
        return f'Word: {self.word}, start_time: {self.start_time}, end_time: {self.end_time}'

    @property
    def is_punctuation(self):
        return self.word in ',.!?'

    @property
    def ends_sentence(self):
        return self.word[-1] in '.!?'


class Sentence:
    word_info_list = []

    def __init__(self, word_info_list=None):
        self.word_info_list = word_info_list or []

    def __str__(self):
        return ' '.join((
            word_info.word for word_info in self.word_info_list
        ))

    def __len__(self):
        words = [word_info for word_info in self.word_info_list if not word_info.is_punctuation]
        return len(words)

    @property
    def start_time(self):
        return self.word_info_list[0].start_time

    @property
    def end_time(self):
        return self.word_info_list[-1].end_time

    @property
    def duration(self):
        return self.end_time - self.start_time


class Transcript:
    word_info_list = []

    def __init__(self, word_info_list=None):
        self.word_info_list = word_info_list or []

    @classmethod
    def from_google_cloud_speech_recognize_response_json(cls, response_json):
        word_info_list = [
            WordInfo.from_google_cloud_speech_word_info_dict(
                data=word_info_data,
            )
            for word_info_data in response_json['alternatives'][0]['words']
        ]
        return cls(word_info_list=word_info_list)

    def find_end_of_next_sentence(self, starting_from=0):
        for index, word_info in enumerate(self.word_info_list[starting_from:], start=starting_from):
            log.debug(f'{index}: {word_info}')
            if word_info.ends_sentence:
                return index + 1
        return len(self.word_info_list) + 1

    def get_sentence(self, start, end):
        return Sentence(self.word_info_list[start:end])

    def sentences(self):
        next_index = 0
        # sentences = []

        while next_index < len(self.word_info_list):
            end_of_next_sentence = self.find_end_of_next_sentence(starting_from=next_index)
            log.debug(f'Found end of next sentence at {end_of_next_sentence}')
            next_sentence = self.get_sentence(start=next_index, end=end_of_next_sentence)
            log.debug(f'Got next sentence from {next_index} to {end_of_next_sentence}: {next_sentence}')
            next_index = end_of_next_sentence
            yield next_sentence
            # sentences.append(next_sentence)

        # return sentences


def build_word_info_list_from_cloud_speech_recognize_response(recognize_response):
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

print('finished importing phrasing.py')
