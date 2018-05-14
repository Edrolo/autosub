import io

from autosub.phrasing import (
    build_word_info_list_from_cloud_speech_recognize_response,
    Transcript,
)
from autosub.utils import extract_audio

from pprint import pprint as p
"""
Grab flac from video: ffmpeg -i video.mp4 audio.flac
Audio needs to be in mono: ffmpeg -i stereo.flac -ac 1 mono.flac
https://cloud.google.com/speech-to-text/docs/reference/rpc/google.cloud.speech.v1p1beta1
"""

import logging
log = logging.getLogger(__name__)


def generate_subtitles(source_path, *args, **kwargs):
    log.debug('Extracting audio from {}'.format(source_path))
    audio_filename, audio_rate = extract_audio(source_path, extension='flac')
    log.debug('Extracted {}'.format(audio_filename))

    transcript = recognize(audio_filename)
    single_line_sentences = [
        ((sentence.start_time, sentence.end_time), str(sentence))
        for sentence in transcript.sentences()
    ]
    p(single_line_sentences)
    return single_line_sentences


def recognize(source_path):
    # Imports the Google Cloud client library
    from google.cloud import speech_v1p1beta1 as speech

    # Instantiates a client
    client = speech.SpeechClient()

    # Loads the audio into memory
    with io.open(source_path, 'rb') as audio_file:
        content = audio_file.read()
        audio = speech.types.RecognitionAudio(content=content)

    config = speech.types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.FLAC,
        # sample_rate_hertz=44100,  # Not required with FLAC or WAV
        language_code='en-US',
        model='video',
        profanity_filter=True,
        speech_contexts=[
            speech.proto.cloud_speech_pb2.SpeechContext(
                phrases=['PDHPE', 'core', ],
            ),
        ],
        enable_automatic_punctuation=True,
        enable_word_time_offsets=True,
    )

    # Detects speech in the audio file
    # response = client.recognize(config, audio)
    log.debug('Starting recognition')
    operation = client.long_running_recognize(config, audio)

    log.info('Waiting for recognition to complete...')
    recognize_response = operation.result(timeout=90)

    p(recognize_response.results)

    # for result in response.results:
    #     print('Transcript: {}'.format(result.alternatives[0].transcript))

    word_info_list = build_word_info_list_from_cloud_speech_recognize_response(
        recognize_response=recognize_response,
    )

    return Transcript(word_info_list)
