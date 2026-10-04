# Contributing

This is a summary. See [CONTRIBUTING.md](../CONTRIBUTING.md) in the project root for the full guide.

## Setup

```sh
git clone https://github.com/jaimefgdev/sounddifff.git
cd sounddifff
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
python scripts/generate_test_audio.py
pytest
```

## Workflow

1. Pick an issue from the [issue board](https://github.com/jaimefgdev/sounddifff/issues) and comment on it
2. Create a branch: `git checkout -b feat/42-description`
3. Write code and tests
4. Run checks: `ruff check . && ruff format --check . && mypy src && pytest`
5. Commit with [conventional commits](https://www.conventionalcommits.org/): `feat: add spectral band comparison`
6. Open a PR against `main` referencing the issue: `Closes #42`

## Standards

- **Formatting**: ruff (runs automatically via pre-commit)
- **Type checking**: mypy in strict mode, type hints on all public functions
- **Docstrings**: Google style on public functions
- **Testing**: pytest + hypothesis, every feature and bug fix needs a test
- **PRs**: one concern per PR, CI must pass, [CodeRabbit](https://coderabbit.ai) reviews automatically

Issues labeled [`good first issue`](https://github.com/jaimefgdev/sounddifff/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) are scoped for newcomers.
