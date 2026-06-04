.PHONY: help install run-parse run-elo run-standings-elo run-leaderboard run-players run-tournaments run recalculate final_standings_reset

VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
FSV := final_standings_version

help:
	@echo "Commands:"
	@echo "  make install            - Setup virtual environment"
	@echo "  make run                - Run full pipeline"
	@echo "  make run-parse          - Parse tournaments only"
	@echo "  make run-elo            - Calculate ratings only"
	@echo "  make run-standings-elo  - Calculate ELO from final standings"
	@echo "  make recalculate        - Clear data and recalculate from scratch"
	@echo ""
	@echo "Final Standings Version:"
	@echo "  make final_standings_reset - Full pipeline (reset + extract + calculate + generate)"

install: $(VENV_DIR)
	@echo "✓ Virtual environment ready"

$(VENV_DIR):
	python3 -m venv $(VENV_DIR)
	$(PYTHON) -m pip install -q -e .
	@echo "✓ Dependencies installed"

run-parse: $(VENV_DIR)
	@echo "Parsing tournaments from input..."
	$(PYTHON) scripts/parse_tournaments.py

run-elo: $(VENV_DIR)
	@echo "Running ELO calculator..."
	$(PYTHON) scripts/elo_calculator.py

run-standings-elo: $(VENV_DIR)
	@echo "Calculating ELO from final standings..."
	$(PYTHON) scripts/elo_from_standings.py

run-leaderboard: $(VENV_DIR)
	@echo "Generating leaderboard..."
	$(PYTHON) scripts/leaderboard_generator.py

run-players: $(VENV_DIR)
	@echo "Generating player pages..."
	$(PYTHON) scripts/players_generator.py

run-tournaments: $(VENV_DIR)
	@echo "Generating tournament pages..."
	$(PYTHON) scripts/tournaments_generator.py

run: run-parse run-elo run-leaderboard run-players run-tournaments
	@echo "✓ All tasks complete"

recalculate: $(VENV_DIR)
	@echo "Recalculating ratings from scratch..."
	$(PYTHON) scripts/recalculate_history.py

final_standings_reset: $(VENV_DIR)
	@echo "Resetting output files..."
	@echo '{}' > $(FSV)/output/players.json
	@echo '{}' > $(FSV)/output/tournaments.json
	@echo "Extracting tournaments from HTML..."
	cd $(FSV) && $(PYTHON) extract_standings.py ../input/*.htm 2>/dev/null || true
	@echo "Calculating ELO ratings..."
	cd $(FSV) && $(PYTHON) elo_calculator.py $(if $(INCLUDE_DUMMY),--include-dummy,)
	@echo "Generating leaderboard..."
	cd $(FSV) && $(PYTHON) leaderboard_generator.py
	@echo "✓ Pipeline complete: dummy.html"
