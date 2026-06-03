#!/usr/bin/env python3
"""
Generate tournaments detail page with match results.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class TournamentsGenerator:
    """Generate detailed tournament pages with match results."""
    
    def __init__(self, output_dir: Path, log_file: Path = None):
        self.output_dir = output_dir
        self.tournaments_file = output_dir / 'tournaments.json'
        self.log_file = log_file or Path('log.txt')
        self.log_buffer = []
    
    def log(self, message: str):
        """Buffer message to be logged at end."""
        timestamp = datetime.now().isoformat()
        self.log_buffer.append(f"[{timestamp}] {message}")
        print(message)
    
    def _flush_logs(self):
        """Write all buffered logs to file (append to file)."""
        if not self.log_buffer:
            return
        
        # Append entries to end of file
        new_entries = "\n".join(self.log_buffer) + "\n"
        with open(self.log_file, 'a') as f:
            f.write(new_entries)
    
    def _load_tournaments(self) -> Dict:
        """Load tournament data from JSON."""
        if not self.tournaments_file.exists():
            return {}
        
        with open(self.tournaments_file, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to URL-friendly slug."""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'-+', '-', text)
        text = re.sub(r' +', '-', text)
        return text
    
    @staticmethod
    def _parse_tournament_id(tournament_id: str) -> tuple:
        """Parse tournament ID into date and name."""
        # Format: YYYYMMDD_format_name
        parts = tournament_id.split('_', 1)
        if len(parts) == 2:
            date_str = parts[0]
            name = parts[1].replace('_', ' ').title()
            
            # Parse date YYYYMMDD
            if len(date_str) == 8:
                year = date_str[:4]
                month = date_str[4:6]
                day = date_str[6:8]
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj, name, tournament_id
        
        return None, tournament_id, tournament_id
    
    def _generate_tournament_sections(self, tournaments: Dict) -> str:
        """Generate collapsible tournament sections."""
        # Sort tournaments by date (newest first)
        sorted_tournaments = sorted(
            tournaments.items(),
            key=lambda x: self._parse_tournament_id(x[0])[0] or datetime.min,
            reverse=True
        )
        
        sections = []
        for tournament_raw_id, tournament_data in sorted_tournaments:
            date_obj, tournament_name, tournament_id = self._parse_tournament_id(tournament_raw_id)
            
            # Format date for display in YYYY-MM-DD format
            if date_obj:
                date_str = date_obj.strftime('%Y-%m-%d')
            else:
                date_str = 'Unknown Date'
            
            rounds_html = self._generate_rounds_html(tournament_data)
            
            sections.append(f"""
    <details id="{tournament_id}">
      <summary class="tournament-summary">
        <span class="tournament-title">{date_str} {tournament_name}</span>
      </summary>
      <div class="tournament-details">
{rounds_html}
      </div>
    </details>
            """)
        
        return '\n'.join(sections)
    
    def _generate_rounds_html(self, tournament_data: Dict) -> str:
        """Generate match results for all rounds."""
        rounds = tournament_data.get('rounds', {})
        rounds_html = []
        
        for round_num in sorted(rounds.keys(), key=lambda x: int(x)):
            round_data = rounds[round_num]
            matches = round_data.get('matches', [])
            
            match_rows = []
            for match in matches:
                player1 = match.get('player1', 'Unknown')
                player2 = match.get('player2', 'BYE' if match.get('has_bye') else 'Unknown')
                result = match.get('result')
                
                # Handle None results
                if result is None:
                    result = [0, 0]
                
                score1, score2 = result[0], result[1]
                
                # Determine result
                if player2 == 'BYE':
                    result_html = '<span class="bye-badge">BYE</span>'
                elif score1 > score2:
                    result_html = f'<span class="match-score"><strong>{player1}</strong> {score1}-{score2}</span>'
                elif score2 > score1:
                    result_html = f'<span class="match-score">{score1}-{score2} <strong>{player2}</strong></span>'
                else:
                    result_html = f'<span class="match-score">{score1}-{score2} (Draw)</span>'
                
                match_rows.append(f"""
        <tr>
          <td>{player1}</td>
          <td>vs</td>
          <td>{player2}</td>
          <td>{result_html}</td>
        </tr>
                """)
            
            match_rows_html = '\n'.join(match_rows)
            
            rounds_html.append(f"""
        <div class="round">
          <h3>Round {round_num}</h3>
          <table class="matches-table">
            <thead>
              <tr>
                <th>Player 1</th>
                <th></th>
                <th>Player 2</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
{match_rows_html}
            </tbody>
          </table>
        </div>
            """)
        
        return '\n'.join(rounds_html)
    
    def _generate_html(self, tournaments: Dict) -> str:
        """Generate HTML for tournaments page."""
        tournaments_html = self._generate_tournament_sections(tournaments)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tournaments - ELO Leaderboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        header nav {{
            margin-top: 15px;
        }}
        
        header a {{
            color: rgba(255, 255, 255, 0.9);
            text-decoration: none;
            font-size: 14px;
            margin: 0 15px;
        }}
        
        header a:hover {{
            text-decoration: underline;
        }}
        
        .tournaments {{
            padding: 20px;
        }}
        
        details {{
            margin-bottom: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        details[open] {{
            background: #f9f9f9;
        }}
        
        .tournament-summary {{
            padding: 15px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
            background: #f5f5f5;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        details[open] .tournament-summary {{
            background: #efefef;
            border-bottom: 1px solid #d0d0d0;
        }}
        
        .tournament-summary:hover {{
            background: #eee;
        }}
        
        .tournament-title {{
            font-size: 16px;
            color: #333;
        }}
        
        .tournament-details {{
            padding: 20px;
        }}
        
        .round {{
            margin-bottom: 25px;
        }}
        
        .round h3 {{
            margin-bottom: 12px;
            color: #333;
            font-size: 15px;
        }}
        
        .matches-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        
        .matches-table thead {{
            background: #f5f5f5;
        }}
        
        .matches-table th {{
            padding: 10px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #ddd;
        }}
        
        .matches-table td {{
            padding: 10px;
            border-bottom: 1px solid #eee;
        }}
        
        .matches-table tbody tr:hover {{
            background: #fafafa;
        }}
        
        .match-score {{
            display: inline-block;
            background: #f0f0f0;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        
        .bye-badge {{
            display: inline-block;
            background: #fff3cd;
            color: #856404;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 12px;
        }}
        
        footer {{
            padding: 15px 20px;
            background: #f5f5f5;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            font-size: 13px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Tournaments</h1>
            <nav>
                <a href="leaderboard.html">Leaderboard</a>
                <a href="players.html">Players</a>
            </nav>
        </header>
        
        <div class="tournaments">
{tournaments_html}
        </div>
        
        <footer>
            Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
        </footer>
    </div>
    
    <script>
        // Auto-expand tournament if navigated via hash
        document.addEventListener('DOMContentLoaded', function() {{
            const hash = window.location.hash.slice(1);
            if (hash) {{
                const details = document.getElementById(hash);
                if (details) {{
                    details.open = true;
                    details.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }}
        }});
    </script>
</body>
</html>"""
        return html
    
    def generate(self) -> None:
        """Generate tournaments page."""
        tournaments = self._load_tournaments()
        html_content = self._generate_html(tournaments)
        output_path = self.output_dir.parent / 'tournaments.html'
        output_path.write_text(html_content, encoding='utf-8')
        
        self.log(f"Generated tournaments page: tournaments.html ({len(tournaments)} tournaments)")
        self._flush_logs()


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / 'output'
    log_file = repo_root / 'log.txt'
    
    generator = TournamentsGenerator(output_dir, log_file)
    generator.log("Starting tournaments page generation")
    generator.generate()
    generator.log("Tournaments page generation complete")


if __name__ == '__main__':
    main()
