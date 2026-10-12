# TubeX

TubeX is a fast, minimalist terminal app for searching YouTube videos and streaming them directly through `mpv` with full video and audio support.

## Features

- **Fast & Non-Blocking**: Background worker searches that keep the UI fluid and responsive
- **In-Memory Query Cache**: Instant return for repeated searches
- **High-Quality Playback**: Merges `bestvideo` and `bestaudio` streams synchronously through `mpv`
- **Clean Terminal UI**: Modern slate theme with clear visual hierarchy, channel labels, and duration tags
- **Custom Result Count**: Set custom result counts with `: N` syntax (e.g. `lo-fi beats : 15`)

## preview
![Tubex Preview](demo.png)


## Run It

```bash
python3 tubex.py
```

## Keybindings

| Key | Action |
| --- | --- |
| `Enter` | Submit search (in input) / Play video (in list) |
| `/` or `f` | Focus search bar |
| `c` | Clear search input |
| `↓` / `↑` | Navigate results list |
| `Esc` | Return focus to search bar |
| `q` | Quit TubeX |

## Search Syntax

Type any query in the search bar. Append `: N` at the end to request a specific number of results (up to 25).

Examples:
- `python tutorials`
- `lo-fi beats : 10`
- `linux command line:5`

## Requirements

- Python 3.10+
- `textual`
- `yt-dlp`
- `mpv`

## Installation (Arch Linux)

Directly clone the repository, install dependencies via pacman, and set up the `tubex` alias with a single command:

```bash
curl -sSL https://raw.githubusercontent.com/DevBarik731/Tubex/main/install.sh | bash
```

Or using `bash -c`:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/DevBarik731/Tubex/main/install.sh)"
```

Then reload your shell configuration (or restart your terminal) and run:

```bash
source ~/.zshrc   # for Zsh (or source ~/.bashrc for Bash)
tubex
```
