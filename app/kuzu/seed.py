import json
import kuzu
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os
import sys

# Load env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_FILE = Path(__file__).resolve().parents[2] / "data" / "kuzu_db.kuzu"
db = kuzu.Database(str(DB_FILE))
conn = kuzu.Connection(db)

def embed_text(text: str, kind: str, identifier: str):
    """Get OpenAI embedding with error handling + logging."""
    try:
        print(f"[Embedding {kind}] {identifier} ...", flush=True)
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return resp.data[0].embedding
    except Exception as e:
        print(f"[ERROR] Failed embedding {kind}={identifier}: {e}", file=sys.stderr)
        return [0.0] * 1536  # fallback vector

# Load JSON
data_path = Path(__file__).resolve().parents[1] / "sample_org_data.json"
with open(data_path) as f:
    data = json.load(f)

org = data["organization"]
print(f"[INFO] Creating Organization: {org['name']}")
conn.execute(f'CREATE (o:Organization {{org_id:"org1", name:"{org["name"]}"}})')

evidence_counter = 0
for ti, team in enumerate(org["teams"], 1):
    print(f"[INFO] Processing team {ti}/{len(org['teams'])}: {team['name']}")
    team_id = f"team{ti}"
    conn.execute(f'CREATE (t:Team {{team_id:"{team_id}", name:"{team["name"]}"}})')
    conn.execute(f'MATCH (o:Organization {{org_id:"org1"}}), (t:Team {{team_id:"{team_id}"}}) CREATE (o)-[:ORG_HAS_TEAM]->(t)')

    for ei, emp in enumerate(team["employees"], 1):
        print(f"   [Employee {ei}/{len(team['employees'])}] {emp['name']}")
        emp_id = emp["id"]
        name = emp["name"].replace("'", "\\'")
        role = emp["role"].replace("'", "\\'")
        conn.execute(f'CREATE (e:Employee {{emp_id:"{emp_id}", name:"{name}", role:"{role}"}})')
        conn.execute(f'MATCH (t:Team {{team_id:"{team_id}"}}), (e:Employee {{emp_id:"{emp_id}"}}) CREATE (t)-[:TEAM_HAS_EMPLOYEE]->(e)')

        for si, skill in enumerate(emp["skills"], 1):
            skill_name = skill["skill"].replace("'", "\\'")
            cat = skill["category"].replace("'", "\\'")
            score = skill["score"]
            evidence_text = skill["evidence"].replace("'", "\\'")

            print(f"      [Skill {si}/{len(emp['skills'])}] {skill_name}")

            # Embed skill + evidence
            skill_vec = embed_text(skill_name, "skill", skill_name)
            evid_vec = embed_text(evidence_text, "evidence", evidence_text[:30] + "...")

            conn.execute(f'MERGE (s:Skill {{skill_id:"{skill_name}", name:"{skill_name}", embedding:{skill_vec}}})')
            conn.execute(f'MERGE (sc:SkillCategory {{category_id:"{cat}", name:"{cat}"}})')
            conn.execute(f'MATCH (s:Skill {{skill_id:"{skill_name}"}}), (sc:SkillCategory {{name:"{cat}"}}) CREATE (s)-[:SKILL_IN_CATEGORY]->(sc)')
            conn.execute(f'MATCH (e:Employee {{emp_id:"{emp_id}"}}), (s:Skill {{skill_id:"{skill_name}"}}) CREATE (e)-[:EMP_HAS_SKILL {{score:{score}}}]->(s)')

            evidence_counter += 1
            evid_id = f"evid{evidence_counter}"
            conn.execute(f'CREATE (ev:Evidence {{evidence_id:"{evid_id}", text:"{evidence_text}", embedding:{evid_vec}}})')
            conn.execute(f'MATCH (ev:Evidence {{evidence_id:"{evid_id}"}}), (s:Skill {{skill_id:"{skill_name}"}}) CREATE (ev)-[:EVIDENCE_FOR]->(s)')