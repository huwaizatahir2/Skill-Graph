from fastapi import FastAPI, HTTPException
import json
from pathlib import Path


app = FastAPI(
    title="Arbisoft Org Graph API",
    description="A simple API exposing teams, employees, and skills from a sample organizational knowledge graph.",
    version="0.1.0",
)

# Load the JSON data once at startup. The JSON file is stored in the same
# directory as this module. If you update the data, restart the application
# to reflect the changes.
DATA_PATH = Path(__file__).resolve().parent / "sample_org_data.json"
with open(DATA_PATH) as f:
    _data = json.load(f)


@app.get("/")
def read_root() -> dict:
    """Root endpoint returns a welcome message."""
    return {"message": "Welcome to the Arbisoft Org Graph API"}


@app.get("/teams")
def get_teams() -> list:
    """Return the list of teams in the organization."""
    return _data.get("organization", {}).get("teams", [])


@app.get("/teams/{team_slug}")
def get_team(team_slug: str) -> dict:
    """Return a single team by slug (lowercase, hyphen-separated name).

    For example, to retrieve the "Platform Engineering" team, use the slug
    `platform-engineering`.
    """
    for team in _data.get("organization", {}).get("teams", []):
        slug = team.get("name", "").lower().replace(" ", "-")
        if slug == team_slug.lower():
            return team
    raise HTTPException(status_code=404, detail="Team not found")


@app.get("/employees")
def get_employees() -> list:
    """Return a flat list of all employees in the organization."""
    employees = []
    for team in _data.get("organization", {}).get("teams", []):
        employees.extend(team.get("employees", []))
    return employees


@app.get("/employees/{emp_id}")
def get_employee(emp_id: str) -> dict:
    """Return a single employee by their ID."""
    for team in _data.get("organization", {}).get("teams", []):
        for emp in team.get("employees", []):
            if emp.get("id") == emp_id:
                return emp
    raise HTTPException(status_code=404, detail="Employee not found")