# Usage

## Basic comparison

```sh
sounddifff old-mix.wav new-mix.wav
```

This runs all analyses (loudness, spectral, temporal, detection) and prints a colored terminal report.

The first argument is the reference file. The second is the file you're comparing against it. Deltas are reported as changes from the first file to the second (positive means the second file is louder, has more energy in a band, etc.).

## Output formats

### Terminal (default)

```sh
sounddifff a.wav b.wav
```

Colored, grouped by category. Designed to be read top to bottom. Loudness changes are highlighted in red (louder) or green (quieter). Clipping and other issues are flagged at the bottom.

### JSON

```sh
sounddifff a.wav b.wav --format json
```

Structured JSON with the same data as the terminal output. Every measurement is included with both raw values and computed deltas. Useful for piping to [jq](https://jqlang.github.io/jq/), parsing in scripts, or integrating into CI pipelines.

### HTML

```sh
sounddifff a.wav b.wav --format html -o report.html
```

Self-contained HTML file with inline styles. No external dependencies, no JavaScript. Open it in any browser, email it, or archive it alongside your session files.

## Failing on changes (`--fail-if`)

```sh
sounddifff reference.wav render.wav --fail-if "lufs>1,peak>0.5,clipping"
```

Rules are comma-separated. Numeric rules (`lufs`, `peak`, `lra`, `band`, `duration` with `>N`; `correlation` with `<N`)
compare the absolute change between the two files. Flag rules (`clipping`, `silence`, `format`) check for problems in
the second file. The report is printed as usual; each broken rule is written to stderr as `FAIL <rule>: <detail>`.

Exit codes: `0` all rules pass, `1` error (unreadable file, unsupported format), `2` invalid command line or rule,
`3` at least one rule failed.

## CLI options

| Flag | Description |
| --- | --- |
| `--format` | Output format: `terminal`, `json`, or `html` |
| `-o, --output` | Write output to a file (required for HTML, optional for others) |
| `--verbose` | Show additional detail in the output |
| `--no-color` | Disable colored terminal output (useful when piping to a file) |
| `--version` | Print the installed version and exit |
| `--help` | Print help text and exit |

## Supported audio formats

| Format | Extension | Requires ffmpeg |
| --- | --- | --- |
| WAV | `.wav` | No |
| FLAC | `.flac` | No |
| OGG Vorbis | `.ogg` | No |
| AIFF | `.aiff`, `.aif` | No |
| MP3 | `.mp3` | Yes |
| AAC | `.aac`, `.m4a` | Yes |
| WMA | `.wma` | Yes |
| Opus | `.opus` | Yes |

## Understanding the output

### Metadata section

Compares duration, sample rate, and channel count between the two files. If sample rates differ, sounddifff warns you that comparison accuracy may be reduced.

### Loudness section

Three measurements per file:

- **LUFS** (Loudness Units Full Scale): integrated loudness per ITU-R BS.1770. The standard measurement for broadcast and streaming loudness.
- **True Peak (dBTP)**: the maximum sample amplitude in decibels. Values above -1.0 dBTP are a concern for inter-sample clipping in lossy codecs.
- **LRA** (Loudness Range): the difference between the 95th and 10th percentile of short-term loudness. Higher LRA means more dynamic range.

### Spectral section

Average energy per frequency band, reported as a delta in dB. Default bands are:

- **Low**: 20-250 Hz (bass, kick, sub)
- **Mid**: 250 Hz - 4 kHz (vocals, guitars, keys)
- **High**: 4-20 kHz (cymbals, air, presence)

A positive delta means the second file has more energy in that band.

### Segments section

Compares the waveform in chunks using cross-correlation. Each segment is classified as:

- **similar**: correlation above the threshold (default 0.9)
- **changed**: content exists in both files at that position but differs significantly
- **added**: content exists in the second file but not the first
- **removed**: content exists in the first file but not the second

### Issues section

Flags potential problems detected in either file:

- **Clipping**: consecutive samples at maximum amplitude. Reports the timestamp, channel, and number of clipped samples.
- **Silence**: regions below the silence threshold (default -60 dBFS) lasting longer than the minimum duration (default 100ms).

## CI usage

Use JSON output and parse the results in your CI pipeline:

```sh
# Check if loudness changed by more than 0.5 dB
sounddifff reference.wav output.wav --format json | jq '.loudness.lufs_delta'
```

See [`examples/ci_regression_test.py`](../examples/ci_regression_test.py) for a complete example with configurable thresholds and pass/fail exit codes.
