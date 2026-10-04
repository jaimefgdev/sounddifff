# Installation

## From PyPI

```sh
pip install sounddiff
```

Requires Python 3.10 or later.

## From source

```sh
git clone https://github.com/jaimefgdev/sounddiff.git
cd sounddiff
pip install -e ".[dev]"
```

This installs sounddiff in editable mode with all development dependencies (pytest, ruff, mypy, hypothesis, pre-commit).

## System dependencies

sounddiff uses [libsndfile](http://www.mega-nerd.com/libsndfile/) for audio I/O. The `soundfile` Python package bundles it on most platforms, but you may need to install it separately.

**macOS:**

```sh
brew install libsndfile
```

**Ubuntu/Debian:**

```sh
sudo apt-get install libsndfile1
```

**Windows:** Bundled automatically via pip. No extra steps.

## Optional: ffmpeg

Core formats (WAV, FLAC, OGG, AIFF) work without any extra dependencies. For MP3, AAC, M4A, WMA, and OPUS, you need [ffmpeg](https://ffmpeg.org/) installed and available on your PATH.

```sh
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows (via chocolatey)
choco install ffmpeg
```

sounddiff checks for ffmpeg at runtime. If you try to compare an MP3 without ffmpeg installed, you'll get a clear error message telling you what to do.

## Shell completions

sounddiff uses [click](https://click.palletsprojects.com/) which provides shell completion out of the box.

**bash** (add to `~/.bashrc`):

```sh
eval "$(_SOUNDDIFF_COMPLETE=bash_source sounddiff)"
```

**zsh** (add to `~/.zshrc`):

```sh
eval "$(_SOUNDDIFF_COMPLETE=zsh_source sounddiff)"
```

**fish** (add to `~/.config/fish/config.fish`):

```sh
_SOUNDDIFF_COMPLETE=fish_source sounddiff | source
```

## Verifying the installation

```sh
sounddiff --version
```

This should print the installed version number.
