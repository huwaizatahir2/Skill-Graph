# Arbisoft Org Graph with FastAPI + KùzuDB

This project exposes a sample organizational knowledge graph via FastAPI
and persists the graph in [KùzuDB](https://kuzudb.com/).

## Setup (macOS)

```bash
# Create venv
python3 -m venv venv
source venv/bin/activate

# Install deps
pip install -r requirements.txt

# Initialize schema
python app/kuzu/bootstrap.py

# Seed from JSON
python app/kuzu/seed.py

# Run API
uvicorn app.main:app --reload
