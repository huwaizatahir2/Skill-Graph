# Arbisoft Org Graph FastAPI Project

This repository contains a minimal FastAPI application that exposes a simple
API over an organizational knowledge graph. The graph data is stored in
`sample_org_data.json` and loaded at startup. Each endpoint returns JSON
objects suitable for consumption by front‑end clients or other services.

## Installation

1. **Clone the repository** or download the zip archive.
2. **Install dependencies** using pip:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application** with Uvicorn:

   ```bash
   uvicorn app.main:app --reload
   ```

   The `--reload` flag enables hot reloading during development.

4. **Access the API**. Once the server is running, open your browser to
   `http://localhost:8000` to see the welcome message. The interactive API
   documentation is available at `http://localhost:8000/docs` (Swagger UI)
   and `http://localhost:8000/redoc` (Redoc).

## API Endpoints

- `GET /` – Welcome message.
- `GET /teams` – List all teams.
- `GET /teams/{team_slug}` – Retrieve a team by slug (lowercase name with hyphens).
- `GET /employees` – List all employees across teams.
- `GET /employees/{emp_id}` – Retrieve a specific employee by ID.

## Data File

The data for this project is stored in `app/sample_org_data.json`. It
contains the nested structure of teams, employees, skills, and evidence
captured from a competency assessment. You can modify this file and
restart the server to use updated data.

## Project Structure

- `app/` – Contains the FastAPI application.
  - `main.py` – The FastAPI app and route definitions.
  - `sample_org_data.json` – Example organizational data used by the API.
- `requirements.txt` – Python dependencies.
- `README.md` – This file.