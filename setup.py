import setuptools
import os
from pathlib import Path
import importlib.util

cur_dir = Path(__file__).parent

try:
    with open("readme.md", "r") as readme_file:
        readme_content = readme_file.read()
except:
    readme_content = '[error] readme.md unavailable'


def import_module_file(name, path):
    path = str(cur_dir / path)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


main_module = import_module_file("wte", "wte/__init__.py")

setuptools.setup(
    name='wte',
    version=main_module.__version__,
    author="webalorn",
    author_email="webalorn@gmail.com",
    description="Convert content from the web to ebooks",
    long_description=readme_content,
    long_description_content_type="text/markdown",
    url="https://github.com/webalorn/web-to-ebook",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
                'wte=wte.main:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    project_urls={
        "Documentation": "https://github.com/webalorn/web-to-ebook/blob/main/README.md",
        "Source": "https://github.com/webalorn/web-to-ebook",
    },
    include_package_data=True,
    install_requires=['requests>=2.24', 'lxml>=4.5',
                      'pyquery>=1.4', 'ebooklib>=0.17'],
    python_requires='>=3',
)
