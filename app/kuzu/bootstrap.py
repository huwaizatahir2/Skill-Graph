import kuzu
from pathlib import Path

DB_FILE = Path(__file__).resolve().parents[2] / "data" / "kuzu_db.kuzu"
DB_FILE.parent.mkdir(parents=True, exist_ok=True)

db = kuzu.Database(str(DB_FILE))
conn = kuzu.Connection(db)

schema_path = Path(__file__).parent / "schema.cypher"
with open(schema_path) as f:
    schema = f.read()

for stmt in schema.strip().split(";"):
    stmt = stmt.strip()
    if stmt:
        try:
            conn.execute(stmt)
            print(f"Executed: {stmt}")
        except Exception as e:
            print(f"Skipping (maybe exists): {stmt} -> {e}")