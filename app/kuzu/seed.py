import json
import kuzu
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os
import sys
import hashlib

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

def stable_id_from_text(prefix: str, text: str) -> str:
    """Generate a stable deterministic ID from text."""
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"

# Load JSON
data_path = Path(__file__).resolve().parents[1] / "sample_org_data.json"
with open(data_path) as f:
    data = json.load(f)

org = data["organization"]
print(f"[INFO] Creating Organization: {org['name']}")
conn.execute(f'MERGE (o:Organization {{org_id:"org1"}}) SET o.name="{org["name"]}"')

for ti, team in enumerate(org["teams"], 1):
    print(f"[INFO] Processing team {ti}/{len(org['teams'])}: {team['name']}")
    team_id = f"team{ti}"
    conn.execute(f'MERGE (t:Team {{team_id:"{team_id}"}}) SET t.name="{team["name"]}"')
    conn.execute(f'MATCH (o:Organization {{org_id:"org1"}}), (t:Team {{team_id:"{team_id}"}}) '
                 f'MERGE (o)-[:ORG_HAS_TEAM]->(t)')

    for ei, emp in enumerate(team["employees"], 1):
        print(f"   [Employee {ei}/{len(team['employees'])}] {emp['name']}")
        emp_id = emp["id"]
        name = emp["name"].replace("'", "\\'")
        role = emp["role"].replace("'", "\\'")
        conn.execute(f'MERGE (e:Employee {{emp_id:"{emp_id}"}}) SET e.name="{name}", e.role="{role}"')
        conn.execute(f'MATCH (t:Team {{team_id:"{team_id}"}}), (e:Employee {{emp_id:"{emp_id}"}}) '
                     f'MERGE (t)-[:TEAM_HAS_EMPLOYEE]->(e)')

        for si, skill in enumerate(emp["skills"], 1):
            skill_name = skill["skill"].replace("'", "\\'")
            cat = skill["category"].replace("'", "\\'")
            score = skill["score"]
            evidence_text = skill["evidence"].replace("'", "\\'")

            print(f"      [Skill {si}/{len(emp['skills'])}] {skill_name}")

            # Embed skill + evidence
            skill_vec = embed_text(skill_name, "skill", skill_name)
            evid_vec = embed_text(evidence_text, "evidence", evidence_text[:30] + "...")

            # Skill node + category
            conn.execute(f'MERGE (s:Skill {{skill_id:"{skill_name}"}}) '
                         f'SET s.name="{skill_name}", s.embedding={skill_vec}')
            conn.execute(f'MERGE (sc:SkillCategory {{category_id:"{cat}"}}) SET sc.name="{cat}"')
            conn.execute(f'MATCH (s:Skill {{skill_id:"{skill_name}"}}), (sc:SkillCategory {{name:"{cat}"}}) '
                         f'MERGE (s)-[:SKILL_IN_CATEGORY]->(sc)')
            conn.execute(f'MATCH (e:Employee {{emp_id:"{emp_id}"}}), (s:Skill {{skill_id:"{skill_name}"}}) '
                         f'MERGE (e)-[:EMP_HAS_SKILL {{score:{score}}}]->(s)')

            # Evidence node with stable hash ID
            evid_id = stable_id_from_text("evid", evidence_text)
            conn.execute(f'MERGE (ev:Evidence {{evidence_id:"{evid_id}"}}) '
                         f'SET ev.text="{evidence_text}", ev.embedding={evid_vec}')
            conn.execute(f'MATCH (ev:Evidence {{evidence_id:"{evid_id}"}}), (s:Skill {{skill_id:"{skill_name}"}}) '
                         f'MERGE (ev)-[:EVIDENCE_FOR]->(s)')