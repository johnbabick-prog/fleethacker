"""Local-only ingestion; source material is never copied into tracked files."""
import sys, hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hatch import store
store.init()
root=Path(sys.argv[1]).resolve()
files=sorted(root.glob('*.txt'))
if not files: raise SystemExit('No .txt modules found')
with store.connect() as c:
    c.execute('DELETE FROM corpus')
    for path in files:
        text=path.read_text(errors='replace')
        title=text.split('DISTRIBUTION STATEMENT')[0][:250]
        # Preserve source identifiers and full text, including source markings.
        for start in range(0,len(text),2400):
            c.execute('INSERT INTO corpus(source,title,body) VALUES (?,?,?)',(path.name,title,text[start:start+2800]))
    c.execute('INSERT OR REPLACE INTO imports VALUES (?,?,?)',(str(root),store.now(),len(files)))
print(f'Indexed {len(files)} local modules')
