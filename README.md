# sounddifff

[![CI](https://github.com/jaimefgdev/sounddifff/actions/workflows/ci.yml/badge.svg)](https://github.com/jaimefgdev/sounddifff/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/sounddifff)](https://pypi.org/project/sounddifff/)
[![Python](https://img.shields.io/pypi/pyversions/sounddifff)](https://pypi.org/project/sounddifff/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

> **Origin and maintenance.** sounddifff is the continuation of **sounddiff**, created by systemBlue and released
> under the MIT license ([original package on PyPI](https://pypi.org/project/sounddiff/), last version 0.2.1). The
> original repository is no longer available. This project is maintained by
> [Jaime Fernández González (jaimefgdev)](https://github.com/jaimefgdev): the original idea and the code up to March
> 2026 are systemBlue's; everything added from October 2026 onward is listed in the [CHANGELOG](CHANGELOG.md).

sounddifff is a CLI tool for audio producers and developers to compare two audio files and see exactly what changed. It reports differences in loudness, spectral balance, timing, and flags issues like clipping and silence. Output comes as colored terminal text, structured JSON, or a self-contained HTML report.

## Example

```text
$ sounddifff mix-v3.wav mix-v4.wav

sounddifff: mix-v3.wav vs mix-v4.wav

Duration     3:42.108 → 3:42.108  (no change)
Sample Rate  48000 Hz → 48000 Hz  (no change)
Channels     stereo   → stereo    (no change)

Loudness (integrated)
  LUFS       -14.2    → -12.8     (+1.4 dB)
  Peak dBTP  -1.1     → -0.3      (+0.8 dB)
  LRA         8.2     →  6.4      (-1.8 LU)

Spectral
  Low  (20-250 Hz)    +0.8 dB avg
  Mid  (250-4k Hz)    +0.3 dB avg
  High (4k-20k Hz)    +1.9 dB avg

Segments
  0:00-1:12   similar (correlation: 0.97)
  1:12-1:14   ADDED (new content, 2.1s)
  1:14-3:42   similar (correlation: 0.98, shifted +2.1s)

Issues
  ⚠ Clipping detected in mix-v4.wav at 2:31.4 (3 samples)
```

## Installation

```sh
pip install sounddifff
```

The name has three f's: the original `sounddiff` package on PyPI belongs to systemBlue and stopped at 0.2.1.
Package, command and Python module are all called `sounddifff`.

Requires Python 3.10 or later. Supports WAV, FLAC, OGG, and AIFF natively. For MP3 and AAC support, install [ffmpeg](https://ffmpeg.org/).

## Usage

Compare two files with colored terminal output:

```sh
sounddifff old-mix.wav new-mix.wav
```

Get structured JSON for scripts and CI pipelines:

```sh
sounddifff old.wav new.wav --format json
```

Generate an HTML report:

```sh
sounddifff old.wav new.wav --format html -o report.html
```

### Audio regression checks in CI

`--fail-if` turns sounddifff into a test: it prints the report as usual and exits with code 3 if any rule is broken
(code 1 is reserved for errors such as unreadable files).

```sh
sounddifff reference.wav render.wav --fail-if "lufs>1,peak>0.5,band>3,clipping"
```

| Rule | Fails when |
|---|---|
| `lufs>N` | integrated loudness changes by more than N LU |
| `peak>N` | true peak changes by more than N dB |
| `lra>N` | loudness range changes by more than N LU |
| `band>N` | any spectral band changes by more than N dB |
| `duration>N` | duration changes by more than N seconds |
| `correlation<N` | overall waveform correlation drops below N |
| `clipping` | the second file clips |
| `silence` | the second file has more silent regions than the first |
| `format` | sample rate or channel count differ |

### GitHub Action

```yaml
- uses: jaimefgdev/sounddifff@v0.3.0
  with:
    reference: audio/reference.wav
    candidate: build/render.wav
    fail-if: lufs>1,peak>0.5,clipping
```

The report is added to the job summary and uploaded as an HTML artifact; the step fails if a rule is broken.
Outputs: `passed` (`true`/`false`) and `report` (path of the HTML file).

`--fail-if` and the GitHub Action were added by Jaime Fernández González (jaimefgdev) in October 2026.

See [docs/usage.md](docs/usage.md) for all options.

## What it analyzes

| Category | Measurements |
| --- | --- |
| **Loudness** | Integrated LUFS, true peak (dBTP), loudness range (LRA) per ITU-R BS.1770 |
| **Spectral** | Average energy per frequency band (low, mid, high) with configurable ranges |
| **Temporal** | Segment-level cross-correlation, added/removed/shifted section detection |
| **Detection** | Clipping events (timestamp, channel, sample count), silence regions |
| **Metadata** | Duration, sample rate, channels, bit depth, format |

## Output formats

**Terminal** is the default. Colored, grouped by category, designed to be read top to bottom. Uses [rich](https://github.com/Textualize/rich) for formatting.

**JSON** outputs the same data in a structured format. Pipe it to [jq](https://jqlang.github.io/jq/), parse it in Python, or use it in CI pipelines for automated regression testing.

**HTML** generates a self-contained report with inline styles. No external dependencies. Open it in any browser, share it with your team, or archive it alongside your session files.

## How it's built

sounddifff is written in Python with a modular architecture. Each analysis type (loudness, spectral, temporal, detection) lives in its own module with no cross-dependencies. The core orchestrator loads two audio files, runs all analyzers, and passes the results to a formatter.

| Dependency | Purpose |
| --- | --- |
| [soundfile](https://python-soundfile.readthedocs.io/) | Audio I/O via libsndfile |
| [numpy](https://numpy.org/) | Array math, FFT, cross-correlation |
| [scipy](https://scipy.org/) | Signal processing |
| [pyloudnorm](https://github.com/csteinmetz1/pyloudnorm) | ITU-R BS.1770 loudness measurement |
| [click](https://click.palletsprojects.com/) | CLI framework |
| [rich](https://github.com/Textualize/rich) | Terminal formatting |
| [jinja2](https://jinja.palletsprojects.com/) | HTML report templates |

See [docs/architecture.md](docs/architecture.md) for the full module breakdown and data flow.

## Documentation

- [Installation](docs/install.md) - system dependencies, shell completions, ffmpeg setup
- [Usage](docs/usage.md) - CLI options and examples
- [API Reference](docs/api.md) - using sounddifff as a Python library
- [Architecture](docs/architecture.md) - module layout and design decisions

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and our development workflow.

The [issue board](https://github.com/jaimefgdev/sounddifff/issues) has open work organized by milestone. Issues labeled [`good first issue`](https://github.com/jaimefgdev/sounddifff/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) are scoped for newcomers and have enough context to get started without deep DSP knowledge.

## Security

Report vulnerabilities privately through [GitHub security advisories](https://github.com/jaimefgdev/sounddifff/security/advisories/new). See [SECURITY.md](.github/SECURITY.md) for our disclosure policy.

## License

[MIT](LICENSE)
