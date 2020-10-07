import argparse
import re

from src.util import Log

# ========== create_book ==========

import src

URL_MATCHS = {
    "^(https?://)?(www\\.)?wattpad\\.com/.+$": src.wattpad,
}


def get_module_of_book(url):
    url = url.strip()
    for pattern, module in URL_MATCHS.items():
        if re.match(pattern, url):
            return module
    return None


def try_create_book(url):
    module = get_module_of_book(url)
    if module is None:
        Log.error(
            f"The content at {url} doesn't match any pattern and is not recognized")
        exit(0)
    return module.download_book(url)

# ========== Main ==========


SHORT_DESCRIPTIOM = """Easily convert websites into book"""


def get_cmd_args():
    parser = argparse.ArgumentParser(description=SHORT_DESCRIPTIOM)

    parser.add_argument('-o', '--output', type=str,
                        help='Output file', default=None)
    parser.add_argument('-q', '--quiet', help='Quiet mode',
                        action='store_true', default=False)

    parser.add_argument(
        'url', type=str, help='Url of the page you want to convert to an ebook')

    return parser.parse_args()


def main():
    args = get_cmd_args()
    if args.quiet:
        Log.silent = True

    book = try_create_book(args.url)

    output_file = args.output or book.epub_name()
    if not output_file.endswith('.epub'):
        output_file += '.epub'

    book.to_epub(output_file)


if __name__ == "__main__":
    main()
