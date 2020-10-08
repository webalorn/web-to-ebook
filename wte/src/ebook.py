import json
import datetime
import imghdr
import os

from ebooklib import epub

from .util import Log, do_hash, downoad_image, format_filename
from .util import ImageData, TmpImageData


class Chapter:
    def __init__(self, title='', content=''):
        self.title = title
        self.content = content
        self.filename = None

    def get_filename(self):
        name = str(self.filename or do_hash(self.title))
        return 'index_' + name + '.xhtml'

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
    def __init__(self, title='', content='', tags=[], author=None, source=None,
                 date=True, status=None):
        self.title = title
        parts = []

        if tags:
            parts.append(('Tags', ', '.join(tags)))
        if author:
            parts.append(('Author', author))
        if source:
            parts.append(('From', source))
        if status:
            parts.append(('Status', status))
        if date:
            if date is True:
                now = datetime.date.today()
                date = now.strftime("%d/%m/%Y")
            parts.append(('Date', date))
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
    def __init__(self, title='', identifier=None, cover=None, author=None, status=None,
                 source=None, lang='en', description=None, date=None, tags=[]):
        self.title = title
        self.chapters = []
        self._cover = None
        self.set_cover(cover)
        self.author = author
        self.source = source
        self.identifier = identifier
        self.lang = lang
        self.description = description
        self.date = date
        self.tags = tags
        self.images = []
        self.status = status

        if not self.date:
            now = datetime.date.today()
            self.date = now.strftime("%Y-%m-%d")

    def add_chapter(self, *kargs, **kwargs):
        self.chapters.append(Chapter(*kargs, **kwargs))

    def cover_from_url(self, url):
        self._cover = None
        if url is not None:
            self._cover = TmpImageData(downoad_image(url), 'cover')

    def set_cover(self, path):
        self._cover = None
        if path is not None:
            self._cover = ImageData(path, 'cover')

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
            source=self.source,
            status=self.status,
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

        # Cover and image
        if self._cover:
            im = self._cover.read()
            ef.set_cover(self._cover.epub_location(), im, True)

        for img in self.images:
            ef.add_item(img.to_epub())

        # Create chapters
        book_parts = []
        chapters = self.chapters
        for i_chap, chap in enumerate(self.chapters):
            chap.filename = f'chapter_{i_chap+1}'

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

        # Write the ebook

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
