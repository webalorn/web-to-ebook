import json

from pyquery import PyQuery as pq
from lxml import etree
import requests

from .ebook import Book
from .util import RequestError, Log, fetch_html, post_process_html


WATTPAD_BASE = "https://www.wattpad.com"

WATTPAD_HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
}


def post_process_local(content, book):
    content = post_process_html(content, book)
    content.find('figcaption').remove()
    content.find('figure span').remove()
    return content


def download_book(book_url):
    Log.log(f'Downloading {book_url} ...')
    d = fetch_html(book_url, headers=WATTPAD_HEADERS)

    story_id = d("button[data-story-id]").attr("data-story-id")
    if "/story/" + story_id not in book_url:
        Log.warning("The url was not the main page of the story")
        return download_book("https://www.wattpad.com/story/" + story_id)
    status_div = d("#story-landing div.author-info > small")
    status_div.find('span').remove()

    book = Book(
        title=d('#story-landing header h1').text().strip(),
        author=d('#story-landing .author-info a.send-author-event').text().strip(),
        source='wattpad',
        identifier=story_id,
        description=d('.panel h2.description > pre').html().strip(),
        status=status_div.text().strip()
    )

    Log.log(
        f'============ Downloading "{book.title}" from Wattpad ============')

    mini_cover_url = d('#story-landing .cover.cover-lg > img').attr('src')
    # cover_url = f"https://a.wattpad.com/cover/{story_id}-512-k282189.jpg"
    parts = mini_cover_url.split('-')
    cover_url = f"{parts[0]}-512-{parts[2]}"
    book.cover_from_url(cover_url)

    table = d(".story-parts .table-of-contents")
    links = list(table.find("a.on-navigate-part"))

    for i, el in enumerate(links):
        chapter_name = el.text.strip()
        chapter_url = WATTPAD_BASE + el.get('href')
        Log.log(f'==> Chapter {i+1}/{len(links)}')
        book.add_chapter(
            title=chapter_name,
            content=extract_chapter_content(chapter_url, book)
        )

    book.tags = [a.text.strip() for a in d('ul.tag-items li a')]

    return book


def extract_chapter_content(chapter_url, book, page=1):
    Log.log(f'Page {page}...')
    d = fetch_html(chapter_url + f"/page/{page}", headers=WATTPAD_HEADERS)

    content = d("#app-container main .panel-reading pre")
    content = post_process_local(content, book)
    text_content = content.html()

    load_more = list(d("a.on-load-more-page").items())
    if load_more:
        text_content += extract_chapter_content(chapter_url, book, page + 1)
    return text_content
