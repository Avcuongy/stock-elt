# Phony targets
.PHONY: help etl backend

# Python interpreter (venv)
PYTHON ?= .venv/scripts/python.exe

# Rules
config:
	$(PYTHON) scripts/config.py

backend:
	$(PYTHON) scripts/backend/extract.py
	$(PYTHON) scripts/backend/transform.py
	$(PYTHON) scripts/backend/load.py

## Display available targets
help:
	@echo "Targets:"
	@echo "  help       - Display this help message"
	@echo "  config     - Set up configuration"