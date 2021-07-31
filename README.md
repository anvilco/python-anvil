# Anvil API Library

[![PyPI Version](https://img.shields.io/pypi/v/python-anvil.svg)](https://pypi.org/project/python-anvil)
[![PyPI License](https://img.shields.io/pypi/l/python-anvil.svg)](https://pypi.org/project/python-anvil)

This is a library that provides an interface to access the [Anvil API](https://www.useanvil.com/developers) from applications
written in the Python programming language.

Anvil is a suite of tools for integrating document-based workflows and PDFs within your application:

1. Anvil Workflows converts your PDF forms into simple, intuitive websites that 
   fill the PDFs and gather signatures for you.
2. Anvil PDF Filling API allows you to fill any PDF with JSON data.
3. Anvil PDF Generation API allows you to create new PDFs.
4. Anvil Etch E-sign API allows you to request signatures on a PDF signing packet.

Currently, this API library only supports our PDF filling API and our GraphQL API.

### Documentation

General API documentation: [Anvil API docs](https://www.useanvil.com/docs)

# Setup

## Requirements

* Python 3.6+

## Installation

Install it directly into an activated virtual environment:

```text
$ pip install python-anvil
```

or add it to your [Poetry](https://python-poetry.org/) project:

```text
$ poetry add python-anvil
```

