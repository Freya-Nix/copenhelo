.PHONY: help install run-parse run-elo run-leaderboard run-players run-tournaments run recalculate

VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python

help:
	@echo "Commands:"
	@echo "  make install       - Setup virtual environment"
	@echo "  make run           - Run full pipeline"
	@echo "  make run-parse     - Parse tournaments only"
	@echo "  make run-elo       - Calculate ratings only"
	@echo "  make recalculate   - Clear data and recalculate from scratch"

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
