# Targets that regenerate what the repository can regenerate.

PY := .venv/bin/python

.PHONY: test reference schema book

## The whole suite.
test:
	$(PY) -m pytest -q

## docs/REFERENCE.md, generated from the argument parsers and deploy/.
## Same commit as any change to a parser, a timer or a tool (CLAUDE.md).
reference:
	$(PY) tools/build_manual_reference.py > docs/REFERENCE.md
	$(PY) -m pytest tests/test_manual_reference.py -q

## config/review/SCHEMA.md, generated from vss/review.py.
schema:
	$(PY) -m vss review --schema > config/review/SCHEMA.md
	$(PY) -m pytest tests/test_review.py -q

## The book, both languages (docs/the-method/).
book:
	cd docs/the-method/_build && python3 build.py
