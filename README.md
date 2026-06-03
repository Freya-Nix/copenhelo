# VIBE CODE WARNING

This is all vibe coded, I wanted to make sure this works before commiting too much time. Don't trust anything and reach out on the Danish Pauper Discord if you have questions

# Copenhelo ELO Rating System

An automated ELO rating system for Magic: The Gathering tournaments. Parses tournament data, calculates ratings, and generates leaderboards.

## Setup

```bash
make install
```

This creates a Python virtual environment and installs dependencies.

## Data Structure

### Input Format

Tournament files go in `input/{YYYYMMDD}_{format}_{location}/` with round-by-round HTML files:

```
input/
└── 20260530_pauper_baltzer/
    ├── r1.htm
    ├── r2.htm
    ├── r3.htm
    └── r4.htm
```

Files are EventLink HTML export files with pairings tables.

## Pipeline

### Step 1: Parse Tournaments

```bash
make run-parse
```

**Script:** `scripts/parse_tournaments.py`

- Reads HTML files from `input/{tournament_id}/`
- Extracts match data (players, results, byes)
- Outputs:
  - `events/{tournament_id}.json` - Clean tournament data
  - `events/parsed_events.csv` - Log of parsed tournaments (prevents re-parsing)
- Logs detailed round-by-round match counts

**Idempotency:** Checks `parsed_events.csv` to skip already-parsed tournaments.

### Step 2: Calculate ELO Ratings

```bash
make run-elo
```

**Script:** `scripts/elo_calculator.py`

- Reads all `events/*.json` files
- Calculates ELO ratings (K=32, default=1500)
- Outputs:
  - `output/players.json` - Player ratings and match history
  - `output/tournaments.json` - Tournament metadata
- Logs every match with rating changes

**Idempotency:** Checks `output/tournaments.json` to skip already-calculated tournaments.

**ELO Formula:**
```
expected_score = 1 / (1 + 10^((opponent_rating - current_rating) / 400))
rating_change = K * (result - expected_score)
new_rating = current_rating + rating_change
```

### Step 3: Generate Pages

```bash
make run
```

Runs all five generators in sequence:

#### Leaderboard (`scripts/leaderboard_generator.py`)
- Outputs: `leaderboard.html`
- Sorted by rating (highest first)
- Links to player detail pages

#### Player Pages (`scripts/players_generator.py`)
- Outputs: `players.html`
- Collapsible player sections
- Full match history with tournament links
- Auto-expands player when navigated via hash anchor

#### Tournament Pages (`scripts/tournaments_generator.py`)
- Outputs: `tournaments.html`
- All tournaments in chronological order
- Match results by round
- Tournament names linked from player pages

## Full Pipeline

Run everything in sequence:

```bash
make run
```

Order: Parse → ELO Calculate → Generate Pages

This executes:
1. `parse_tournaments.py` - Extract tournament data
2. `elo_calculator.py` - Calculate ratings
3. `leaderboard_generator.py` - Generate leaderboard.html
4. `players_generator.py` - Generate players.html
5. `tournaments_generator.py` - Generate tournaments.html

## Recalculation

To clear all processed data and recalculate from scratch:

```bash
make recalculate
```

**Script:** `scripts/recalculate_history.py`

- Clears `events/parsed_events.csv`
- Clears `output/` directory
- Re-runs ELO calculation from all `events/*.json` files
- Useful if tournament dates need reordering

## Logging

All scripts log to `log.txt` with timestamps. Logs are appended in chronological order.

Format: `[YYYY-MM-DDTHH:MM:SS.SSSSSS] message`

- **Parsing logs:** Round-by-round match counts
- **ELO logs:** Every match with result and rating changes
- **Generation logs:** Output file locations and counts

## GitHub Actions Workflow

The file `.github/workflows/update-elo.yml` automatically runs the pipeline daily.

### Trigger

- **Schedule:** Daily at 00:00 UTC (midnight)
- **Manual:** Via `workflow_dispatch` (can run from GitHub UI)

### Steps

1. **Checkout** - Clone the repository
2. **Setup Python** - Install Python 3.11
3. **Install dependencies** - Run `make install`
4. **Parse tournaments** - Run `make run-parse`
5. **Calculate ratings** - Run `make run-elo`
6. **Generate pages** - Run leaderboard, player, and tournament generators
7. **Commit and push** - Commits changes back to main branch
   - Only commits if files changed (checks with MD5)
   - Includes updated HTML pages and log.txt

### Deployment

After workflow completion:
- All generated HTML files are committed
- GitHub Pages serves the files automatically (if enabled)
- **leaderboard.html** - Main page (can be served as index)
- **players.html** - Player details
- **tournaments.html** - Tournament results

### To Enable GitHub Pages

1. Go to repo Settings → Pages
2. Source: Select "main branch"
3. Pages will be available at `https://username.github.io/copenhelo/`

Or to serve from root:
1. Rename `leaderboard.html` to `index.html`
2. Update links in HTML files to match

## File Structure

```
copenhelo/
├── input/                          # Tournament input files
│   └── {YYYYMMDD}_{format}_{loc}/
│       ├── r1.htm
│       ├── r2.htm
│       └── ...
├── events/                         # Parsed event data (generated)
│   ├── {tournament_id}.json
│   └── parsed_events.csv
├── output/                         # ELO rating data (generated)
│   ├── players.json
│   └── tournaments.json
├── scripts/
│   ├── parse_tournaments.py        # HTML → Events
│   ├── elo_calculator.py           # Events → Ratings
│   ├── leaderboard_generator.py    # Ratings → leaderboard.html
│   ├── players_generator.py        # Ratings → players.html
│   ├── tournaments_generator.py    # Ratings → tournaments.html
│   └── recalculate_history.py      # Remove data and recalculate
├── leaderboard.html                # Generated after run
├── players.html                    # Generated after run
├── tournaments.html                # Generated after run
├── log.txt                         # All script output logs
└── Makefile                        # Command shortcuts
```

## Commands Summary

| Command | Action |
|---------|--------|
| `make install` | Create virtual environment |
| `make run` | Run full pipeline (parse → elo → pages) |
| `make run-parse` | Parse tournaments only |
| `make run-elo` | Calculate ratings only |
| `make recalculate` | Clear data and recalculate everything |
| `make help` | Show available commands |

## Example Workflow

1. **Add tournament:** Place HTML files in `input/20260603_modern_cph/`
2. **Run pipeline:** `make run`
3. **Check logs:** `cat log.txt` to see parsed rounds and rating changes
4. **View results:** Open `leaderboard.html` in browser
5. **Explore:** Click player names to see history, tournament names to see results

## Notes

- All scripts use buffered logging with timestamps
- Idempotency prevents re-processing tournaments
- ELO calculations are executed in round order
- Players start at rating 1500 if new
- HTML files are overwritten on each generation (safe to delete)
- Data files (JSON, CSV) are never deleted (only appended)
