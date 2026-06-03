#!/usr/bin/env python3
"""
Generate player detail pages with match history.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class PlayersGenerator:
    """Generate detailed player pages with match history."""
    
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
    
    def _flush_logs(self):
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
    
    def _load_players(self) -> List[Dict]:
        """Load player data from JSON."""
        if not self.players_file.exists():
            return []
        
        with open(self.players_file, 'r') as f:
            players_dict = json.load(f)
            # Convert from dict to list format
            return list(players_dict.values())
    
    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to URL-friendly slug."""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'-+', '-', text)
        text = re.sub(r' +', '-', text)
        return text
    
    def _generate_match_rows(self, player: Dict) -> str:
        """Generate match history rows for a player."""
        rows = []
        
        # Use history array which contains detailed match info
        history = player.get('history', [])
        for match in history:
            opponent = match['opponent']
            result = match['result_code']
            rating_change = match['rating_change']
            new_rating = match['rating_after']
            tournament_id = match.get('tournament', 'Unknown')
            round_num = match.get('round', 'N/A')
            
            # Determine CSS class and display text for result
            if result.upper() == 'W':
                result_class = 'win'
                result_text = 'Win'
            elif result.upper() == 'L':
                result_class = 'loss'
                result_text = 'Loss'
            else:
                result_class = 'draw'
                result_text = 'Draw'
            
            # Format rating change
            change_class = 'positive' if rating_change >= 0 else 'negative'
            change_text = f"+{rating_change:.1f}" if rating_change >= 0 else f"{rating_change:.1f}"
            
            rows.append(f"""
            <tr>
              <td>{tournament_id}</td>
              <td>{round_num}</td>
              <td>{opponent}</td>
              <td><span class="result {result_class}">{result_text}</span></td>
              <td><span class="rating-change {change_class}">{change_text}</span></td>
              <td>{new_rating:.1f}</td>
            </tr>
            """)
        
        return '\n'.join(rows)
    
    def _generate_html(self, players: List[Dict]) -> str:
        """Generate HTML for players detail page with collapsible sections."""
        sorted_players = sorted(players, key=lambda p: p['rating'], reverse=True)
        
        player_sections = []
        for player in sorted_players:
            slug = self._slugify(player['name'])
            matches_html = self._generate_match_rows(player)
            
            player_sections.append(f"""
    <details id="{slug}">
      <summary class="player-summary">
        <span class="player-name">{player['name']}</span>
        <span class="player-rating">{player['rating']}</span>
        <span class="player-matches">{len(player['matches'])} matches</span>
      </summary>
      <div class="player-details">
        <table class="match-history">
          <thead>
            <tr>
              <th>Tournament</th>
              <th>Round</th>
              <th>Opponent</th>
              <th>Result</th>
              <th>Rating Change</th>
              <th>New Rating</th>
            </tr>
          </thead>
          <tbody>
{matches_html}
          </tbody>
        </table>
      </div>
    </details>
            """)
        
        sections_html = '\n'.join(player_sections)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Player History - ELO Leaderboard</title>
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
            max-width: 900px;
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
        
        header a {{
            color: rgba(255, 255, 255, 0.9);
            text-decoration: none;
            font-size: 14px;
        }}
        
        header a:hover {{
            text-decoration: underline;
        }}
        
        .players {{
            padding: 20px;
        }}
        
        details {{
            margin-bottom: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        details[open] {{
            background: #f9f9f9;
        }}
        
        .player-summary {{
            padding: 15px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
            background: #f5f5f5;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        details[open] .player-summary {{
            background: #efefef;
            border-bottom: 1px solid #d0d0d0;
        }}
        
        .player-summary:hover {{
            background: #eee;
        }}
        
        .player-name {{
            font-size: 16px;
            flex: 1;
        }}
        
        .player-rating {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            margin: 0 15px;
            min-width: 60px;
            text-align: center;
        }}
        
        .player-matches {{
            font-size: 13px;
            color: #666;
            min-width: 100px;
            text-align: right;
        }}
        
        .player-details {{
            padding: 20px;
        }}
        
        .match-history {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        
        .match-history thead {{
            background: #f5f5f5;
        }}
        
        .match-history th {{
            padding: 10px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #ddd;
        }}
        
        .match-history td {{
            padding: 10px;
            border-bottom: 1px solid #eee;
        }}
        
        .match-history tr:hover {{
            background: #fafafa;
        }}
        
        .result {{
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 4px;
            text-align: center;
            min-width: 40px;
        }}
        
        .result.win {{
            color: #22863a;
            background: #f0ffe4;
        }}
        
        .result.loss {{
            color: #cb2431;
            background: #ffeef0;
        }}
        
        .result.draw {{
            color: #6f42c1;
            background: #f5f3ff;
        }}
        
        .rating-change {{
            font-weight: 600;
            text-align: center;
        }}
        
        .rating-change.positive {{
            color: #22863a;
        }}
        
        .rating-change.negative {{
            color: #cb2431;
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
            <h1>Player History</h1>
            <a href="leaderboard.html">← Back to Leaderboard</a>
        </header>
        
        <div class="players">
{sections_html}
        </div>
        
        <footer>
            Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
        </footer>
    </div>
    
    <script>
        // Auto-expand player if navigated via hash
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
        """Generate players detail page."""
        players = self._load_players()
        html_content = self._generate_html(players)
        output_path = self.output_dir.parent / 'players.html'
        output_path.write_text(html_content, encoding='utf-8')
        
        self.log(f"Generated players page: {output_path} ({len(players)} players)")
        self._flush_logs()


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / 'output'
    log_file = repo_root / 'log.txt'
    
    generator = PlayersGenerator(output_dir, log_file)
    generator.log("Starting player pages generation")
    generator.generate()
    generator.log("Player pages generation complete")


if __name__ == '__main__':
    main()
