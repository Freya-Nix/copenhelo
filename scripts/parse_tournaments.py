#!/usr/bin/env python3
"""
Parse tournament HTML files and extract clean event data.
Stores results in events/ folder and logs to log.txt
"""

import json
import csv
from pathlib import Path
from datetime import datetime
import sys
import re
from bs4 import BeautifulSoup


class EventParser:
    """Parse EventLink HTML tournament files and extract clean data."""
    
    def __init__(self, log_file: Path = None):
        self.log_file = log_file or Path('log.txt')
        self.log_buffer = []  # Buffer log entries
    
    def log(self, message: str):
        """Buffer message to be logged at end."""
        timestamp = datetime.now().isoformat()
        self.log_buffer.append(f"[{timestamp}] {message}")
        print(message)
    
    def flush_logs(self):
        """Write all buffered logs to file (append to file)."""
        if not self.log_buffer:
            return
        
        # Append entries to end of file
        new_entries = "\n".join(self.log_buffer) + "\n"
        with open(self.log_file, 'a') as f:
            f.write(new_entries)
    
    def parse_tournament_file(self, filepath: Path) -> list:
        """
        Parse a tournament HTML file and extract match data.
        
        Returns:
            List of match dictionaries with keys: table, player1, player2, result, has_bye
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        matches = []
        
        # Find pairings table
        table = soup.find('table', class_='pairings-table')
        if not table:
            self.log(f"Warning: No pairings table found in {filepath}")
            return matches
        
        tbody = table.find('tbody')
        if not tbody:
            return matches
        
        # Parse each match row
        for row in tbody.find_all('tr'):
            cells = row.find_all('td', class_='pairings-table__cell')
            if len(cells) < 6:
                continue
            
            # Extract table number
            table_num = cells[0].get_text(strip=True)
            
            # Extract player 1
            player1_cell = cells[2]
            player1_name = self._extract_player_name(player1_cell)
            if not player1_name:
                continue
            
            # Extract score
            result_cell = cells[3]
            result = self._extract_match_result(result_cell)
            
            # Extract player 2 or bye
            player2_cell = cells[4]
            bye_div = player2_cell.find('div', class_='bye')
            
            if bye_div:
                # Player 1 got a bye
                matches.append({
                    'table': table_num if table_num else None,
                    'player1': player1_name,
                    'player2': None,
                    'result': None,
                    'has_bye': True
                })
            else:
                player2_name = self._extract_player_name(player2_cell)
                if player2_name:
                    matches.append({
                        'table': table_num if table_num else None,
                        'player1': player1_name,
                        'player2': player2_name,
                        'result': result,
                        'has_bye': False
                    })
        
        return matches
    
    @staticmethod
    def _extract_player_name(cell) -> str:
        """Extract player name from table cell."""
        team_div = cell.find('div', class_='team')
        if not team_div:
            return None
        
        name_span = team_div.find('span', class_='team__text')
        if name_span:
            # Get the innermost span with the actual name
            name_elem = name_span.find('span')
            if name_elem:
                return name_elem.get_text(strip=True)
        
        return None
    
    @staticmethod
    def _extract_match_result(cell) -> tuple:
        """
        Extract match result from result cell.
        Returns tuple (player1_wins, player2_wins) or None if no result.
        """
        scores = cell.find_all('div', class_='box-score')
        if len(scores) >= 2:
            try:
                p1_score = int(scores[0].get_text(strip=True))
                p2_score = int(scores[1].get_text(strip=True))
                return (p1_score, p2_score)
            except (ValueError, AttributeError):
                pass
        
        return None


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    input_dir = repo_root / 'input'
    events_dir = repo_root / 'events'
    csv_file = events_dir / 'parsed_events.csv'
    log_file = repo_root / 'log.txt'
    
    # Create events directory
    events_dir.mkdir(exist_ok=True)
    
    # Initialize CSV if it doesn't exist
    if not csv_file.exists():
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'tournament_id', 'rounds', 'matches', 'file'])
            writer.writeheader()
    
    parser = EventParser(log_file)
    parser.log("Starting tournament parsing")
    
    # Load already parsed tournaments from CSV
    parsed_tournaments = set()
    if csv_file.exists() and csv_file.stat().st_size > 0:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row and 'tournament_id' in row:
                    parsed_tournaments.add(row['tournament_id'])
    
    processed_count = 0
    skipped_count = 0
    
    # Find all tournament directories
    for tournament_dir in sorted(input_dir.iterdir()):
        if not tournament_dir.is_dir():
            continue
        
        tournament_id = tournament_dir.name
        
        # Check if already parsed
        if tournament_id in parsed_tournaments:
            parser.log(f"Skipping tournament {tournament_id} (already parsed)")
            skipped_count += 1
            continue
        
        parser.log(f"Parsing tournament: {tournament_id}")
        tournament_data = {
            'id': tournament_id,
            'rounds': {},
            'parsed_at': datetime.now().isoformat()
        }
        
        # Find all round files
        round_files = sorted(
            tournament_dir.glob('r*.htm'),
            key=lambda p: int(re.search(r'r(\d+)', p.name).group(1))
        )
        
        total_matches = 0
        round_count = len(round_files)
        
        for round_file in round_files:
            match = re.search(r'r(\d+)', round_file.name)
            if not match:
                continue
            
            round_num = int(match.group(1))
            
            matches = parser.parse_tournament_file(round_file)
            tournament_data['rounds'][str(round_num)] = {
                'matches': matches,
                'count': len(matches)
            }
            
            total_matches += len(matches)
            parser.log(f"  Parsed round {round_num}: {len(matches)} matches")
        
        # Save tournament data as JSON
        output_file = events_dir / f'{tournament_id}.json'
        with open(output_file, 'w') as f:
            json.dump(tournament_data, f, indent=2)
        
        # Add to CSV
        with open(csv_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'tournament_id', 'rounds', 'matches', 'file'])
            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'tournament_id': tournament_id,
                'rounds': round_count,
                'matches': total_matches,
                'file': output_file.name
            })
        
        parser.log(f"Parsed tournament {tournament_id}: {round_count} rounds, {total_matches} matches -> events/{output_file.name}")
        processed_count += 1
    
    parser.log(f"Tournament parsing complete: {processed_count} processed, {skipped_count} skipped")
    parser.flush_logs()  # Write all logs at end


if __name__ == '__main__':
    main()
