[![Build Status](https://github.com/unitedstates/congressional-record/actions/workflows/ci.yml/badge.svg)](https://github.com/unitedstates/congressional-record/actions/workflows/ci.yml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![code style: prettier](https://img.shields.io/badge/code_style-prettier-ff69b4.svg)](https://github.com/prettier/prettier)

# congressional-record

This tool converts HTML files containing the text of the Congressional Record into structured text data. It identifies and parses various types of congressional content including speeches, procedural text, and official statements.

From the repository root, type `python -m congressionalrecord.cli -h` for instructions.

## Content Types

The parser identifies and categorizes the following types of content:

- **Speech** - Floor speeches and statements by members of Congress, tagged with the speaker's bioguideid wherever possible. Speeches are recorded as "turns," such that each subsequent instance of speech by a Member counts as a new "turn."
- **Prayer** - Opening prayers delivered by chaplains or guest clergy at the beginning of legislative sessions
- **Constitutional Authority** - Constitutional Authority Statements filed by members when introducing bills, including the bill number and constitutional article/section/clause cited
- **Committee Election** - Announcements of members being elected to congressional committees
- **Committee Resignation** - Letters and announcements of members resigning from committees
- **Recorder** - Comments and readings by the legislative clerk or recorder
- **Clerk** - Statements and readings by the House or Senate Clerk
- **Rollcall** - Rollcall vote records and results
- **Title** - Section headings and titles within the Congressional Record
- **Linebreak** - Formatting breaks and section dividers

## Document Types

In addition to content types, the parser identifies special document types for reports that differ from regular proceedings:

- **Foreign Travel Expenditure** - Reports of congressional foreign travel expenditures (identified by `document_type: "foreign_travel_expenditure"`)

Regular congressional proceedings have `document_type: null`.

All content is output as JSON with standardized fields including speaker identification, text content, and metadata.

This software is released as-is under the BSD3 License, with no warranty of any kind.

# installation

Clone and download the repository:

```bash
git clone https://github.com/unitedstates/congressional-record.git
cd congressional-record
```

In Python 3 using `venv` for e.g.:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

then `.venv/bin/python -m congressionalrecord.cli -h` to see usage instructions.


If using Python 3 with uv, use:

```bash
uv sync
```

then `uv run python -m congressionalrecord.cli -h` to see usage instructions.


# Recommended citation:

Judd, Nicholas, Dan Drinkard, Jeremy Carbaugh, and Lindsay Young. _congressional-record: A parser for the Congressional Record._ Chicago, IL: 2017.
