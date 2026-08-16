PYTHON = .venv/bin/python
PYTEST = $(PYTHON) -m pytest
LICENSES_VENV = .venv-licenses

.PHONY: test test-ui install-test licenses-report

install-test:
	$(PYTHON) -m pip install pytest

test:
	$(PYTEST)

test-ui:
	$(PYTEST) tests/ui tests/integration -q

# Builds an isolated venv with only the runtime dependencies (requirements.txt)
# so the report reflects exactly what ships in the app, not dev/build tooling.
# Output lives under assets/ so it's bundled by PyInstaller and loaded by the
# Licenses dialog at runtime.
licenses-report:
	$(PYTHON) -m venv $(LICENSES_VENV)
	$(LICENSES_VENV)/bin/python -m pip install -U pip
	$(LICENSES_VENV)/bin/python -m pip install -r requirements.txt pip-licenses
	$(LICENSES_VENV)/bin/python -m piplicenses \
		--from=mixed --with-authors --with-urls --with-license-file --no-license-path \
		--format=json --output-file=assets/licenses-report.json
	rm -rf $(LICENSES_VENV)
