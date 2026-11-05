"""Immutable, source-attributed local troubleshooting reports for class retrieval."""
import uuid, re, base64, hashlib
import pymupdf as fitz
from fastapi import APIRouter,HTTPException,Query,Request
from fastapi.responses import Response
from pydantic import BaseModel,Field
from . import store
from .workspace import read
router=APIRouter()
SHIP_TYPES={'CVN','CG','DDG','LCS','SSN','SSBN','SSGN','MCM','T-AKE','T-AO','T-AS','LCC','T-ESB','AS'}
with store.connect() as c:
    c.execute('CREATE TABLE IF NOT EXISTS troubleshooting(id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS problem_photos(id TEXT PRIMARY KEY,job_id TEXT NOT NULL,payload TEXT NOT NULL)')
def records(ship_class,query=''):
    if not ship_class or ship_class in SHIP_TYPES:return []
    with store.connect() as c:rows=[store.unseal(r[0]) for r in c.execute('SELECT payload FROM troubleshooting ORDER BY rowid DESC')]
    words=query.lower().split()
    return [r for r in rows if r['ship_class']==ship_class and all(w in (' '.join([r['equipment'],r['symptom'],r['actions_taken'],r['outcome']])).lower() for w in words)][:50]
def similar_records(ship_class,query,equipment_id=''):
    # Rank local evidence by shared terms; never invent a resolved outcome.
    ignored={'the','and','this','that','with','from','have','has','was','were','for','what','when','does','not','are','you','our','any','past','reports','problem'}
    terms=set(re.findall(r'[a-z0-9]+',query.lower()))-ignored
    terms={t for t in terms if len(t)>2 or any(c.isdigit() for c in t)}
    ranked=[]
    for row in records(ship_class):
        words=set(re.findall(r'[a-z0-9]+',' '.join(row.get(k,'') for k in ('equipment','symptom','actions_taken','outcome')).lower()))
        hits=len(terms & words)
        if terms and not hits:continue
        same_model=bool(equipment_id and row.get('equipment_id','').split('::')[-1]==equipment_id.split('::')[-1])
        ranked.append((hits+int(same_model),row))
    return [r for _,r in sorted(ranked,key=lambda x:x[0],reverse=True)][:10]

def photos(job_id):
    with store.connect() as c:rows=[store.unseal(r[0]) for r in c.execute('SELECT payload FROM problem_photos WHERE job_id=?',(job_id,))]
    return [{k:v for k,v in row.items() if k!='data'} for row in rows]

@router.post('/api/jobs/{job_id}/problem-photos')
async def save_photo(job_id:str,request:Request):
    draft=read(job_id)
    raw=bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw)>5*1024*1024:raise HTTPException(413,'Photo must be under 5 MB')
    data=bytes(raw)
    mime='image/png' if data.startswith(b'\x89PNG\r\n\x1a\n') else 'image/jpeg' if data.startswith(b'\xff\xd8\xff') else ''
    if not mime:raise HTTPException(422,'Use a PNG or JPEG photo')
    try:
        with fitz.open(stream=data,filetype='png' if mime=='image/png' else 'jpeg') as image:
            if image.page_count!=1:raise ValueError('Invalid image')
    except Exception as exc:raise HTTPException(422,'Photo could not be read') from exc
    ident=hashlib.sha256(job_id.encode()+data).hexdigest()
    photo={'id':ident,'job_id':job_id,'mime':mime,'recorded':store.now(),'ship_id':draft.get('ship_id',''),'equipment_id':draft.get('equipment_id',''),'url':'/api/problem-photos/'+ident,'data':base64.b64encode(data).decode()}
    with store.connect() as c:
        inserted=c.execute('INSERT OR IGNORE INTO problem_photos VALUES (?,?,?)',(ident,job_id,store.seal(photo))).rowcount
        if inserted:
            event={'id':str(uuid.uuid4()),'kind':'problem_photo_saved','job_id':job_id,'photo':photo,'time':store.now()}
            c.execute('INSERT INTO events(id,payload) VALUES (?,?)',(event['id'],store.seal(event)))
    return {k:v for k,v in photo.items() if k!='data'}

@router.get('/api/jobs/{job_id}/problem-photos')
def list_photos(job_id:str):
    read(job_id)
    return photos(job_id)

@router.get('/api/problem-photos/{photo_id}')
def get_photo(photo_id:str):
    with store.connect() as c:row=c.execute('SELECT payload FROM problem_photos WHERE id=?',(photo_id,)).fetchone()
    if not row:raise HTTPException(404,'Photo not found')
    photo=store.unseal(row[0])
    return Response(base64.b64decode(photo['data']),media_type=photo['mime'],headers={'Cache-Control':'no-store'})

class Publish(BaseModel):
    draft_version:int=Field(ge=0)
@router.get('/api/troubleshooting')
def history(ship_class:str=Query(max_length=120),q:str=Query(default='',max_length=3000),similar:bool=False,equipment_id:str=Query(default='',max_length=200)):
    return similar_records(ship_class,q,equipment_id) if similar else records(ship_class,q)
@router.post('/api/jobs/{job_id}/troubleshooting')
def publish(job_id:str,body:Publish):
    draft=read(job_id)
    if draft['version']!=body.draft_version:raise HTTPException(409,'Draft changed; reload before saving a troubleshooting record')
    required=['ship_name','hull_number','ship_class','equipment','symptom','actions_taken','outcome']
    missing=[k for k in required if not draft[k].strip()]
    if missing:raise HTTPException(422,'Complete these fields: '+', '.join(missing))
    if draft['ship_class'] in SHIP_TYPES:raise HTTPException(422,'Choose a named ship class (for example Arleigh Burke), not only a type such as DDG')
    job=next(j for j in store.jobs() if j['id']==job_id)
    progress=store.session(job_id)
    record={**{k:draft[k] for k in required},'id':str(uuid.uuid4()),'job_id':job_id,'ship_id':draft.get('ship_id',''),'equipment_id':draft.get('equipment_id',''),'technician':draft['owner'],'location':draft['location'],'notes':draft['notes'],'recorded':store.now(),'draft_version':draft['version'],'procedure':progress,'evidence':store.logs(job_id),'problem_photos':photos(job_id),'job_status':job['status'],'status':'Technician report — unverified','scope':'Class match only; verify hull, equipment configuration and procedure applicability.'}
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        current=c.execute('SELECT payload FROM drafts WHERE job_id=?',(job_id,)).fetchone()
        if not current or store.unseal(current[0])['version']!=body.draft_version:raise HTTPException(409,'Draft changed; reload before saving')
        # A retried save of the same draft returns the same immutable report.
        for row in c.execute('SELECT payload FROM troubleshooting'):
            previous=store.unseal(row[0])
            if previous['job_id']==job_id and previous['draft_version']==draft['version']:return previous
        c.execute('INSERT INTO troubleshooting VALUES (?,?)',(record['id'],store.seal(record)))
        event={'id':str(uuid.uuid4()),'kind':'troubleshooting_recorded','time':store.now(),'record':record}
        c.execute('INSERT INTO events(id,payload) VALUES (?,?)',(event['id'],store.seal(event)))
    return record
