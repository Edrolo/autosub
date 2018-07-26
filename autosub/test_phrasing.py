import pytest
import yaml

from autosub.phrasing import (
    Transcript,
    WordInfo,
)
from autosub.recognizers.google_cloud_speech import remove_ums

example_google_cloud_speech_json = {
    'alternatives': [{
        'transcript': "Hello there.",
        'confidence': 0.9235186576843262,
        'words': [
            {
                'word': "Hello",
                'start_time': {
                    'seconds': 0,
                    'nanos': 100000000,
                },
                'end_time': {
                    'seconds': 1,
                    'nanos': 000000000,
                },
            },
            {
                'word': "there.",
                'start_time': {
                    'seconds': 1,
                    'nanos': 100000000,
                },
                'end_time': {
                    'seconds': 1,
                    'nanos': 500000000,
                },
            },
        ],
    }],
}


example_amazon_transcribe_json = {
    "jobName": "test-job-1",
    "accountId": "123456789012",
    "results": {
        "transcripts": [
            {
                "transcript": "Hello there.",
            },
        ],
        "items": [
            {
                "start_time": "0.100",
                "end_time": "1.000",
                "alternatives": [
                    {
                        "confidence": "0.8000",
                        "content": "Hello",
                    }
                ],
                "type": "pronunciation",
            },
            {
                "start_time": "1.100",
                "end_time": "1.500",
                "alternatives": [
                    {
                        "confidence": "0.9000",
                        "content": "Hello",
                    }
                ],
                "type": "pronunciation",
            },
            {
                "alternatives": [
                    {
                        "content": ".",
                    },
                ],
                "type": "punctuation",
            },
        ],
        "status": "COMPLETED",
    }
}


@pytest.fixture
def transcript_from_file():
    with open('example_google_cloud_speech_transcript.yaml', 'rb') as f:
        example_google_cloud_speech = yaml.load(f)

    transcript = Transcript.from_google_cloud_speech_recognize_response_json(
        example_google_cloud_speech,
    )

    return transcript


@pytest.fixture
def hello_there_transcript():
    transcript = Transcript.from_google_cloud_speech_recognize_response_json(
        example_google_cloud_speech_json,
    )
    return transcript


@pytest.fixture
def single_sentence_with_ums():
    test_sentence_string = 'Hello, um, my name is um... Monty.'
    return sentence_factory(test_sentence_string)


@pytest.fixture
def really_long_sentence():
    test_sentence_string = (
        "So they kind of work out what it is that we want to know "
        "more information about it and make sure the information "
        "gets disseminated to the people that need to know it "
        "and they monitor health trends they need to they're sort of "
        "identifying the fact that for example, we identified that "
        "non-communicable diseases were starting to have more of an impact "
        "on health status and burden of disease."
    )
    return sentence_factory(test_sentence_string)


def test_three_periods_does_not_end_a_sentence():
    test_sentence_string = 'What... are you doing?'
    sentence = sentence_factory(test_sentence_string)
    assert str(sentence) == test_sentence_string


def test_equality():
    test_sentence_string = 'What... are you doing?'
    sentence_1 = sentence_factory(test_sentence_string)
    sentence_2 = sentence_factory(test_sentence_string)
    assert sentence_1 == sentence_2


def test_transcript_find_end_of_next_sentence(hello_there_transcript):
    end_of_next_sentence = hello_there_transcript._find_end_of_next_sentence(starting_from=0)
    assert end_of_next_sentence == 2
    assert hello_there_transcript.word_info_list[end_of_next_sentence-1].word == 'there.'


def test_transcript_get_sentence(hello_there_transcript):
    sentence = hello_there_transcript._get_word_sequence(0, 3)
    assert len(sentence) == 2
    assert str(sentence) == 'Hello there.'


def test_transcript_with_single_sentence_gives_one_sentence(hello_there_transcript):
    sentences = list(hello_there_transcript.sentences)
    assert len(sentences) == 1
    assert str(sentences[0]) == 'Hello there.'


def test_sentence_breakup(transcript_from_file):
    sentences = list(transcript_from_file.sentences)
    assert [str(sentence) for sentence in sentences] == [
        "This lesson is the first lesson in the course.",
        "Today we're going to be having a look at the syllabus.",
    ]


def test_sentences_property(single_sentence_with_ums):
    sentence_without_ums = single_sentence_with_ums.filter(remove_ums)
    assert str(sentence_without_ums) == 'Hello, my name is Monty.'


def test_sentence_remove_um_filter(single_sentence_with_ums):
    sentence_without_ums = single_sentence_with_ums.filter(remove_ums)
    assert str(sentence_without_ums) == 'Hello, my name is Monty.'


def transcript_factory(string_of_words):
    words = string_of_words.split()
    print('Factoring words:')
    print(words)
    word_info_list = [
        WordInfo(word, start_time=index, end_time=index+1)
        for index, word in enumerate(words)
    ]
    transcript = Transcript(word_info_list=word_info_list)
    print(transcript)
    return transcript


def sentence_factory(string_of_words):
    return next(transcript_factory(string_of_words).sentences)
