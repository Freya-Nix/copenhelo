#!/usr/bin/env python3
"""
Generate HTML leaderboard from player data.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class LeaderboardGenerator:
    """Generate HTML leaderboards from player data."""
    
    def __init__(self, output_dir: Path, log_file: Path = None):
        self.output_dir = output_dir
        self.players_file = output_dir / 'players.json'
        self.log_file = log_file or Path('log.txt')
        self.log_buffer = []
    
    def log(self, message: str):
        """Buffer message to be logged at end."""
        timestamp = datetime.now().isoformat()
        self.log_buffer.append(f"[{timestamp}] {message}")
        print(message)
    
    def flush_logs(self):
        """Write all buffered logs to file (prepend to existing)."""
        if not self.log_buffer:
            return
        
        # Read existing content
        existing_content = ""
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                existing_content = f.read()
        
        # Write buffered entries at top
        new_entries = "\n".join(self.log_buffer) + "\n"
        with open(self.log_file, 'w') as f:
            f.write(new_entries + existing_content)
    
    def load_players(self) -> Dict[str, Dict]:
        """Load player data from JSON."""
        if not self.players_file.exists():
            return {}
        
        with open(self.players_file, 'r') as f:
            return json.load(f)
    
    def generate_leaderboard(self):
        """Generate main leaderboard HTML."""
        players = self.load_players()
        
        # Sort by rating
        sorted_players = sorted(
            players.values(),
            key=lambda p: p['rating'],
            reverse=True
        )
        
        html = self._generate_html(sorted_players)
        
        output_file = self.output_dir.parent / 'leaderboard.html'
        with open(output_file, 'w') as f:
            f.write(html)
        
        self.log(f"Generated leaderboard: {output_file} ({len(sorted_players)} players)")
    
    def _generate_html(self, sorted_players: List[Dict]) -> str:
        """Generate HTML content for leaderboard."""
        rows = []
        for rank, player in enumerate(sorted_players, 1):
            # Create anchor-friendly slug for player name
            slug = self._slugify(player['name'])
            rows.append(f"""
    <tr>
      <td class="rank">{rank}</td>
      <td class="name"><a href="players.html#{slug}">{player['name']}</a></td>
      <td class="rating">{player['rating']}</td>
      <td class="matches">{len(player['matches'])}</td>
    </tr>
            """)
        
        rows_html = '\n'.join(rows)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ELO Leaderboard</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 20px;
    }}
    
    .container {{
      max-width: 900px;
      margin: 0 auto;
      background: white;
      border-radius: 12px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      overflow: hidden;
    }}
    
    .header {{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 40px 20px;
      text-align: center;
    }}
    
    .header h1 {{
      font-size: 2.5em;
      margin-bottom: 10px;
    }}
    
    .header p {{
      font-size: 1.1em;
      opacity: 0.9;
    }}
    
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    
    thead {{
      background: #f8f9fa;
      border-bottom: 2px solid #dee2e6;
    }}
    
    th {{
      padding: 15px;
      text-align: left;
      font-weight: 600;
      color: #333;
    }}
    
    td {{
      padding: 15px;
      border-bottom: 1px solid #dee2e6;
    }}
    
    tr:hover {{
      background: #f8f9fa;
    }}
    
    .rank {{
      font-weight: 600;
      color: #667eea;
      width: 60px;
    }}
    
    .name {{
      font-weight: 500;
      flex-grow: 1;
    }}
    
    .name a {{
      color: #667eea;
      text-decoration: none;
      transition: color 0.2s;
    }}
    
    .name a:hover {{
      color: #764ba2;
      text-decoration: underline;
    }}
    
    .rating {{
      text-align: right;
      font-weight: 600;
      color: #764ba2;
      width: 100px;
    }}
    
    .matches {{
      text-align: center;
      color: #666;
      width: 80px;
    }}
    
    th.rank, th.rating, th.matches {{
      text-align: right;
    }}
    
    .footer {{
      background: #f8f9fa;
      padding: 20px;
      text-align: center;
      color: #666;
      font-size: 0.9em;
      border-top: 1px solid #dee2e6;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>ELO Leaderboard</h1>
      <p>Tournament Ratings</p>
    </div>
    
    <table>
      <thead>
        <tr>
          <th class="rank">Rank</th>
          <th class="name">Player</th>
          <th class="rating">Rating</th>
          <th class="matches">Matches</th>
        </tr>
      </thead>
      <tbody>
{rows_html}
      </tbody>
    </table>
    
    <div class="footer">
      <p>Last updated at runtime</p>
    </div>
  </div>
</body>
</html>
"""
        return html
    
    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to URL-friendly slug."""
        import re
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'-+', '-', text)
        text = re.sub(r' +', '-', text)
        return text


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / 'output'
    log_file = repo_root / 'log.txt'
    
    generator = LeaderboardGenerator(output_dir, log_file)
    generator.log("Starting leaderboard generation")
    generator.generate_leaderboard()
    generator.log("Leaderboard generation complete")
    generator.flush_logs()


if __name__ == '__main__':
    main()
