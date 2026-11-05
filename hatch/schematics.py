"""Class-scoped schematic originals, kept encrypted in the local database."""
import base64, hashlib, json, uuid
from pathlib import Path
from urllib.parse import unquote, quote
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import Response
from . import store
router=APIRouter()
CATALOG=json.loads((Path(__file__).resolve().parents[1]/'config/ship_classes.json').read_text())
KNOWN={name for names in CATALOG['groups'].values() for name in names}
with store.connect() as c:
    c.execute('CREATE TABLE IF NOT EXISTS schematics(id TEXT PRIMARY KEY, ship_class TEXT NOT NULL, payload TEXT NOT NULL)')
    c.execute('CREATE INDEX IF NOT EXISTS schematics_class ON schematics(ship_class)')

def validate_class(value):
    if value not in KNOWN and not (value.startswith('Custom: ') and 1<=len(value[8:].strip())<=100):
        raise HTTPException(422,'Select a listed class or enter a custom class')

@router.get('/api/ship-classes')
def classes():
    with store.connect() as c:
        custom=[r[0] for r in c.execute("SELECT DISTINCT ship_class FROM schematics WHERE ship_class LIKE 'Custom: %' ORDER BY ship_class")]
    return {**CATALOG,'custom':custom}

@router.get('/api/schematics')
def listing(ship_class:str=Query(max_length=120)):
    validate_class(ship_class)
    with store.connect() as c:
        rows=c.execute('SELECT payload FROM schematics WHERE ship_class=? ORDER BY rowid DESC',(ship_class,)).fetchall()
    return [{k:v for k,v in store.unseal(r[0]).items() if k!='content'} for r in rows]

@router.post('/api/schematics')
async def upload(request:Request,ship_class:str=Query(max_length=120)):
    validate_class(ship_class)
    chunks=[];size=0
    async for chunk in request.stream():
        size+=len(chunk)
        if size>20*1024*1024:raise HTTPException(413,'Maximum schematic size is 20 MB')
        chunks.append(chunk)
    content=b''.join(chunks)
    if content.startswith(b'%PDF-'):mime='application/pdf'
    elif content.startswith(b'\x89PNG\r\n\x1a\n'):mime='image/png'
    elif content.startswith(b'\xff\xd8\xff'):mime='image/jpeg'
    else:raise HTTPException(415,'Use a PDF, PNG or JPEG schematic')
    name=unquote(request.headers.get('X-Filename','schematic')).replace('\\','/').split('/')[-1][:180]
    value={'id':str(uuid.uuid4()),'ship_class':ship_class,'name':name,'mime':mime,'size':size,'created':store.now(),'sha256':hashlib.sha256(content).hexdigest(),'content':base64.b64encode(content).decode()}
    with store.connect() as c:
        c.execute('INSERT INTO schematics VALUES (?,?,?)',(value['id'],ship_class,store.seal(value)))
    return {k:v for k,v in value.items() if k!='content'}

@router.get('/api/schematics/{schematic_id}/download')
def download(schematic_id:str):
    with store.connect() as c:row=c.execute('SELECT payload FROM schematics WHERE id=?',(schematic_id,)).fetchone()
    if not row:raise HTTPException(404,'Schematic not found')
    value=store.unseal(row[0])
    return Response(base64.b64decode(value['content']),media_type=value['mime'],headers={'Content-Disposition':"attachment; filename*=UTF-8''"+quote(value['name'],safe=''),'X-Content-Type-Options':'nosniff'})
