# Contributing to sounddiff

Contributions are welcome. This guide covers everything you need to get set up and submit a pull request.

## Development setup

1. Fork and clone the repo
2. Create a virtual environment: `python -m venv .venv && source .venv/bin/activate`
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Install pre-commit hooks: `pre-commit install`
5. Generate test audio fixtures: `python scripts/generate_test_audio.py`
6. Run the test suite: `pytest`

If all tests pass, your environment is ready.

## Finding work

The [issue board](https://github.com/jaimefgdev/sounddiff/issues) is organized by milestone. Issues labeled [`good first issue`](https://github.com/jaimefgdev/sounddiff/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) are scoped for newcomers and include enough context to get started without deep DSP knowledge.

If you want to work on something, leave a comment on the issue so nobody duplicates effort. If you have an idea that isn't on the board, open an issue first so we can align on scope before you write code.

## Development workflow

1. Create a branch from `main`: `git checkout -b feat/42-your-description`
2. Make your changes and write tests for new behavior
3. Run the full check: `ruff check . && ruff format --check . && mypy src && pytest`
4. Commit using [conventional commits](https://www.conventionalcommits.org/): `feat: add stereo field analysis`
5. Push your branch and open a PR against `main`

## Pull request guidelines

- **One concern per PR.** Keep diffs focused and reviewable.
- **Reference the issue** in your PR body: `Closes #42`
- **CI must pass** before review. The pipeline runs ruff, mypy, and pytest across Python 3.10-3.13 on Linux and macOS.
- **[CodeRabbit](https://coderabbit.ai) reviews every PR automatically.** Address its feedback or explain your reasoning if you disagree.
- Maintainers will review within a few days. If a week goes by without a response, ping us in the PR.

## Code standards

**Formatting and linting** are handled by [ruff](https://docs.astral.sh/ruff/). Pre-commit hooks run automatically, so you don't need to think about formatting manually.

**Type annotations** are required on all public functions. [mypy](https://mypy.readthedocs.io/) runs in strict mode.

**Docstrings** follow [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) on public functions. Private functions (underscore-prefixed) don't require them.

**No `# type: ignore`** without a comment explaining why.

## Testing

Every new feature needs tests. Every bug fix needs a regression test.

We use [pytest](https://docs.pytest.org/) for the test suite and [hypothesis](https://hypothesis.readthedocs.io/) for property-based testing on DSP functions. Test audio is generated deterministically by `scripts/generate_test_audio.py` and is not committed to the repo. This keeps the repo lightweight and tests reproducible.

If you're unsure how to test something, ask in the issue. We'd rather help you write a good test than skip testing.

## Conventions

### Branch naming

Include the issue number when there is one:

- `feat/42-segment-detection`
- `fix/17-clipping-threshold`
- `docs/8-usage-guide`
- `chore/12-ci-update`

### Commit messages

```text
feat: add spectral band comparison
fix: handle mono files in loudness calculation
docs: add installation guide
test: add property tests for temporal alignment
chore: update CI to Python 3.13
refactor: extract segment detection into its own module
```

## Questions

Open an [issue](https://github.com/jaimefgdev/sounddiff/issues). We're happy to help with anything from setup problems to architecture questions.
