# API Reference

sounddifff can be used as a Python library in addition to the CLI. Import the `diff` function, pass two file paths, and get back a typed result object.

## Quick example

```python
from sounddifff.core import diff

result = diff("old-mix.wav", "new-mix.wav")

print(f"LUFS delta: {result.loudness.lufs_delta:+.1f} dB")
print(f"Correlation: {result.temporal.overall_correlation:.3f}")
print(f"Clipping events: {len(result.detection.clips)}")

for band in result.spectral.bands:
    print(f"  {band.name}: {band.delta_db:+.1f} dB")
```

## Core

### `sounddifff.core.diff(path_a, path_b) -> DiffResult`

Compare two audio files and return a structured result.

- `path_a`: path to the reference file (str or Path)
- `path_b`: path to the comparison file (str or Path)
- Raises `FileNotFoundError` if either file doesn't exist
- Raises `ValueError` if the format is unsupported or requires ffmpeg

## Types

All result types are frozen dataclasses defined in `sounddifff.types`. They are immutable after creation. Computed values (deltas, durations) are exposed as properties.

### `DiffResult`

Top-level container for all analysis results.

| Field | Type | Description |
| --- | --- | --- |
| `metadata` | `MetadataComparison` | File metadata (duration, sample rate, channels) |
| `loudness` | `LoudnessComparison` | LUFS, true peak, loudness range |
| `spectral` | `SpectralComparison` | Per-band frequency energy |
| `temporal` | `TemporalComparison` | Segment correlation and classification |
| `detection` | `DetectionResult` | Clipping and silence events |
| `warnings` | `list[str]` | Warnings (e.g., sample rate mismatch) |

### `AudioMetadata`

Metadata for a single audio file.

| Field | Type | Description |
| --- | --- | --- |
| `path` | `str` | File path |
| `duration` | `float` | Duration in seconds |
| `sample_rate` | `int` | Sample rate in Hz |
| `channels` | `int` | Number of channels |
| `bit_depth` | `int \| None` | Bit depth (None if unknown) |
| `format_name` | `str` | Format identifier (e.g., "WAV") |
| `frames` | `int` | Total number of sample frames |

### `MetadataComparison`

Comparison of metadata between two files.

| Field | Type | Description |
| --- | --- | --- |
| `file_a` | `AudioMetadata` | Reference file metadata |
| `file_b` | `AudioMetadata` | Comparison file metadata |

Properties: `duration_delta`, `same_duration`, `same_sample_rate`, `same_channels`

### `LoudnessResult`

Loudness measurements for a single file.

| Field | Type | Description |
| --- | --- | --- |
| `lufs` | `float` | Integrated loudness in LUFS |
| `true_peak_dbtp` | `float` | True peak in dBTP |
| `loudness_range` | `float` | Loudness range in LU |

### `LoudnessComparison`

| Field | Type | Description |
| --- | --- | --- |
| `file_a` | `LoudnessResult` | Reference file measurements |
| `file_b` | `LoudnessResult` | Comparison file measurements |

Properties: `lufs_delta`, `peak_delta`, `lra_delta`

### `SpectralBand`

Energy measurement for a single frequency band.

| Field | Type | Description |
| --- | --- | --- |
| `name` | `str` | Band name (e.g., "Low", "Mid", "High") |
| `low_hz` | `float` | Lower frequency bound |
| `high_hz` | `float` | Upper frequency bound |
| `energy_db_a` | `float` | Energy in dB for reference file |
| `energy_db_b` | `float` | Energy in dB for comparison file |

Properties: `delta_db`

### `SpectralComparison`

| Field | Type | Description |
| --- | --- | --- |
| `bands` | `list[SpectralBand]` | Per-band energy comparison |

### `Segment`

A detected segment in the temporal comparison.

| Field | Type | Description |
| --- | --- | --- |
| `kind` | `SegmentKind` | Classification: `SIMILAR`, `ADDED`, `REMOVED`, `CHANGED` |
| `start_time` | `float` | Start time in seconds |
| `end_time` | `float` | End time in seconds |
| `correlation` | `float \| None` | Cross-correlation coefficient (for similar/changed segments) |
| `time_shift` | `float \| None` | Time offset in seconds (if shifted) |

Properties: `duration`

### `TemporalComparison`

| Field | Type | Description |
| --- | --- | --- |
| `segments` | `list[Segment]` | Detected segments with classification |
| `overall_correlation` | `float` | Overall waveform correlation coefficient |

### `ClipEvent`

A detected clipping event.

| Field | Type | Description |
| --- | --- | --- |
| `file_label` | `str` | Which file the clipping was found in |
| `timestamp` | `float` | Time position in seconds |
| `channel` | `int` | Channel index (0-based) |
| `sample_count` | `int` | Number of consecutive clipped samples |

### `SilenceRegion`

A detected region of silence.

| Field | Type | Description |
| --- | --- | --- |
| `file_label` | `str` | Which file the silence was found in |
| `start_time` | `float` | Start time in seconds |
| `end_time` | `float` | End time in seconds |

Properties: `duration`

### `DetectionResult`

| Field | Type | Description |
| --- | --- | --- |
| `clips` | `list[ClipEvent]` | All clipping events across both files |
| `silence_regions_a` | `list[SilenceRegion]` | Silence regions in the reference file |
| `silence_regions_b` | `list[SilenceRegion]` | Silence regions in the comparison file |

## Report

### `sounddifff.report.render(result, fmt, output_path=None) -> str`

Render a `DiffResult` in the specified format.

```python
from sounddifff.report import render
from sounddifff.types import OutputFormat

# Terminal output (colored text)
print(render(result, OutputFormat.TERMINAL))

# JSON string
json_str = render(result, OutputFormat.JSON)

# HTML written to file
render(result, OutputFormat.HTML, output_path="report.html")
```

### `OutputFormat`

Enum with three values: `TERMINAL`, `JSON`, `HTML`.

## Formats

### `sounddifff.formats.load_audio(path) -> tuple[ndarray, AudioMetadata]`

Load an audio file and return the signal as a float64 numpy array (shape: frames x channels) along with its metadata. Mono files are returned with shape (frames, 1).

### `sounddifff.formats.format_duration(seconds) -> str`

Format a duration as `M:SS.mmm` (e.g., `3:42.108`).
