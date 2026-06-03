#!/usr/bin/env python3
"""
ELO Rating Calculator for Tournaments
Reads parsed tournament data from events/ and calculates ratings.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import math


class ELOCalculator:
    """Standard chess ELO rating calculator."""
    
    DEFAULT_RATING = 1500
    K_FACTOR = 32
    
    @staticmethod
    def calculate_new_rating(
        current_rating: float,
        opponent_rating: float,
        score: float,  # 1.0 = win, 0.5 = draw, 0.0 = loss
        k_factor: int = K_FACTOR
    ) -> float:
        """
        Calculate new rating using standard ELO formula.
        
        Args:
            current_rating: Player's current rating
            opponent_rating: Opponent's rating
            score: Match result (1.0 = win, 0.5 = draw, 0.0 = loss)
            k_factor: ELO K-factor (default 32)
            
        Returns:
            New rating
        """
        expected_score = 1 / (1 + math.pow(10, (opponent_rating - current_rating) / 400))
        rating_change = k_factor * (score - expected_score)
        new_rating = current_rating + rating_change
        return round(new_rating, 1)


class TournamentDataProcessor:
    """Process tournament data and calculate ratings."""
    
    def __init__(self, output_dir: Path, log_func=None):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.players_file = output_dir / 'players.json'
        self.tournaments_file = output_dir / 'tournaments.json'
        self.log_buffer = []  # Buffer for logs
        self.log_func = log_func or self._default_log
        
        self.players: Dict[str, Dict] = self._load_or_init_players()
        self.tournaments: Dict[str, Dict] = self._load_or_init_tournaments()
    
    def _default_log(self, msg: str):
        """Default log function."""
        self.log_buffer.append(msg)
        print(msg)
    
    def log(self, msg: str):
        """Buffer log message."""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {msg}"
        self.log_buffer.append(log_entry)
        print(msg)
    
    def _load_or_init_players(self) -> Dict[str, Dict]:
        """Load existing player data or initialize empty dict."""
        if self.players_file.exists():
            with open(self.players_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_or_init_tournaments(self) -> Dict[str, Dict]:
        """Load existing tournament data or initialize empty dict."""
        if self.tournaments_file.exists():
            with open(self.tournaments_file, 'r') as f:
                return json.load(f)
        return {}
    
    def process_tournament(self, tournament_id: str, round_num: int, matches: List[Dict]):
        """
        Process matches from a round and update ratings.
        
        Args:
            tournament_id: Tournament identifier
            round_num: Round number
            matches: List of match dictionaries
        """
        if tournament_id not in self.tournaments:
            self.tournaments[tournament_id] = {
                'id': tournament_id,
                'rounds': {},
                'created_at': datetime.now().isoformat()
            }
        
        round_key = str(round_num)
        self.tournaments[tournament_id]['rounds'][round_key] = {
            'matches': matches,
            'processed_at': datetime.now().isoformat()
        }
        
        # Process each match
        for match in matches:
            if match['has_bye']:
                # Initialize player if not exists, but don't change rating
                if match['player1'] not in self.players:
                    self.players[match['player1']] = {
                        'name': match['player1'],
                        'rating': ELOCalculator.DEFAULT_RATING,
                        'matches': [],
                        'history': []
                    }
            else:
                # Both players in match
                p1_name = match['player1']
                p2_name = match['player2']
                result = match['result']
                
                # Initialize players if not exist
                if p1_name not in self.players:
                    self.players[p1_name] = {
                        'name': p1_name,
                        'rating': ELOCalculator.DEFAULT_RATING,
                        'matches': [],
                        'history': []
                    }
                if p2_name not in self.players:
                    self.players[p2_name] = {
                        'name': p2_name,
                        'rating': ELOCalculator.DEFAULT_RATING,
                        'matches': [],
                        'history': []
                    }
                
                # Calculate rating change if we have a result
                if result:
                    p1_rating_before = self.players[p1_name]['rating']
                    p2_rating_before = self.players[p2_name]['rating']
                    
                    # Determine scores (1.0 = win, 0.0 = loss, 0.5 = draw)
                    p1_wins, p2_wins = result
                    if p1_wins > p2_wins:
                        p1_score = 1.0
                        p2_score = 0.0
                        result_code = 'W'
                    elif p1_wins < p2_wins:
                        p1_score = 0.0
                        p2_score = 1.0
                        result_code = 'L'
                    else:
                        # Draw
                        p1_score = 0.5
                        p2_score = 0.5
                        result_code = 'D'
                    
                    # Calculate new ratings
                    p1_new_rating = ELOCalculator.calculate_new_rating(
                        p1_rating_before,
                        p2_rating_before,
                        p1_score
                    )
                    p2_new_rating = ELOCalculator.calculate_new_rating(
                        p2_rating_before,
                        p1_rating_before,
                        p2_score
                    )
                    
                    p1_rating_change = round(p1_new_rating - p1_rating_before, 1)
                    p2_rating_change = round(p2_new_rating - p2_rating_before, 1)
                    
                    # Log the match
                    self.log(
                        f"    {p1_name} ({result_code}) {p2_name} [{p1_rating_change:+.1f} {p2_rating_change:+.1f}]"
                    )
                    
                    # Update ratings
                    self.players[p1_name]['rating'] = p1_new_rating
                    self.players[p2_name]['rating'] = p2_new_rating
                    
                    # Record match history
                    self.players[p1_name]['history'].append({
                        'tournament': tournament_id,
                        'round': round_num,
                        'opponent': p2_name,
                        'result_code': 'W' if p1_score == 1.0 else ('D' if p1_score == 0.5 else 'L'),
                        'rating_before': p1_rating_before,
                        'rating_after': p1_new_rating,
                        'rating_change': p1_rating_change,
                        'score': (p1_wins, p2_wins)
                    })
                    self.players[p2_name]['history'].append({
                        'tournament': tournament_id,
                        'round': round_num,
                        'opponent': p1_name,
                        'result_code': 'W' if p2_score == 1.0 else ('D' if p2_score == 0.5 else 'L'),
                        'rating_before': p2_rating_before,
                        'rating_after': p2_new_rating,
                        'rating_change': p2_rating_change,
                        'score': (p2_wins, p1_wins)
                    })
                    
                    # Record matches played
                    self.players[p1_name]['matches'].append({
                        'tournament': tournament_id,
                        'round': round_num,
                        'opponent': p2_name,
                        'result': result
                    })
                    self.players[p2_name]['matches'].append({
                        'tournament': tournament_id,
                        'round': round_num,
                        'opponent': p1_name,
                        'result': (p2_wins, p1_wins)  # Reversed
                    })
    
    def save(self):
        """Save player and tournament data to JSON files."""
        with open(self.players_file, 'w') as f:
            json.dump(self.players, f, indent=2, default=str)
        
        with open(self.tournaments_file, 'w') as f:
            json.dump(self.tournaments, f, indent=2, default=str)
    
    def flush_logs(self):
        """Write all buffered logs to file (prepend to existing)."""
        log_file = Path('log.txt')
        if not self.log_buffer:
            return
        
        # Read existing content
        existing_content = ""
        if log_file.exists():
            with open(log_file, 'r') as f:
                existing_content = f.read()
        
        # Write buffered entries at top
        new_entries = "\n".join(self.log_buffer) + "\n"
        with open(log_file, 'w') as f:
            f.write(new_entries + existing_content)
        
        print(f"Saved {len(self.players)} players to {self.players_file}")
        print(f"Saved {len(self.tournaments)} tournaments to {self.tournaments_file}")


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    events_dir = repo_root / 'events'
    output_dir = repo_root / 'output'
    log_file = repo_root / 'log.txt'
    
    processor = TournamentDataProcessor(output_dir)
    
    processor.log("Starting ELO calculation")
    
    # Find all tournament JSON files
    if not events_dir.exists():
        processor.log("Error: events/ directory not found. Run parse_tournaments.py first.")
        processor.flush_logs()
        return
    
    processed_count = 0
    skipped_count = 0
    
    for tournament_file in sorted(events_dir.glob('*.json')):
        tournament_id = tournament_file.stem
        
        # Check if already processed
        if tournament_id in processor.tournaments:
            processor.log(f"Skipping tournament {tournament_id} (already processed)")
            skipped_count += 1
            continue
        
        try:
            with open(tournament_file, 'r') as f:
                tournament_data = json.load(f)
            
            processor.log(f"Processing tournament: {tournament_id}")
            
            # Process each round
            for round_key, round_data in tournament_data['rounds'].items():
                round_num = int(round_key)
                matches = round_data['matches']
                processor.process_tournament(tournament_id, round_num, matches)
                processor.log(f"  Round {round_num}: {len(matches)} matches")
            
            processed_count += 1
        
        except Exception as e:
            processor.log(f"Error processing {tournament_id}: {str(e)}")
    
    processor.save()
    processor.log(f"ELO calculation complete: {processed_count} processed, {skipped_count} skipped")
    processor.flush_logs()


if __name__ == '__main__':
    main()
