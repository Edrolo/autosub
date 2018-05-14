print('importing translators.py')
from googleapiclient.discovery import build


class Translator(object):
    def __init__(self, language, api_key, src, dst):
        self.language = language
        self.api_key = api_key
        self.service = build(
            'translate', 'v2', developerKey=self.api_key)
        self.src = src
        self.dst = dst

    def __call__(self, sentence):
        try:
            if not sentence:
                return
            result = self.service.translations().list(
                source=self.src,
                target=self.dst,
                q=[sentence]
            ).execute()
            if (
                'translations' in result
                and len(result['translations'])
                and 'translatedText' in result['translations'][0]
            ):
                return result['translations'][0]['translatedText']
            return ""

        except KeyboardInterrupt:
            return

print('Finished importing translators.py')
