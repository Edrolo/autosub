from . import (
    google_speech,
    google_cloud_speech,
)

RECOGNIZERS = {
    'google_speech': 'Google Speech API',
    'google_cloud_speech': 'Google Cloud Speech API https://cloud.google.com/speech-to-text/',
    'aws_transcribe': 'AWS Transcribe (not implemented) https://aws.amazon.com/transcribe/',
}

__all__ = [
    'google_speech',
    'google_cloud_speech',
    'RECOGNIZERS',
]
