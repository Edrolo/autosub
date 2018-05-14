import pytest
import yaml

from autosub.phrasing import Transcript


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


def test_transcript_find_end_of_next_sentence(hello_there_transcript):
    end_of_next_sentence = hello_there_transcript.find_end_of_next_sentence(starting_from=0)
    assert end_of_next_sentence == 2
    assert hello_there_transcript.word_info_list[end_of_next_sentence-1].word == 'there.'


def test_transcript_get_sentence(hello_there_transcript):
    sentence = hello_there_transcript.get_sentence(0, 3)
    assert len(sentence) == 2
    assert str(sentence) == 'Hello there.'


def test_transcript_with_single_sentence_gives_one_sentence(hello_there_transcript):
    sentences = list(hello_there_transcript.sentences())
    assert len(sentences) == 1
    assert str(sentences[0]) == 'Hello there.'


def test_sentence_breakup(transcript_from_file):
    sentences = list(transcript_from_file.sentences())
    assert [str(sentence) for sentence in sentences] == [
        "This lesson is the first lesson in the course.",
        "Today we're going to be having a look at the syllabus.",
    ]
