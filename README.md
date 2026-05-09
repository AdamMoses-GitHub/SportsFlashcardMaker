# Team Logo Flashcards

This project downloads team logos and generates print-ready **front/back flashcard images** with white backgrounds.

## Supported Sets

### Professional (American)

| Code | League |
|---|---|
| `mlb` | MLB |
| `nfl` | NFL |
| `nba` | NBA |
| `nhl` | NHL |
| `wnba` | WNBA |
| `mls` | MLS |
| `nwsl` | NWSL |
| `ufl` | UFL |

### English Football

| Code | League |
|---|---|
| `epl` | Premier League |
| `efl_championship` | EFL Championship |
| `efl_league_one` | EFL League One |
| `efl_league_two` | EFL League Two |

### College Football Conferences

| Code | Conference |
|---|---|
| `acc` | ACC |
| `big_ten` | Big Ten |
| `big_12` | Big 12 |
| `sec` | SEC |
| `mac` | MAC |
| `aac` | AAC |
| `ivy_league` | Ivy League |
| `pac_12` | Pac-12 |

## What you get

- Generates print-ready PNGs for every team in the selected set.
- Default card size is **6×4 inches** (landscape) at **300 DPI** (1800×1200 px). Fully configurable.
- Logos are centered and scaled to fit while preserving aspect ratio.
- Two files per team by default:
  - Front side: centered logo on white background
  - Back side: large centered team-name text (auto multi-line, auto-sized)
- Alternative output modes: logo only, text only, or combined logo+text on one card.
- Each output folder includes a `README.md` summarizing the generation settings and files created.

## Architecture

The project separates business logic from user interfaces:

- **Core Logic** (`src/sports_flashcard_maker/core.py`) — pure business logic, zero UI dependencies
- **CLI** (`src/sports_flashcard_maker/cli.py`) — command-line interface
- **GUI** (`src/sports_flashcard_maker/gui.py`) — tkinter desktop GUI
- **Supporting Modules**:
  - `teams.py` — set definitions and logo configuration
  - `download_logos.py` — logo downloader
  - `flashcards.py` — flashcard image renderer

## Setup

### Conda (recommended)

```powershell
conda create -p .conda python=3.13 -y
conda activate .\.conda
pip install -e .
```

### venv

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## Usage

### Command Line (CLI)

```powershell
sports-flashcards --set mlb
sports-flashcards --set nfl
sports-flashcards --set nba
sports-flashcards --set nhl
sports-flashcards --set wnba
sports-flashcards --set mls
sports-flashcards --set nwsl
sports-flashcards --set ufl
sports-flashcards --set epl
sports-flashcards --set efl_championship
sports-flashcards --set efl_league_one
sports-flashcards --set efl_league_two
sports-flashcards --set acc
sports-flashcards --set big_ten
sports-flashcards --set big_12
sports-flashcards --set sec
sports-flashcards --set mac
sports-flashcards --set aac
sports-flashcards --set ivy_league
sports-flashcards --set pac_12
```

Multiple sets in one command:

```powershell
sports-flashcards --set mlb nfl nba nhl
```

#### All Options

| Option | Default | Description |
|---|---|---|
| `--set` | `mlb` | One or more set codes (see table above) |
| `--output-dir` | `output/<SET>/` | Output folder |
| `--logos-dir` | `data/logos_raw` | Logo download/cache folder |
| `--dpi` | `300` | Image DPI |
| `--card-ratio` | `3x2` | Card size ratio (see table below) |
| `--card-output-mode` | `logo_text` | `logo_text`, `logo_only`, `text_only`, or `combined` |
| `--filename-format` | `prefix` | `prefix` (LABEL_TEAM.png) or `suffix` (TEAM_LABEL.png) |
| `--side-labels` | `front_back` | `front_back` or `logo_text` |
| `--name-format` | `full` | `full`, `team_only`, or `city_only` |
| `--name-order` | `city_first` | `city_first` or `team_first` (full format only) |
| `--split-text-colors` | off | Render location and team name in different colors on back |
| `--location-color` | `#1f4e79` | Location text color when split colors are on |
| `--team-color` | `#b22222` | Team text color when split colors are on |

#### Card Ratios

| Ratio | Size | Orientation |
|---|---|---|
| `1x1` | 4×4 in | Square |
| `3x2` | 6×4 in | Landscape |
| `2x3` | 4×6 in | Portrait |
| `5x4` | 5×4 in | Landscape |
| `4x5` | 4×5 in | Portrait |
| `7x5` | 7×5 in | Landscape |
| `5x7` | 5×7 in | Portrait |
| `8x10` | 8×10 in | Portrait |
| `10x8` | 10×8 in | Landscape |

### Desktop GUI

```powershell
sports-flashcards-gui
```

Or run directly:

```powershell
python -m sports_flashcard_maker.gui
```

The GUI has three tabs:

- **Sets** — checkboxes grouped by Professional, English Football, and College Football
- **Settings** — DPI slider, card ratio, output folder, card output mode, filename pattern, team text options, and split text colors
- **Output** — filename preview, run summary, and live run log

## Output Structure

```
output/
  MLB/
  NFL/
  NBA/
  NHL/
  WNBA/
  MLS/
  NWSL/
  UFL/
  PREMIER_LEAGUE/
  EFL_CHAMPIONSHIP/
  EFL_LEAGUE_ONE/
  EFL_LEAGUE_TWO/
  ACC/
  BIG_TEN/
  BIG_12/
  SEC/
  MAC/
  AAC/
  IVY_LEAGUE/
  PAC_12/
```

Default filenames (prefix style, full name format):

```
front_arizona_diamondbacks.png
back_arizona_diamondbacks.png
```

## Notes

- Logos are fetched from ESPN CDN/API endpoints.
- Split text colors (location vs. team) are not supported for soccer sets that do not expose separate location/team name fields (EPL, EFL leagues, NWSL).
- For extended configuration examples (filename formats, name formats, batch generation), see [EXTENDED_CONFIG.md](EXTENDED_CONFIG.md).
