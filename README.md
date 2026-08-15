# VulturEklips

VulturEklips is a desktop app for importing eclipse photos, detecting the solar disc, aligning frames, and exporting a composite image.

## Setup

```bash
cd /Users/alanhart/Documents/Dev/VulturEklips
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest
```

## Run the app

```bash
cd /Users/alanhart/Documents/Dev/VulturEklips
. .venv/bin/activate
python main.py
```

## Run tests

Run the full suite:

```bash
cd /Users/alanhart/Documents/Dev/VulturEklips
.venv/bin/python -m pytest
```

Run only the orchestration test file:

```bash
cd /Users/alanhart/Documents/Dev/VulturEklips
.venv/bin/python -m pytest tests/test_orchestrated_ui_actions.py -q
```

Or use the convenience target in the project Makefile:

```bash
cd /Users/alanhart/Documents/Dev/VulturEklips
make test
make test-ui
```

The Qt tests run in offscreen mode automatically, so they can be executed in headless environments and CI.
