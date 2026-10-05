# Targets that regenerate what the repository can regenerate.

PY := .venv/bin/python

.PHONY: playbook playbook-test

## The decision playbook: docs/playbook/, gitignored. Rebuild after any
## ruling, verdict or CLI change (docs/manual/playbook.md).
playbook:
	$(PY) tools/build_playbook.py

playbook-test:
	$(PY) -m pytest tests/test_playbook.py -q
