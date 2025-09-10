from fastapi import FastAPI, HTTPException
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import os
import kuzu

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


# --- Helper: OpenAI embedding ---
def embed_query(q: str):
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=q
    )
    return resp.data[0].embedding


# --- Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the Arbisoft Org Graph API with semantic search"}


@app.get("/search")
def semantic_search(q: str, min_sim: float = 0.5):
    """Semantic search for employees based on skill relevance to query."""
    q_vec = embed_query(q)

    query = """
    MATCH (e:Employee)-[r:EMP_HAS_SKILL]->(s:Skill)
    WITH e, s, r, cosinesim(s.embedding, $q_vec) AS sim
    WHERE sim >= $min_sim
    RETURN e.name AS employee, e.role AS role, s.name AS skill, r.score AS level, sim
    ORDER BY sim DESC, level DESC
    LIMIT 10
    """

    result = conn.execute(query, {"q_vec": q_vec, "min_sim": min_sim})
    return [dict(row) for row in result]
