from fastapi import FastAPI, HTTPException
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import os
import kuzu
import numpy as np

# Load env vars
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Init FastAPI
app = FastAPI(
    title="Arbisoft Org Graph API",
    description="API exposing teams, employees, and skills from a sample org graph with semantic search.",
    version="0.2.0",
)

# Kùzu DB connection
DB_FILE = Path(__file__).resolve().parent.parent / "data" / "kuzu_db.kuzu"
db = kuzu.Database(str(DB_FILE))
conn = kuzu.Connection(db)


# --- Helpers ---
def embed_query(q: str):
    """Call OpenAI to embed query text."""
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=q
    )
    return resp.data[0].embedding


def cosine_sim(v1, v2):
    """Compute cosine similarity between two vectors."""
    v1, v2 = np.array(v1), np.array(v2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


# --- Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the Arbisoft Org Graph API with semantic search"}


@app.get("/search")
def semantic_search(q: str, min_sim: float = 0.5):
    """Semantic search for employees based on skill relevance to query.
    Returns both search results and graph JSON for visualization.
    """
    try:
        q_vec = embed_query(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")

    try:
        query = """
        MATCH (e:Employee)-[r:EMP_HAS_SKILL]->(s:Skill)<-[:EVIDENCE_FOR]-(ev:Evidence)
        RETURN e.emp_id AS emp_id, e.name AS employee, e.role AS role,
               s.skill_id AS skill_id, s.name AS skill,
               r.score AS level, s.embedding AS embedding,
               ev.evidence_id AS evidence_id, ev.text AS evidence
        """
        result = conn.execute(query)
        rows = []
        nodes, edges = [], []

        columns = result.get_column_names()
        for row in result:
            row_dict = dict(zip(columns, row))
            sim = cosine_sim(q_vec, row_dict["embedding"])
            if sim >= min_sim:
                record = {
                    "employee": row_dict["employee"],
                    "role": row_dict["role"],
                    "skill": row_dict["skill"],
                    "level": row_dict["level"],
                    "evidence": row_dict["evidence"],
                    "similarity": sim
                }
                rows.append(record)

                # --- Graph construction ---
                emp_id = row_dict["emp_id"]
                skill_id = row_dict["skill_id"]
                evidence_id = row_dict["evidence_id"]

                # Add nodes (deduplicate later on frontend or keep a set)
                nodes.extend([
                    {"id": emp_id, "label": row_dict["employee"], "type": "Employee"},
                    {"id": skill_id, "label": row_dict["skill"], "type": "Skill"},
                ])
                if evidence_id:
                    nodes.append({"id": evidence_id, "label": row_dict["evidence"], "type": "Evidence"})

                # Add edges
                edges.append({"from": emp_id, "to": skill_id, "label": "EMP_HAS_SKILL"})
                if evidence_id:
                    edges.append({"from": evidence_id, "to": skill_id, "label": "EVIDENCE_FOR"})

        # Sort search results as before
        rows.sort(key=lambda x: (x["similarity"], x["level"]), reverse=True)

        return {
            "results": rows[:10],  # your original results
            "graph": {
                "nodes": nodes,
                "edges": edges,
                "query": q  # include query string for frontend context
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")
