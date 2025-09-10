from fastapi import FastAPI, HTTPException
import json
from pathlib import Path

app = FastAPI(
    title="Arbisoft Org Graph API",
    description="API exposing teams, employees, and skills from a sample org graph.",
    version="0.1.0",
)

DATA_PATH = Path(__file__).resolve().parent / "sample_org_data.json"
with open(DATA_PATH) as f:
    _data = json.load(f)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Arbisoft Org Graph API"}

@app.get("/teams")
def get_teams():
    return _data.get("organization", {}).get("teams", [])

@app.get("/teams/{team_slug}")
def get_team(team_slug: str):
    for team in _data.get("organization", {}).get("teams", []):
        slug = team.get("name", "").lower().replace(" ", "-")
        if slug == team_slug.lower():
            return team
    raise HTTPException(status_code=404, detail="Team not found")

@app.get("/employees")
def get_employees():
    employees = []
    for team in _data.get("organization", {}).get("teams", []):
        employees.extend(team.get("employees", []))
    return employees

@app.get("/employees/{emp_id}")
def get_employee(emp_id: str):
    for team in _data.get("organization", {}).get("teams", []):
        for emp in team.get("employees", []):
            if emp.get("id") == emp_id:
                return emp
    raise HTTPException(status_code=404, detail="Employee not found")
