.PHONY: install dev lint test check package

install:
	python3 -m venv --system-site-packages .venv
	.venv/bin/pip install --upgrade pip setuptools wheel
	.venv/bin/pip install -e . -r requirements.txt

dev:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e . -r requirements-dev.txt

lint:
	.venv/bin/ruff check src tests

test:
	.venv/bin/pytest -q

check: lint test
	.venv/bin/python -m compileall -q src

package:
	git archive --format=zip --output=J07-VIREO-source.zip HEAD
