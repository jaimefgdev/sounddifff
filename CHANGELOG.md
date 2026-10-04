# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0]

Changes by Jaime Fernández González ([@jaimefgdev](https://github.com/jaimefgdev)).

### Added
- `sounddifff check FILE --preset ...`: checks one file against Spotify, YouTube, Apple Music, podcast, EBU R 128
  or ATSC A/85 targets (integrated loudness, true peak with 4x oversampling, clipping) and suggests the gain to
  apply. New module `sounddifff.compliance`.
- Folder comparison: `sounddifff dir_a/ dir_b/` pairs files by relative path, compares each pair, lists files that
  exist on one side only and honours `--fail-if`. New module `sounddifff.batch`.
- GitHub Action: `preset` input (check one file), folder support and `comment: true` to post the result on pull
  requests (one comment, updated on every push).
- README image of the HTML report.

### Fixed
- The HTML template lived outside the package, so installed copies silently fell back to a much simpler report.
  It now ships inside the package.
- HTML report: the footer printed the first file's path instead of the version; Windows paths were not shortened to
  file names; spectral columns were misaligned.
- Reports listed every clipping event (thousands on long files); they now list the first 20 and count the rest.

## [0.3.0] — sounddifff

Changes by Jaime Fernández González ([@jaimefgdev](https://github.com/jaimefgdev)), maintainer since October 2026.

### Added
- `--fail-if` option: rules such as `lufs>1,peak>0.5,band>3,clipping` turn a comparison into a regression test.
  Exit code 3 when a rule is broken (1 stays for errors, 2 for invalid command lines). New module
  `sounddifff.thresholds` with 19 tests.
- GitHub Action (`uses: jaimefgdev/sounddifff@v0.3.0`): runs the comparison, writes the report to the job summary,
  uploads the HTML report and fails the step when a rule is broken. Tested in CI on every push.

### Changed
- Renamed to **sounddifff** (package, command, Python module and repository). The `sounddiff` name on PyPI belongs to
  the original author, so new versions are published as `sounddifff`.
- The version is defined once, in `src/sounddifff/__init__.py`; the package metadata reads it from there (it said
  0.1.0 while PyPI was at 0.2.1).
- CI now tests Linux, Windows and macOS on Python 3.10, 3.13 and 3.14.
- Removed the Sentry release workflow, which depended on the original author's account.
- README and LICENSE credit systemBlue as the original author and record the current maintainer.

### Fixed
- CI: mypy now targets Python 3.12, because NumPy 2.3+ type stubs use 3.12 syntax and broke the lint job.
  Python 3.10 compatibility is still enforced by ruff (`py310`) and the test matrix.
- Links, badges, CODEOWNERS and security contact pointed to the original account, which no longer exists.

## [0.2.1] and earlier — systemBlue

Original work by systemBlue, published on PyPI up to version 0.2.1 (March 2026).

### Added
- Project scaffolding with src layout and hatchling build system
- CI pipeline with Python 3.10-3.13 matrix on Linux and macOS
- Pre-commit hooks (ruff, mypy, gitleaks)
- Core analysis modules: loudness, spectral, temporal, detection
- CLI with click: `sounddiff <file1> <file2>`
- Output formats: terminal (rich), JSON, HTML
- Test infrastructure with pytest and hypothesis
