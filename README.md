# TubeX

TubeX is a fast, minimalist terminal app for searching YouTube videos and streaming them directly through `mpv` with full video and audio support.

## Features

- **Instant Search**: Fast YouTube video searching powered by yt-dlp flat playlist dumps
- **Keyboard Navigation Highlight**: High-contrast visual highlight with accent indicator when navigating results via `↑`/`↓`
- **Resolution Selector**: Choose from 4K, 2K, 1080p, 720p, 480p, 360p, Auto/Best, or Audio-Only with modal picker (`r`) or instant hotkeys (`1`-`8`)
- **Live Details Panel**: Live metadata sidebar showing title, channel, duration, and views
- **High-Quality Playback**: Merges selected video and audio streams synchronously through `mpv`
- **Minimal & Lightweight**: Super clean, fast codebase without heavy image processing dependencies
- **Custom Result Count**: Set custom result counts with `: N` syntax (e.g. `lo-fi beats : 15`)

## Preview
![Tubex Preview](demo.jpeg)

## Run It

```bash
python3 tubex.py
```

## Navigation & Controls

| Control | Action |
| --- | --- |
| `Enter` | Submit search (in input) / Play video (in list) |
| `r` | Open Resolution / Quality selection modal |
| `1` - `8` | Quick switch resolution (Best, 4K, 2K, 1080p, 720p, 480p, 360p, Audio) |
| `t` | Toggle sidebar preview panel on/off |
| `/` or `f` | Focus search bar |
| `c` | Clear search input |
| `↓` / `↑` | Navigate results list with highlight & update preview |
| `Esc` | Return focus to search bar / close modal |
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

```bash
git clone https://github.com/DevBarik731/Tubex.git && cd Tubex && chmod +x install.sh && ./install.sh
```
Then reload your shell configuration (or restart your terminal) and run:

```bash
source ~/.zshrc   # for Zsh (or source ~/.bashrc for Bash)
tubex
```
