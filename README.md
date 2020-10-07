# Web to ebook

WTE (web-to-ebook) helps you to convert content from some websites into an ebook (epub format) that you can read offline or on an ebook reader.

## Install

### Manually

Clone the repository and intall or upgrade the dependencies :

```bash
git clone https://github.com/webalorn/web-to-ebook
python3 -m pip install --upgrade requests lxml pyquery ebooklib
```

## Usage

```bash
wte [url_of_the_page] # Simple usage
wte [url_of_the_page] --quiet -o [output.epub] # More options
wte -h # Show the help and all the options
```

### Currently supported

- [Wattpad](https://www.wattpad.com/) : Converts a whole book
