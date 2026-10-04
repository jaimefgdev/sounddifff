# sounddifff

Structured audio comparison CLI. Python 3.10+, src layout, hatchling build.

## Build & Test

```sh
pip install -e ".[dev]"
python scripts/generate_test_audio.py
pytest
ruff check . && ruff format --check . && mypy src
```

## Architecture

```
src/sounddifff/
  types.py       # Dataclasses for all results
  formats.py     # Audio I/O via soundfile
  loudness.py    # LUFS, true peak, LRA (pyloudnorm)
  spectral.py    # Band energy comparison (numpy FFT)
  temporal.py    # Cross-correlation, segment detection
  detection.py   # Clipping, silence detection
  core.py        # Pipeline orchestration
  cli.py         # Click CLI entry point
  report.py      # Output formatters (terminal/JSON/HTML)
```

## Conventions

- **Ruff** for linting and formatting. No black, isort, or flake8.
- **mypy strict mode.** Type hints everywhere.
- **Google-style docstrings** on all public functions.
- **Conventional commits.** `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`.
- **One concern per PR.** Small, focused diffs. Squash merge.
- **pytest + hypothesis** for testing. Property-based tests for DSP functions.
- **Test audio is generated, not committed.** Run `scripts/generate_test_audio.py`.
- **No `# type: ignore` without a comment.**

## Key dependencies

| Package | Purpose |
|---------|---------|
| soundfile | Audio I/O (wav, flac, ogg, aiff) |
| numpy | Array math, FFT, correlation |
| scipy | Signal processing, filtering |
| pyloudnorm | ITU-R BS.1770 LUFS measurement |
| click | CLI framework |
| rich | Terminal formatting |
| jinja2 | HTML report templates |
