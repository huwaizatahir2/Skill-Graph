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
    """Semantic search for employees based on skill relevance to query."""
    try:
        q_vec = embed_query(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")

    try:
        query = """
        MATCH (e:Employee)-[r:EMP_HAS_SKILL]->(s:Skill)
        RETURN e.name AS employee, e.role AS role, s.name AS skill,
               r.score AS level, s.embedding AS embedding
        """
        result = conn.execute(query)
        rows = []
        columns = result.get_column_names()
        for row in result:
            row_dict = dict(zip(columns, row))
            sim = cosine_sim(q_vec, row_dict["embedding"])
            if sim >= min_sim:
                rows.append({
                    "employee": row_dict["employee"],
                    "role": row_dict["role"],
                    "skill": row_dict["skill"],
                    "level": row_dict["level"],
                    "similarity": sim
                })

        rows.sort(key=lambda x: (x["similarity"], x["level"]), reverse=True)
        return rows[:10]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")