# Project setup

## Enviroment

**Python Version:** Python >= 3.9

## Project setup

Run the following commands in your terminal:

```bash
git clone https://github.com/Avcuongy/stock-elt.git

cd stock-elt

python -m venv .venv

.venv\Scripts\Activate.ps1

pip install -r requirements.txt

pip install -e .

python scripts/config.py

# Data source
python scripts/backend/extract.py
python scripts/backend/transform.py
python scripts/backend/load.py

# ETL
python scripts/elt.py
```
