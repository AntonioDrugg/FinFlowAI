import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / ".tmp" / "finflowai.db"
SPACE   = "ge-souza-tax"

con = sqlite3.connect(DB_PATH)
cur = con.cursor()
cur.execute("UPDATE clients SET space = ? WHERE space = '' OR space IS NULL", (SPACE,))
n = cur.rowcount
con.commit()
con.close()
print("Backfilled", n, "client row(s) -> space:", SPACE)
