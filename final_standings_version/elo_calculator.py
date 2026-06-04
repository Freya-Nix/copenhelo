#!/usr/bin/env python3
"""
Calculate ELO ratings from tournament standings.
Reads extracted standings and updates player ratings and tournament data.
"""

import json
import math
import csv
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List


# Constants
DEFAULT_RATING = 1500
K_FACTOR = 64


def calculate_performance_rating(
    current_rating: float,
    field_avg_rating: float,
    score: float,  # 0.0 to 1.0, where 1.0 = perfect score
    num_games: int
) -> float:
    """
    Calculate performance rating using simplified USCF method.
    
    Find the rating R such that a player with rating R would be expected
    to score exactly 'score' points against the field.
    
    Args:
        current_rating: Player's current rating
        field_avg_rating: Average rating of opponents (excluding this player)
        score: Actual score as fraction (e.g., 3.5/5 = 0.7)
        num_games: Number of games played
        
    Returns:
        Performance rating
    """
    if score == 1.0:
        return field_avg_rating + 400
    elif score == 0.0:
        return field_avg_rating - 400
    
    # Binary search for performance rating
    low = 0
    high = 4000
    
    for _ in range(50):
        mid = (low + high) / 2
        expected = 1 / (1 + math.pow(10, (field_avg_rating - mid) / 400))
        
        if expected < score:
            low = mid
        else:
            high = mid
    
    return round((low + high) / 2, 1)


def calculate_new_rating(
    current_rating: float,
    performance_rating: float,
    k_factor: int = K_FACTOR
) -> float:
    """
    Calculate new rating based on performance rating.
    
    Args:
        current_rating: Player's rating before tournament
        performance_rating: Performance rating from tournament
        k_factor: K-factor (default 40)
        
    Returns:
        New rating
    """
    rating_change = k_factor * (performance_rating - current_rating) / 400
    new_rating = current_rating + rating_change
    return round(new_rating, 1)


def load_players(players_file: Path) -> Dict[str, Dict]:
    """Load players from JSON, or return empty dict if file doesn't exist."""
    if not players_file.exists():
        return {}
    
    with open(players_file, 'r') as f:
        return json.load(f)


def load_tournaments(tournaments_file: Path) -> Dict[str, Dict]:
    """Load tournaments from JSON, or return empty dict if file doesn't exist."""
    if not tournaments_file.exists():
        return {}
    
    with open(tournaments_file, 'r') as f:
        return json.load(f)


def save_players(players: Dict, players_file: Path):
    """Save players to JSON file."""
    with open(players_file, 'w') as f:
        json.dump(players, f, indent=2)


def save_tournaments(tournaments: Dict, tournaments_file: Path):
    """Save tournaments to JSON file."""
    with open(tournaments_file, 'w') as f:
        json.dump(tournaments, f, indent=2)


def get_current_rating(name: str, players: Dict) -> float:
    """Get player's current rating, default to 1500."""
    if name in players:
        return players[name]['rating']
    return DEFAULT_RATING


def process_tournament_standings(
    tournament_id: str,
    tournament_name: str,
    standings: List[Dict],
    players: Dict,
    tournaments: Dict
) -> tuple:
    """
    Process a tournament's standings and calculate ELO changes.
    
    Args:
        tournament_id: Tournament identifier
        tournament_name: Human-readable tournament name
        standings: List of standings dicts
        players: Current players data
        tournaments: Current tournaments data
        
    Returns:
        (updated_players, updated_tournaments, results_for_display)
    """
    # Calculate field average
    field_ratings = [get_current_rating(p['name'], players) for p in standings]
    total_rating = sum(field_ratings)
    
    results = []
    
    for player in standings:
        name = player['name']
        games = player['games']
        
        if games == 0:
            continue
        
        # Get current rating
        current_rating = get_current_rating(name, players)
        
        # Calculate field average excluding this player
        field_avg = (total_rating - current_rating) / (len(standings) - 1)
        
        # Calculate actual score (0.0 to 1.0)
        actual_score = player['points'] / (games * 3)
        
        # Calculate performance rating
        perf_rating = calculate_performance_rating(
            current_rating,
            field_avg,
            actual_score,
            games
        )
        
        # Calculate new rating
        new_rating = calculate_new_rating(current_rating, perf_rating, K_FACTOR)
        
        # Update player data
        if name not in players:
            players[name] = {
                'name': name,
                'rating': new_rating,
                'matches': [],
                'history': []
            }
        else:
            players[name]['rating'] = new_rating
        
        # Add to history
        history_entry = {
            'tournament': tournament_id,
            'date': datetime.now().isoformat(),
            'rank': player['rank'],
            'record': f"{player['wins']}-{player['losses']}-{player['draws']}",
            'points': player['points'],
            'rating_before': current_rating,
            'rating_after': new_rating,
            'change': new_rating - current_rating
        }
        players[name]['history'].append(history_entry)
        
        # Store result for display
        results.append({
            'name': name,
            'rank': player['rank'],
            'record': f"{player['wins']}-{player['losses']}-{player['draws']}",
            'points': player['points'],
            'old_rating': current_rating,
            'field_avg': field_avg,
            'perf_rating': perf_rating,
            'new_rating': new_rating,
            'change': new_rating - current_rating
        })
    
    # Sort by rating change
    results.sort(key=lambda x: x['change'], reverse=True)
    
    # Update tournament data
    if tournament_id not in tournaments:
        tournaments[tournament_id] = {
            'id': tournament_id,
            'name': tournament_name,
            'created_at': datetime.now().isoformat(),
            'standings': []
        }
    
    tournaments[tournament_id]['standings'] = standings
    
    return players, tournaments, results


def print_results_table(results: List[Dict]):
    """Pretty print results table."""
    print(f"\n{'Name':<25} {'Rank':<6} {'Record':<12} {'Old Elo':<10} "
          f"{'Field Avg':<12} {'Perf':<10} {'New Elo':<10} {'Change':<10}")
    print("-" * 115)
    
    for r in results:
        change_str = f"+{r['change']:.1f}" if r['change'] >= 0 else f"{r['change']:.1f}"
        print(f"{r['name']:<25} {r['rank']:<6} {r['record']:<12} "
              f"{r['old_rating']:<10.1f} {r['field_avg']:<12.1f} "
              f"{r['perf_rating']:<10.1f} {r['new_rating']:<10.1f} {change_str:<10}")


def load_processed_tournaments(csv_file: Path) -> set:
    """
    Load set of already-processed tournament IDs from parsed_events.csv.
    
    Args:
        csv_file: Path to parsed_events.csv
        
    Returns:
        Set of tournament IDs marked as elo_calculated
    """
    if not csv_file.exists():
        return set()
    
    processed = set()
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row and row.get('elo_calculated') == 'yes':
                    processed.add(row['tournament_id'])
    except (csv.Error, KeyError):
        pass
    
    return processed


def mark_tournament_processed(csv_file: Path, tournament_id: str):
    """
    Mark a tournament as processed (elo_calculated=yes) in the CSV.
    
    Args:
        csv_file: Path to parsed_events.csv
        tournament_id: Tournament identifier to mark as calculated
    """
    if not csv_file.exists():
        return
    
    # Read all rows
    rows = []
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['tournament_id'] == tournament_id:
                    row['elo_calculated'] = 'yes'
                rows.append(row)
    except (csv.Error, KeyError):
        return
    
    # Write all rows back
    try:
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'tournament_id', 'players', 'htm_parsed_to_json', 'elo_calculated', 'file'])
            writer.writeheader()
            writer.writerows(rows)
    except csv.Error:
        pass


def load_tournaments_from_json(tournaments_file: Path) -> set:
    """
    Load set of tournament IDs from tournaments.json (unused now, kept for reference).
    
    Args:
        tournaments_file: Path to tournaments.json
        
    Returns:
        Set of tournament IDs in the file
    """
    if not tournaments_file.exists():
        return set()
    
    try:
        with open(tournaments_file, 'r') as f:
            data = json.load(f)
            return set(data.keys())
    except (json.JSONDecodeError, KeyError):
        return set()


def process_all_standings(events_dir: Path, output_dir: Path, exclude_dummy: bool = True):
    """
    Process all extracted standings files and calculate ratings.
    Skips tournaments that have already been processed.
    
    Args:
        events_dir: Directory containing extracted standings JSON files
        output_dir: Directory to save output (players.json, tournaments.json)
        exclude_dummy: If True, skip tournaments with 'dummy' in the name (default: True)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    players_file = output_dir / 'players.json'
    tournaments_file = output_dir / 'tournaments.json'
    csv_file = events_dir / 'parsed_events.csv'
    
    # Load existing data
    players = load_players(players_file)
    tournaments = load_tournaments(tournaments_file)
    
    # Get already processed tournaments from CSV
    processed_tournaments = load_processed_tournaments(csv_file)
    
    # Find all standings files (excluding parsed_events.csv)
    standings_files = sorted([f for f in events_dir.glob("*.json") if f.name != 'parsed_events.csv'])
    
    if not standings_files:
        print(f"No standings files found in {events_dir}")
        return
    
    print(f"Found {len(standings_files)} standings file(s)\n")
    
    processed_count = 0
    skipped_count = 0
    
    for standings_file in standings_files:
        try:
            with open(standings_file, 'r') as f:
                data = json.load(f)
            
            tournament_id = data['tournament_id']
            
            # Skip dummy tournaments if exclude_dummy is True
            if exclude_dummy and 'dummy' in tournament_id.lower():
                print(f"Skipping: {tournament_id} (dummy tournament)")
                skipped_count += 1
                continue
            
            # Check if already processed
            if tournament_id in processed_tournaments:
                print(f"Skipping: {tournament_id} (already calculated)")
                skipped_count += 1
                continue
            
            tournament_name = tournament_id.replace("_", " ").title()
            standings = data['standings']
            
            print(f"{'='*80}")
            print(f"Processing: {tournament_name}")
            print(f"{'='*80}")
            
            # Process standings
            players, tournaments, results = process_tournament_standings(
                tournament_id,
                tournament_name,
                standings,
                players,
                tournaments
            )
            
            # Display results
            print_results_table(results)
            
            # Mark as processed in CSV
            mark_tournament_processed(csv_file, tournament_id)
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing {standings_file}: {e}")
    
    # Save all data only if we processed anything new
    if processed_count > 0:
        save_players(players, players_file)
        save_tournaments(tournaments, tournaments_file)
        print(f"\nSaved to {output_dir}")
        print(f"  - players.json")
        print(f"  - tournaments.json")
    
    print(f"\nProcessing complete: {processed_count} processed, {skipped_count} skipped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Calculate ELO ratings from tournament standings')
    parser.add_argument('--include-dummy', action='store_true', 
                       help='Include dummy tournaments (for testing/dev only)')
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    events_dir = script_dir / "events"
    output_dir = script_dir / "output"
    
    if not events_dir.exists():
        print(f"Error: {events_dir} does not exist")
        print("Run extract_standings.py first")
        return
    
    exclude_dummy = not args.include_dummy
    process_all_standings(events_dir, output_dir, exclude_dummy=exclude_dummy)


if __name__ == '__main__':
    main()
