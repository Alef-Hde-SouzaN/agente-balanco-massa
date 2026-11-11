import os
import sqlite3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DB = os.getenv('BM_DB', str(ROOT / 'data' / 'balanco.sqlite3'))

def conectar(path=None):
    con = sqlite3.connect(path or DB)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con

def inicializar(path=None):
    destino = path or DB
    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    with conectar(destino) as con:
        con.executescript((ROOT / 'sql/schema.sql').read_text())
        if not con.execute('SELECT 1 FROM ordens LIMIT 1').fetchone():
            con.executescript((ROOT / 'sql/seed.sql').read_text())

if __name__ == '__main__':
    inicializar()
    print(DB)
