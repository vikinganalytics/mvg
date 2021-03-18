# MVG Documentation

Documentation is written with [sphinx](https://www.sphinx-doc.org/en/master/) that uses a markuplanguage called [reStructuredText (.rst)](https://docutils.sourceforge.io/rst.html) that is similar to markdown.

The content of the documentation can be found in `docs/source/` and `index.rst` is the landing page that links to all the other pages in `docs/source/content`

## Building the Documentation

The documentation is built by navigating to the `docs/` directory and running `make clean`, `make html`.

## Installation

We use a sphinx extension called nbsphinx, that requires the external program **pandoc** to convert the markdown to rst:

### pandoc

Installation steps for any OS:

[https://pandoc.org/installing.html](https://pandoc.org/installing.html)

Linux:

```bash
wget https://github.com/jgm/pandoc/releases/download/2.11.4/pandoc-2.11.4-1-amd64.deb
sudo dpkg -i pandoc-2.11.4-1-amd64.deb
rm pandoc-2.11.4-1-amd64.deb
pandoc --version
```
