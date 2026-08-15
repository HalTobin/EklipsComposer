PYTHON = .venv/bin/python
PYTEST = $(PYTHON) -m pytest

.PHONY: test test-ui install-test

install-test:
	$(PYTHON) -m pip install pytest

test:
	$(PYTEST)

test-ui:
	$(PYTEST) tests/ui tests/integration -q
