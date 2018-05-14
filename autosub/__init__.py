#!/usr/bin/env python
from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
)

import argparse
import importlib
import os
import sys

from autosub.constants import (
    LANGUAGE_CODES,
    DEFAULT_CONCURRENCY,
    DEFAULT_SUBTITLE_FORMAT,
    DEFAULT_SRC_LANGUAGE,
    DEFAULT_DST_LANGUAGE,
    DEFAULT_RECOGNIZER,
)
from autosub.formatters import FORMATTERS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source_path', help="Path to the video or audio file to subtitle",
                        nargs='?')
    parser.add_argument('-C', '--concurrency', help="Number of concurrent API requests to make",
                        type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument('-o', '--output',
                        help="Output path for subtitles (by default, subtitles are saved in \
                        the same directory and name as the source path)")
    parser.add_argument('-F', '--format', help="Destination subtitle format",
                        default=DEFAULT_SUBTITLE_FORMAT)
    parser.add_argument('-S', '--src-language', help="Language spoken in source file",
                        default=DEFAULT_SRC_LANGUAGE)
    parser.add_argument('-D', '--dst-language', help="Desired language for the subtitles",
                        default=DEFAULT_DST_LANGUAGE)
    parser.add_argument('-K', '--api-key',
                        help="The Google Translate API key to be used. (Required for subtitle translation)")
    parser.add_argument('--list-formats', help="List all available subtitle formats",
                        action='store_true')
    parser.add_argument('--list-languages', help="List all available source/destination languages",
                        action='store_true')

    args = parser.parse_args()

    if args.list_formats:
        print("List of formats:")
        for subtitle_format in FORMATTERS.keys():
            print("{format}".format(format=subtitle_format))
        return 0

    if args.list_languages:
        print("List of all languages:")
        for code, language in sorted(LANGUAGE_CODES.items()):
            print("{code}\t{language}".format(code=code, language=language))
        return 0

    if args.format not in FORMATTERS.keys():
        print(
            "Subtitle format not supported. "
            "Run with --list-formats to see all supported formats."
        )
        return 1

    if args.src_language not in LANGUAGE_CODES.keys():
        print(
            "Source language not supported. "
            "Run with --list-languages to see all supported languages."
        )
        return 1

    if args.dst_language not in LANGUAGE_CODES.keys():
        print(
            "Destination language not supported. "
            "Run with --list-languages to see all supported languages."
        )
        return 1

    if not args.source_path:
        print("Error: You need to specify a source path.")
        return 1

    try:
        timed_subtitle_filename = generate_subtitle_file(
            source_path=args.source_path,
            dst_subtitle_filename=args.output,
            concurrency=args.concurrency,
            src_language=args.src_language,
            dst_language=args.dst_language,
            subtitle_file_format=args.format,
            google_translate_api_key=args.api_key,
        )

        print("Subtitles file created at {}".format(timed_subtitle_filename))
    except KeyboardInterrupt:
        return 1

    return 0


def generate_subtitle_filename(source_path, subtitle_file_format):
    base, ext = os.path.splitext(source_path)
    subtitle_filename = "{base}.{format}".format(
        base=base,
        format=subtitle_file_format,
    )
    return subtitle_filename


def export_subtitles(subtitles, subtitle_file_name, subtitle_file_format):
    formatter = FORMATTERS.get(subtitle_file_format)
    formatted_subtitles = formatter(subtitles)

    with open(subtitle_file_name, 'wb') as f:
        f.write(formatted_subtitles.encode("utf-8"))


def generate_subtitle_file(
    source_path,
    dst_subtitle_filename='',
    concurrency=DEFAULT_CONCURRENCY,
    src_language=DEFAULT_SRC_LANGUAGE,
    dst_language=DEFAULT_DST_LANGUAGE,
    subtitle_file_format=DEFAULT_SUBTITLE_FORMAT,
    recognizer=DEFAULT_RECOGNIZER,
    google_translate_api_key=None,
):
    timed_subtitles = generate_subtitles(
        source_path=source_path,
        concurrency=concurrency,
        src_language=src_language,
        dst_language=dst_language,
        recognizer=recognizer,
        google_translate_api_key=google_translate_api_key,
    )

    dst_subtitle_filename = dst_subtitle_filename or generate_subtitle_filename(source_path, subtitle_file_format)

    export_subtitles(
        subtitles=timed_subtitles,
        subtitle_file_name=dst_subtitle_filename,
        subtitle_file_format=subtitle_file_format,
    )

    return dst_subtitle_filename


def generate_subtitles(
    source_path,
    concurrency=DEFAULT_CONCURRENCY,
    src_language=DEFAULT_SRC_LANGUAGE,
    dst_language=DEFAULT_DST_LANGUAGE,
    recognizer=DEFAULT_RECOGNIZER,
    google_translate_api_key=None,
):
    recognizer_module = importlib.import_module(f'autosub.recognizers.{recognizer}')

    subtitles = recognizer_module.generate_subtitles(
        source_path=source_path,
        concurrency=concurrency,
        src_language=src_language,
        dst_language=dst_language,
        google_translate_api_key=google_translate_api_key,
    )

    return subtitles


if __name__ == '__main__':
    sys.exit(main())
