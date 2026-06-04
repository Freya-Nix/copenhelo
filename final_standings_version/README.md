# ELO Rating System

Extract tournament standings from HTML, calculate ELO ratings, generate leaderboard.

## Quick Start

Run the full pipeline:

```bash
make final_standings_reset
```

This clears output, extracts all HTML tournaments, calculates ratings (excluding dummy tournaments by default), and generates the leaderboard.

### Including Dummy Tournaments

To include test/dummy tournaments in the calculation:

```bash
make final_standings_reset INCLUDE_DUMMY=1
```

Or run steps individually:

```bash
# 1. Extract tournaments from HTML
python extract_standings.py input/*.htm

# 2. Calculate ratings (exclude dummy by default)
python elo_calculator.py

# 2b. Or include dummy tournaments
python elo_calculator.py --include-dummy

# 3. Generate leaderboard
python leaderboard_generator.py
```

Output: `../dummy.html` with interactive player rankings + history.

## How It Works

**Extract** → EventLink HTML to JSON standings  
**Calculate** → USCF performance rating (K-factor 64, default 1500)  
**Generate** → Interactive HTML leaderboard  

Ratings process tournaments chronologically from `parsed_events.csv`. Dummy tournaments automatically excluded.

## Key Files

| File | Purpose |
|------|---------|
| `elo_calculator.py` | Calculates cumulative player ratings |
| `leaderboard_generator.py` | Generates HTML output |
| `extract_standings.py` | Parses HTML tournament files |
| `parsed_events.csv` | Tracks processing state |
| `output/players.json` | Player ratings + history |

## Configuration

In `elo_calculator.py`:
- `K_FACTOR = 64` — Rating volatility (higher = bigger swings)
- `DEFAULT_RATING = 1500` — Starting rating

**Dummy Tournament Filtering:**
- By default, tournaments with "dummy" in their name are skipped
- Use `--include-dummy` flag to process them (dev/testing only)
- From Make: `make final_standings_reset INCLUDE_DUMMY=1`
- From CLI: `python elo_calculator.py --include-dummy`

## Data Reset

```bash
# Clear everything for fresh calculation
echo '{}' > output/players.json
echo '{}' > output/tournaments.json
# Edit parsed_events.csv: mark all as elo_calculated=no
```

Then run the quick start again.

## Notes

- Field strength automatically adjusted (uses avg opponent rating)
- Players start at 1500, evolve across tournaments
- No minimum rating (can go below 1500)
- Tournament order matters (must be chronological)
