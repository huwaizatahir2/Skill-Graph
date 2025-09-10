import json
import kuzu
from pathlib import Path

DB_FILE = Path(__file__).resolve().parents[2] / "data" / "kuzu_db.kuzu"
db = kuzu.Database(str(DB_FILE))
conn = kuzu.Connection(db)

data_path = Path(__file__).resolve().parents[1] / "sample_org_data.json"
with open(data_path) as f:
    data = json.load(f)

org = data["organization"]
conn.execute(f'CREATE (o:Organization {{org_id:"org1", name:"{org["name"]}"}})')

for ti, team in enumerate(org["teams"], 1):
    team_id = f"team{ti}"
    conn.execute(f'CREATE (t:Team {{team_id:"{team_id}", name:"{team["name"]}"}})')
    conn.execute(f'MATCH (o:Organization {{org_id:"org1"}}), (t:Team {{team_id:"{team_id}"}}) '
                 f'CREATE (o)-[:ORG_HAS_TEAM]->(t)')

    for ei, emp in enumerate(team["employees"], 1):
        emp_id = emp["id"]
        name = emp["name"].replace("'", "\\'")
        role = emp["role"].replace("'", "\\'")
        conn.execute(f'CREATE (e:Employee {{emp_id:"{emp_id}", name:"{name}", role:"{role}"}})')
        conn.execute(f'MATCH (t:Team {{team_id:"{team_id}"}}), (e:Employee {{emp_id:"{emp_id}"}}) '
                     f'CREATE (t)-[:TEAM_HAS_EMPLOYEE]->(e)')

        for si, skill in enumerate(emp["skills"], 1):
            skill_id = f"{emp_id}_skill{si}"
            skill_name = skill["skill"].replace("'", "\\'")
            category = skill["category"].replace("'", "\\'")
            score = skill["score"]
            evidence = skill["evidence"].replace("'", "\\'")
            conn.execute(f'MERGE (sc:SkillCategory {{category_id:"{category}", name:"{category}"}})')
            conn.execute(f'MERGE (s:Skill {{skill_id:"{skill_name}", name:"{skill_name}"}})')
            conn.execute(f'MATCH (e:Employee {{emp_id:"{emp_id}"}}), (s:Skill {{skill_id:"{skill_name}"}}) '
                         f'CREATE (e)-[:EMP_HAS_SKILL {{score:{score}, evidence:"{evidence}"}}]->(s)')
            conn.execute(f'MATCH (s:Skill {{skill_id:"{skill_name}"}}), (sc:SkillCategory {{name:"{category}"}}) '
                         f'CREATE (s)-[:SKILL_IN_CATEGORY]->(sc)')