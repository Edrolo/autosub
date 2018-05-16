from os import (
    environ,
    path,
)

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


def generate_subtitles(source_path, **extra_options):
    transcript = recognize(
        source_path=source_path,
        hint_phrases=extra_options.get('hint_phrases', []),
    )
    single_line_sentences = [
        ((sentence.start_time, sentence.end_time), str(sentence))
        for sentence in transcript.sentences()
    ]
    log.debug(single_line_sentences)
    return single_line_sentences


def recognize(source_path, hint_phrases=None):
    # Imports the Google Cloud client library
    from google.cloud import speech_v1p1beta1 as speech
    hint_phrases = hint_phrases or []

    log.debug('Extracting audio from {}'.format(source_path))
    audio_filename, audio_rate = extract_audio(source_path, extension='flac')
    log.debug('Extracted {}'.format(audio_filename))

    # Instantiates a client
    client = speech.SpeechClient()

    config = speech.types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=audio_rate,  # Not required with FLAC or WAV when sending audio data
        language_code='en-US',
        model='video',
        profanity_filter=True,
        speech_contexts=[
            speech.proto.cloud_speech_pb2.SpeechContext(
                phrases=hint_phrases,
            ),
        ],
        enable_automatic_punctuation=True,
        enable_word_time_offsets=True,
    )

    # Async GC Storage method (required for files with duration longer than 180 seconds)
    uri = upload_blob(
        bucket_name=environ.get('GOOGLE_STORAGE_BUCKET'),
        source_file_name=audio_filename,
    )
    audio = {'uri': uri}

    # Direct method - can be used for files with duration < 180 seconds
    # import io
    # with io.open(source_path, 'rb') as audio_file:
    #     content = audio_file.read()
    #     audio = speech.types.RecognitionAudio(content=content)

    # Common to Async methods
    # Detects speech in the audio file
    log.debug(f'Starting recognition with audio: {audio}')
    operation = client.long_running_recognize(config, audio)
    log.debug('Started operation')

    # Also possible to use a callback for async recognition:
    # def callback(operation_future):
    #     # Handle result.
    #     log.debug('Entered callback')
    #     result = operation_future.result()
    #     log.debug('Result returned')
    # operation.add_done_callback(callback)
    # metadata = operation.metadata()  # TypeError: 'NoneType' object is not callable

    # Synchronous method (possible for files of < 60 seconds)
    # response = client.recognize(config, audio)

    log.info('Waiting for recognition to complete...')
    recognize_response = operation.result(timeout=90)

    p(recognize_response.results)

    # for result in response.results:
    #     print('Transcript: {}'.format(result.alternatives[0].transcript))

    word_info_list = build_word_info_list_from_cloud_speech_recognize_response(
        recognize_response=recognize_response,
    )

    return Transcript(word_info_list)


def upload_blob(bucket_name, source_file_name):
    """Uploads a file to the bucket."""
    from google.cloud import storage
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    file_path, file_name = path.split(source_file_name)
    destination_blob_name = file_name
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    log.debug(f'blob: {vars(blob)}')
    return f'gs://{bucket_name}/{blob.name}'
