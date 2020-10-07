import shutil
import requests
import tempfile
import string

from pyquery import PyQuery as pq


class RequestError(Exception):
    def __init__(self, message, req):
        super().__init__(
            f'{message} [Status: {req.status_code} because {req.reason}, url: {req.url}]')
        self.message = message
        self.req = req


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
        message += ' [y/n]'
        while True:
            ans = cls.input(message).strip().lower()
            if ans in ['y', 'yes', '1', 'true']:
                return True
            if ans in ['n', 'no', '0', 'false']:
                return False
