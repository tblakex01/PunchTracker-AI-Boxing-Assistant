# Repository Guidelines

These instructions apply to the entire repository. Follow them when modifying or adding files.

## Environment Setup
- Use **Python 3.11+**.
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  pip install black flake8  # development tools
  ```
- Verify that all imported modules are listed in `requirements.txt`:
  ```bash
  python utils/verify_requirements.py
  ```

## Formatting
- Format code with **Black** before committing:
  ```bash
  black .
  ```
- Use the default line length (88 characters) and 4‑space indentation.

## Linting
- Run **flake8** and resolve all issues:
  ```bash
  flake8 --max-line-length=120
  ```

## Testing
- Execute the test suite with **pytest** and ensure it passes:
  ```bash
  pytest -v
  ```

## Pull Requests
- Make concise, focused commits using present‑tense messages (e.g., "Add combo detection module").
- Verify formatting, linting, and tests succeed before submitting a PR.
