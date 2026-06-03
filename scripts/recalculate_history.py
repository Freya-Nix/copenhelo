#!/usr/bin/env python3
"""
Recalculate ELO history from scratch.
Useful when input tournaments have outdated dates or need to be reordered.
"""

import json
from pathlib import Path
from datetime import datetime
import sys
from elo_calculator import TournamentDataProcessor, ELOCalculator


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    events_dir = repo_root / 'events'
    output_dir = repo_root / 'output'
    log_file = repo_root / 'log.txt'
    
def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    events_dir = repo_root / 'events'
    output_dir = repo_root / 'output'
    log_file = repo_root / 'log.txt'
    
    log_buffer = []
    
    def log_message(msg: str):
        """Buffer log message."""
        timestamp = datetime.now().isoformat()
        log_buffer.append(f"[{timestamp}] {msg}")
        print(msg)
    
    def flush_logs():
        """Write all buffered logs to file (append to file)."""
        if not log_buffer:
            return
        
        # Append entries to end of file
        new_entries = "\n".join(log_buffer) + "\n"
        with open(log_file, 'a') as f:
            f.write(new_entries)
    
    log_message("=" * 60)
    log_message("RECALCULATING HISTORY FROM SCRATCH")
    log_message("=" * 60)
    
    # Find all tournament JSON files
    if not events_dir.exists():
        log_message("Error: events/ directory not found.")
        flush_logs()
        return
    
    tournament_files = sorted(events_dir.glob('*.json'))
    if not tournament_files:
        log_message("No tournament files found in events/")
        flush_logs()
        return
    
    log_message(f"Found {len(tournament_files)} tournament(s)")
    
    # Create fresh processor (will load existing data but we'll clear it)
    processor = TournamentDataProcessor(output_dir, log_func=log_message)
    
    # Clear all existing data
    processor.players = {}
    processor.tournaments = {}
    log_message("Cleared existing player and tournament data")
    
    processed_count = 0
    
    # Process all tournaments in order
    for tournament_file in tournament_files:
        tournament_id = tournament_file.stem
        
        try:
            with open(tournament_file, 'r') as f:
                tournament_data = json.load(f)
            
            log_message(f"Processing tournament: {tournament_id}")
            
            # Process each round in order
            sorted_rounds = sorted(
                tournament_data['rounds'].items(),
                key=lambda x: int(x[0])
            )
            
            for round_key, round_data in sorted_rounds:
                round_num = int(round_key)
                matches = round_data['matches']
                processor.process_tournament(tournament_id, round_num, matches)
                log_message(f"  Round {round_num}: {len(matches)} matches")
            
            processed_count += 1
        
        except Exception as e:
            log_message(f"Error processing {tournament_id}: {str(e)}")
            import traceback
            log_message(traceback.format_exc())
    
    # Save the recalculated data
    processor.save()
    
    # Summary
    log_message(f"Recalculation complete!")
    log_message(f"  Tournaments processed: {processed_count}")
    log_message(f"  Players in database: {len(processor.players)}")
    log_message("=" * 60)
    
    flush_logs()


if __name__ == '__main__':
    main()
