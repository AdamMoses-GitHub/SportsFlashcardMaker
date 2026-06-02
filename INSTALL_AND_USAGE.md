# Sports Flashcard Maker — Install & Usage Guide

## What This Tool Lets You Do

- Download official team logos from ESPN's public API (no key needed) for 40+ leagues and conferences
- Generate print-ready PNG flashcard images in three styles: logo-only, text-only, and combined
- Choose from nine card aspect ratios and set print DPI for any output size
- Control filename conventions, team name formatting, text colors, font sizes, and card index numbering
- Overlay a league or conference logo in any corner of every card
- Run everything from the command line or through a desktop GUI
- Batch-generate multiple sets in a single command with per-set output folders

---

## Installation

### Method A — Conda (Recommended)

Creates an isolated environment with Python 3.13 and installs the package in editable mode.

```powershell
conda create -p .conda python=3.13 -y
conda activate .\.conda
pip install -e .
```

Both entry points (`sports-flashcards` and `sports-flashcards-gui`) are now on your PATH inside the environment.

### Method B — venv (Quick)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

> Requires Python ≥ 3.10 already installed on the system.

---

## Running the App

### CLI

```powershell
sports-flashcards --set mlb
```

### GUI

```powershell
sports-flashcards-gui
```

Or without a script entry point:

```powershell
python -m sports_flashcard_maker
```

---

## Usage — Workflows

### 1. Generate a Simple Set (MLB)

**Scenario:** You want a standard set of MLB logo + text flashcards to print and cut.

1. Activate your environment.
2. Run the command:
   ```powershell
   sports-flashcards --set mlb
   ```
3. Logos are downloaded to `data/logos_raw/` (cached for future runs).
4. Cards are written to `output/MLB/`.
5. Each team produces two PNGs: `logo_<team>.png` and `text_<team>.png`.

**Example use case:** You want to quiz yourself on all 30 MLB teams. Run once, print the output folder double-sided, cut, done. No Photoshop, no spreadsheet.

---

### 2. Print-Quality College Football Cards

**Scenario:** You're making a full 134-team FBS set for a classroom activity and need high-DPI output with conference labels.

1. Generate all FBS teams at 600 DPI with conference shown:
   ```powershell
   sports-flashcards --set fbs_all --dpi 600 --card-types logo text combo --show-conference --card-ratio 3x2
   ```
2. Cards land in `output/FBS_ALL/` — three card types per team.
3. The `combo` type produces a single card with the logo and team name together, ideal for one-sided printing.

**Example use case:** You have a 134-team college football set. The `--show-conference` flag adds "SEC", "Big Ten", etc. below each team name on text and combo cards, giving students the extra context without a separate reference sheet.

---

### 3. Custom Styling — Split Text Colors

**Scenario:** You want visually distinctive text cards where the city name is blue and the team name is red.

1. Run with split color flags:
   ```powershell
   sports-flashcards --set nfl --card-types text --split-text-colors --location-color "#1f4e79" --team-color "#b22222"
   ```
2. Text cards render with the location in dark blue and mascot name in dark red.
3. Works for any set that has separate location and team name fields (not applicable to EPL/EFL/NWSL).

**Example use case:** You're making a color-coded study deck for a geography class. Split colors let students quickly distinguish city from team name without reading closely.

---

### 4. Batch Generation with Consistent Filenames

**Scenario:** You want the entire set of pro sports leagues with a consistent filename convention for easy sorting.

1. Run all six pro leagues in one command, suffix format, team-only names:
   ```powershell
   sports-flashcards --set mlb nfl nba nhl wnba mls --filename-format suffix --name-format team_only
   ```
2. Each league gets its own subdirectory under `output/`.
3. Files are named `<team>_logo.png` and `<team>_text.png` (suffix format).

**Example use case:** You maintain a shared drive of card sets. Suffix format puts the team name first alphabetically in file listings (`cardinals_logo.png`, `cubs_logo.png`…) instead of grouping everything under `logo_` and `text_` prefixes.

---

## Full CLI Reference

### All Options

| Option | Default | Choices / Notes |
|---|---|---|
| `--set` | `mlb` | One or more set codes; see the full list below |
| `--logos-dir` | `data/logos_raw` | Where to cache downloaded logo PNGs |
| `--output-dir` | `output/<SET>/` | Override the output destination |
| `--dpi` | `300` | DPI metadata embedded in saved PNGs |
| `--card-ratio` | `3x2` | `1x1` `3x2` `2x3` `5x4` `4x5` `7x5` `5x7` `8x10` `10x8` |
| `--card-types` | `logo text` | Any combo of `logo` `text` `combo` |
| `--filename-format` | `prefix` | `prefix` → `CARDTYPE_TEAM.png`; `suffix` → `TEAM_CARDTYPE.png` |
| `--name-format` | `full` | `full` (city+team), `team_only`, `city_only` |
| `--name-order` | `city_first` | `city_first` or `team_first`; only applies to `full` format |
| `--text-color` | `black` | Hex or named color; used when `--split-text-colors` is off |
| `--text-size` | `large` | `large` (fills card), `medium`, `small` |
| `--split-text-colors` | off | Flag; renders location and team name in separate colors |
| `--location-color` | `#1f4e79` | Location text color when `--split-text-colors` is on |
| `--team-color` | `#b22222` | Team name color when `--split-text-colors` is on |
| `--league-logo-corner` | `none` | `none` `top-left` `top-right` `bottom-left` `bottom-right` |
| `--show-conference` | off | Flag; prints conference/division below team name |
| `--abbreviate-conference` | off | Flag; uses short form (e.g. `AL` instead of `American League`) |
| `--index-corner` | `none` | `none` `top-left` `top-center` `top-right` `bottom-left` `bottom-center` `bottom-right` |
| `--force-refresh` | off | Flag; re-downloads logos even if cached copies exist |

### Card Ratio → Physical Size

| Ratio | Size at 300 DPI | Orientation |
|---|---|---|
| `1x1` | 4 × 4 in (1200 × 1200 px) | Square |
| `3x2` | 6 × 4 in (1800 × 1200 px) | Landscape |
| `2x3` | 4 × 6 in (1200 × 1800 px) | Portrait |
| `5x4` | 5 × 4 in (1500 × 1200 px) | Landscape |
| `4x5` | 4 × 5 in (1200 × 1500 px) | Portrait |
| `7x5` | 7 × 5 in (2100 × 1500 px) | Landscape |
| `5x7` | 5 × 7 in (1500 × 2100 px) | Portrait |
| `8x10` | 8 × 10 in (2400 × 3000 px) | Portrait |
| `10x8` | 10 × 8 in (3000 × 2400 px) | Landscape |

### Available Set Codes

**Pro (American)**
`mlb` · `nfl` · `nba` · `nhl` · `wnba` · `mls` · `nwsl` · `ufl`

**English Football**
`epl` · `efl_championship` · `efl_league_one` · `efl_league_two`

**FBS College Football — Individual Conferences**
`acc` · `big_ten` · `big_12` · `sec` · `aac` · `mac` · `mountain_west` · `sun_belt` · `cusa` · `ivy_league` · `pac_12` · `fbs_independents`

**FBS College Football — Bundles**
`power_four` (ACC + Big Ten + Big 12 + SEC) · `group_of_five` (AAC + MAC + Mountain West + Sun Belt + CUSA + FBS Independents) · `fbs_all` (all FBS)

**FCS College Football — Individual Conferences**
`big_sky` · `caa` · `meac` · `mvfc` · `nec` · `ovc_big_south` · `patriot` · `pioneer` · `socon` · `southland` · `swac` · `uac` · `fcs_independents`

**FCS/CFB Bundles**
`fcs_all` · `cfb_all` (every CFB team)

---

## Development

### Project Structure

```
SportsFlashcardMaker/
├── pyproject.toml              # Package metadata and entry points
├── requirements.txt            # Pinned runtime dependencies
├── EXTENDED_CONFIG.md          # Additional CLI examples and scenarios
├── data/
│   └── logos_raw/              # Downloaded logo cache (gitignored)
├── output/                     # Generated flashcard PNGs (gitignored)
│   ├── FBS_ALL/
│   ├── MLB/
│   └── UFL/
└── src/
    └── sports_flashcard_maker/
        ├── __init__.py
        ├── __main__.py         # python -m sports_flashcard_maker entry point
        ├── cli.py              # argparse CLI, calls core.py
        ├── core.py             # Pure business logic (no UI imports)
        ├── download_logos.py   # ESPN API + concurrent logo downloader
        ├── flashcards.py       # Pillow image renderer
        ├── gui.py              # tkinter desktop GUI
        └── teams.py            # All team data and FlashcardSet definitions
```

### Key Directories

| Path | Contents |
|---|---|
| `src/sports_flashcard_maker/` | All application source code |
| `data/logos_raw/` | Cached PNG logos; safe to delete, will re-download |
| `output/` | Generated flashcard PNGs; one subfolder per set |

### Running Tests

No test suite is included in this release. To validate a build manually:

```powershell
# Smoke test — generate a small set and check output
sports-flashcards --set ufl --output-dir output/test_ufl
```

### Linting / Formatting

No linter config is bundled. The codebase follows standard `ruff` / `black` conventions if you want to add them:

```powershell
pip install ruff black
ruff check src/
black src/
```

---

## Requirements

| Package | Version |
|---|---|
| Python | ≥ 3.10 |
| Pillow | ≥ 10.4.0 |
| requests | ≥ 2.32.0 |
