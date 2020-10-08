import shutil
import requests
import tempfile
import string
import imghdr
import random

from pyquery import PyQuery as pq
from ebooklib import epub


class RequestError(Exception):
    def __init__(self, message, req):
        super().__init__(
            f'{message} [Status: {req.status_code} because {req.reason}, url: {req.url}]')
        self.message = message
        self.req = req

# ========== Images wraper =========


class ImageData:
    def __init__(self, path, uid=None):
        self.path = path
        if uid is not None:
            self.uid = str(uid)
        else:
            self.uid = str(random.randint(1, 10 ** 9))

    def extension(self):
        return imghdr.what(self.hd_location())

    def epub_location(self):
        return f'images/{self.uid}.{self.extension()}'

    def hd_location(self):
        return self.path

    def read(self):
        with open(self.hd_location(), 'rb') as f:
            return f.read()

    def to_epub(self):
        return epub.EpubItem(
            uid=self.uid,
            file_name=self.epub_location(),
            content=self.read(),
        )


class TmpImageData(ImageData):
    def __init__(self, file, uid=None):
        self.file = file
        super().__init__(file.name, uid)

# ========== Utility functions =========


def do_hash(element):
    return str(abs(hash(element)))


def downoad_image(url):
    r = requests.get(url, stream=True)

    f = tempfile.NamedTemporaryFile()
    if r.status_code == 200:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)
    else:
        raise RequestError("Failed to dowload the image", r)
    return f


def fetch_html(url, **kwargs):
    r = requests.get(url, **kwargs)
    assert r.status_code == 200, RequestError(f'Error when fetching a page', r)
    return pq(r.text)


def format_filename(s):
    valid_chars = f"-_{string.ascii_letters}{string.digits}"
    filename = ''.join(c for c in s if c > 'z' or c in valid_chars)
    return filename


def post_process_html(content, book):
    imgs = content.find('img')
    for img in imgs:
        url = img.get('src')
        imgdata = TmpImageData(downoad_image(url), len(book.images))
        book.images.append(imgdata)
        img.set('src', imgdata.epub_location())
    return content

# ========== LOGGER ==========


class Log:
    silent = False
    colors = {
        'default': '\033[39m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
    }

    @classmethod
    def set_mode(cls, silent):
        cls.silent = silent

    @classmethod
    def log(cls, *messages, color=None):
        if not cls.silent:
            msg = ' '.join([str(m) for m in messages])
            if color is not None:
                msg = cls.colors[color] + msg + cls.colors['default']
            print(msg)

    @classmethod
    def error(cls, *messages):
        cls.log("[ERROR]", *messages, color='red')

    @classmethod
    def warning(cls, *messages):
        cls.log("[WARNING]", *messages, color='magenta')

    @classmethod
    def success(cls, *messages):
        cls.log(*messages, color='green')

    @classmethod
    def input(cls, message, default=None):
        if cls.silent:
            return default
        return input(message)

    @classmethod
    def confirm(cls, message, default=False):
        if cls.silent:
            return default
        message += ' [y/n] '
        while True:
            ans = cls.input(message).strip().lower()
            if ans in ['y', 'yes', '1', 'true']:
                return True
            if ans in ['n', 'no', '0', 'false']:
                return False
