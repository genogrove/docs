# Genogrove Documentation

[![Read the Docs — Genogrove documentation](https://img.shields.io/readthedocs/genogrove)](https://genogrove.readthedocs.io/)
[![Genogrove version](https://img.shields.io/badge/genogrove-v0.14.0-green.svg)](https://github.com/genogrove/genogrove)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Sphinx](https://img.shields.io/badge/built%20with-Sphinx-blue.svg)](https://www.sphinx-doc.org/)
[![MyST](https://img.shields.io/badge/markup-MyST%20Markdown-purple.svg)](https://myst-parser.readthedocs.io/)

This repository contains the source files for the [genogrove documentation](https://genogrove.readthedocs.io/), built with [Sphinx](https://www.sphinx-doc.org/) and [MyST Parser](https://myst-parser.readthedocs.io/).

## Building Locally

Install the dependencies and build the HTML documentation:

```bash
pip install -r source/requirements.txt
make html
```

The output will be in `build/html/`.

## Structure

- `source/` — documentation source files (Markdown via MyST)
- `source/conf.py` — Sphinx configuration
- `source/guide/` — user guide pages
- `source/reference/` — API reference pages
- `repos/` — git submodules for API doc generation (Breathe/Doxygen)