import sqlite3
from pathlib import Path
DB=Path(__file__).resolve().parent.parent/'logs'/'panel.db'
def init_db():
    DB.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB) as db:
        db.execute('CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,timestamp REAL,tool TEXT,event TEXT,detail TEXT)');db.commit()
