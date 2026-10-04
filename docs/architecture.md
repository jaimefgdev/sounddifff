# Architecture

## Module layout

```text
src/sounddifff/
  types.py       Frozen dataclasses for all analysis results
  formats.py     Audio I/O and format detection (soundfile)
  loudness.py    LUFS, true peak, loudness range (pyloudnorm)
  spectral.py    Frequency band energy comparison (numpy FFT)
  temporal.py    Cross-correlation and segment detection
  detection.py   Clipping and silence detection
  core.py        Pipeline orchestration
  cli.py         Click CLI entry point
  report.py      Output formatters (terminal, JSON, HTML)
```

## Data flow

```text
CLI (click)
  -> core.diff(path_a, path_b)
    -> formats.load_audio(path_a)  ->  ndarray + AudioMetadata
    -> formats.load_audio(path_b)  ->  ndarray + AudioMetadata
    -> loudness.compare_loudness(data_a, data_b, ...)  ->  LoudnessComparison
    -> spectral.compare_spectral(data_a, data_b, ...)  ->  SpectralComparison
    -> temporal.compare_temporal(data_a, data_b, ...)   ->  TemporalComparison
    -> detection.compare_detection(data_a, data_b, ...) ->  DetectionResult
    -> DiffResult (all results combined)
  -> report.render(result, format)
  -> stdout or file
```

## Design decisions

### Frozen dataclasses for all results

Every result type is a frozen (immutable) dataclass. Once a `DiffResult` is created, it can't be modified. Computed values like `lufs_delta` are properties that derive from the stored measurements. This keeps the data model predictable and easy to test.

### Independent analysis modules

The four analysis modules (loudness, spectral, temporal, detection) don't import from each other. Each one takes raw audio data and returns a typed result. The `core` module orchestrates them in sequence. This means you can add a new analysis module without touching the existing ones, and you can run any analysis in isolation.

### Channel handling at the analysis layer

`formats.load_audio()` always returns multi-channel data as a 2D array (frames x channels). Each analysis module decides how to handle channels:

- Loudness: passes multi-channel data directly to pyloudnorm
- Spectral: mixes to mono for FFT analysis
- Temporal: mixes to mono for cross-correlation
- Detection (clipping): analyzes each channel independently
- Detection (silence): mixes to mono for RMS calculation

### No global state

Every function takes its inputs as arguments and returns its outputs. No module-level caches, no singletons, no configuration objects that need to be initialized. This makes the code straightforward to test and reason about.

### Error handling at the boundary

File validation and error handling happen in `formats.py` (file loading) and `cli.py` (user-facing errors). The analysis modules assume they receive valid numpy arrays and focus on computation.

## Testing approach

Tests live in `tests/` with one file per module. Test audio is generated deterministically by `scripts/generate_test_audio.py` using fixed parameters (specific frequencies, amplitudes, and durations). This means tests are reproducible across machines without committing audio files to the repo.

The test suite uses:

- **pytest**: standard test runner and fixtures
- **hypothesis**: property-based testing for DSP edge cases (e.g., "correlation of a signal with itself is always 1.0")
- **click.testing.CliRunner**: CLI integration tests without spawning subprocesses

Key fixtures in `conftest.py` provide pre-loaded audio pairs (identical, loud/quiet, clipped/clean, with/without silence, different lengths, mono) so tests can focus on assertions rather than setup.

## Adding a new analysis module

1. Create `src/sounddifff/your_module.py` with a `compare_*` function that takes audio data and returns a result dataclass
2. Add the result dataclass to `types.py`
3. Call your `compare_*` function from `core.py` and include the result in `DiffResult`
4. Add rendering logic to `report.py` for terminal, JSON, and HTML output
5. Write tests in `tests/test_your_module.py`
6. Add test fixtures to `conftest.py` if needed
