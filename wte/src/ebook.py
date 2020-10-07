import json
import datetime
import imghdr
import os

from ebooklib import epub

from .util import Log, do_hash, downoad_image, format_filename


class Chapter:
    def __init__(self, title='', content=''):
        self.title = title
        self.content = content

    @classmethod
    def from_json(cls, data):
        chap = cls()
        chap.title = data['title']
        chap.content = data['content']
        return chap

    def to_json(self):
        return {
            'title': self.title,
            'content': self.content,
        }

    def get_filename(self):
        return 'index_' + do_hash(self.title) + '.xhtml'

    def get_real_content(self):
        return (f'<h2>{self.title}</h2>'
                + self.content)

    def to_epub(self):
        chap = epub.EpubHtml(
            title=self.title,
            file_name=self.get_filename(),
        )
        chap.set_content(self.get_real_content())

        return chap


class FrontPageChapter(Chapter):
    def __init__(self, title='', content='', tags=[], author=None, source=None):
        self.title = title
        parts = []

        if tags:
            parts.append(('Tags', ', '.join(tags)))
        if author:
            parts.append(('Author', author))
        if source:
            parts.append(('From', source))
        parts = [f'<li><strong>{a}:<strong> {b}\n' for a, b in parts]

        content = content.replace("\n", "<br/>")
        self.content = f"""
            <h1>{title}</h1>
            <p style='font-style:italic;'>
                {content}
            </p>
            <ul>{''.join(parts)}</ul>
        """

    def get_filename(self):
        return 'index_frontpage.xhtml'

    def get_real_content(self):
        return self.content


class Book:
    def __init__(self, title='', identifier=None, cover=None, author=None,
                 source=None, lang='en', description=None, date=None, tags=[]):
        self.title = title
        self.chapters = []
        self.cover = cover
        self.author = author
        self.source = source
        self.identifier = identifier
        self.lang = lang
        self.description = description
        self.date = date
        self.tags = tags

        if not self.date:
            now = datetime.date.today()
            self.date = now.strftime("%Y-%m-%d")

    @classmethod
    def from_json(cls, data):
        book = cls()
        book.title = data['title']
        book.cover = data['cover']
        book.author = data['author']
        book.source = data['source']
        book.chapters = [Chapter.from_json(c) for c in data['chapters']]
        return book

    def add_chapter(self, *kargs, **kwargs):
        self.chapters.append(Chapter(*kargs, **kwargs))

    def cover_from_url(self, url):
        self.cover = None
        if url is not None:
            self.cover = downoad_image(url)

    def to_json(self):
        return {
            'title': self.title,
            'cover': self.cover,
            'author': self.author,
            'source': self.source,
            'chapters': [c.to_json() for c in self.chapters]
        }

    def epub_name(self):
        title = self.title.replace("'", " ").lower()
        parts = title.split()
        if self.source:
            parts.append(self.source)
        if self.identifier:
            parts.append(self.identifier)
        return format_filename('-'.join(parts)) + '.epub'

    def get_front_page(self):
        if self.description is None:
            return None
        return FrontPageChapter(
            title=self.title,
            content=self.description,
            tags=self.tags,
            author=self.author,
            source=self.source
        )

    def to_epub(self, dest_path=None):
        ef = epub.EpubBook()
        identifier = self.identifier or do_hash(self.title)
        if self.source is not None:
            identifier = str(self.source) + '-' + identifier

        # Main data
        ef.set_identifier(identifier)
        ef.set_title(self.title)
        ef.set_language(self.lang)
        if self.author is not None:
            authors = self.author if isinstance(
                self.author, list) else[self.author]
            for auth in authors:
                ef.add_author(auth)

        # Metadata
        if self.description:
            ef.add_metadata('DC', 'description', self.description)
        if self.source:
            ef.add_metadata('DC', 'publisher', self.source)

        # Cover
        if self.cover:
            image_path = self.cover if isinstance(
                self.cover, str) else self.cover.name
            image_name = 'cover.' + imghdr.what(image_path)
            im = open(image_path, 'rb').read()
            ef.set_cover(image_name, im, True)

        # Create chapters
        book_parts = []
        chapters = self.chapters

        front_page = self.get_front_page()
        if front_page:
            chapters = [front_page] + chapters

        for chap in chapters:
            epub_chap = chap.to_epub()
            ef.add_item(epub_chap)
            book_parts.append(epub_chap)

        ef.toc = tuple(book_parts)
        ef.spine = ['nav'] + book_parts

        ef.add_item(epub.EpubNcx())
        ef.add_item(epub.EpubNav())

        if dest_path is not None:
            dest_path = str(dest_path)
            if os.path.exists(dest_path):
                if not Log.confirm(f"The file {dest_path} already exists. Overwride ?"):
                    Log.warning(
                        f"The epub file was not written because {dest_path} already exists")
                    dest_path = None
            if dest_path:
                epub.write_epub(dest_path, ef)
                Log.success(
                    f"The file {dest_path} has been successfully written")

        return ef


if __name__ == "__main__":
    data = json.load(open('book.json', 'r'))
    book = Book.from_json(data)
    book.cover_from_url("https://a.wattpad.com/cover/96907097-512-k463519.jpg")
    book.tags = ['tag1', 'tag2', 'tag3', 'tag4', 'tag5']
    book.description = """There are many gods bound to Shalara's care. Some are good; others bad. But none are as feared or reviled as Katastarof, Lord of Calamity and Destruction.
    
    Eons ago, the Pantheon locked the destruction deity away, binding his tomb with several Keys. These Keys were then scattered across the world, to hopefully never see the light of day again."""

    ef = book.to_epub('test.epub')

    print(book.epub_name())
