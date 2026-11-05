import json, os, sqlite3, uuid
from pathlib import Path
from datetime import datetime, timezone
from cryptography.fernet import Fernet
ROOT = Path(os.environ.get('HATCH_DATA', 'data'))
ROOT.mkdir(parents=True, exist_ok=True)
KEY = ROOT / 'device.key'
if not KEY.exists():
    fd = os.open(KEY, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as f: f.write(Fernet.generate_key())
CIPHER = Fernet(KEY.read_bytes())
def now(): return datetime.now(timezone.utc).isoformat()
class ClosingConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try: return super().__exit__(*args)
        finally: self.close()

def connect():
    c = sqlite3.connect(ROOT / 'hatch.db', timeout=30, factory=ClosingConnection)
    c.row_factory = sqlite3.Row
    return c
def seal(value): return CIPHER.encrypt(json.dumps(value).encode()).decode()
def unseal(value): return json.loads(CIPHER.decrypt(value.encode()))
def init():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, payload TEXT NOT NULL, ship INTEGER DEFAULT 0, shore INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS receipts(target TEXT, event_id TEXT, payload TEXT, PRIMARY KEY(target,event_id));
        CREATE VIRTUAL TABLE IF NOT EXISTS corpus USING fts5(source UNINDEXED,title,body);
        CREATE TABLE IF NOT EXISTS imports(path TEXT PRIMARY KEY, imported TEXT, documents INTEGER);
        ''')
        if not c.execute('SELECT count(*) FROM jobs').fetchone()[0]:
            for n, title in enumerate(['Investigate reported lighting discrepancy','Scheduled equipment record review','Reconcile consumables before next maintenance window'],1):
                job={'id':f'WO-{n:03}', 'title':title,'asset':'MH-60R / DEMO 701','status':'Open','priority':['High','Routine','Routine'][n-1], 'version':1}
                c.execute('INSERT INTO jobs VALUES (?,?)',(job['id'],seal(job)))
def jobs():
    with connect() as c: return [unseal(r['payload']) for r in c.execute('SELECT * FROM jobs')]
def search(query):
    import re
    words = re.findall(r'[a-zA-Z0-9]{3,}',query)[:12]
    if not words: return []
    expression = ' OR '.join('"'+w+'"' for w in words)
    with connect() as c:
        rows=c.execute('SELECT rowid,source,title,body FROM corpus WHERE corpus MATCH ? ORDER BY rank LIMIT 5',(expression,)).fetchall()
    return [dict(r) for r in rows]
def complete(job_id,version,meter,note,photo=None):
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT payload FROM jobs WHERE id=?',(job_id,)).fetchone()
        if not row: raise ValueError('Unknown work order')
        job=unseal(row[0])
        if job['version']!=version or job['status']!='Open': raise ValueError('Record changed or already completed; refresh before retrying')
        job.update(status='Completed locally',version=version+1,meter=meter,note=note,completed=now(),photo=photo)
        event={'id':str(uuid.uuid4()),'kind':'work_order_completed','time':now(),'job':job,'base_version':version}
        c.execute('UPDATE jobs SET payload=? WHERE id=?',(seal(job),job_id))
        c.execute('INSERT INTO events(id,payload) VALUES (?,?)',(event['id'],seal(event)))
    return event['id']
def sync(target):
    if target not in ('ship','shore'): raise ValueError('Invalid target')
    # Separate durable receipts simulate receiver idempotency. These are not remote servers.
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        rows=c.execute('SELECT * FROM events WHERE '+target+'=0'+(' AND ship=1' if target=='shore' else '')).fetchall()
        for row in rows:
            c.execute('INSERT OR IGNORE INTO receipts VALUES (?,?,?)',(target,row['id'],row['payload']))
            c.execute('UPDATE events SET '+target+'=1 WHERE id=?',(row['id'],))
    return len(rows)

def procedure_schema():
    with connect() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS sessions(job_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS lessons(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS logs(id TEXT PRIMARY KEY, job_id TEXT NOT NULL, payload TEXT NOT NULL);''')

def procedure(source):
    from .demo_procedures import structured
    demo=structured(source)
    if demo:return demo
    import hashlib
    with connect() as c:
        rows=c.execute('SELECT title,body FROM corpus WHERE source=? ORDER BY rowid',(source,)).fetchall()
    if not rows: raise ValueError('Source module not found')
    # Imported windows have stride 2400 and overlap 400; recover exact original text.
    text=rows[0]['body']+''.join(r['body'][400:] for r in rows[1:])
    return {'source':source,'title':rows[0]['title'],'revision_hash':hashlib.sha256(text.encode()).hexdigest(),'sections':[text[i:i+2400] for i in range(0,len(text),2400)]}

def session(job_id):
    if job_id not in [j['id'] for j in jobs()]: raise ValueError('Unknown work order')
    with connect() as c:
        row=c.execute('SELECT payload FROM sessions WHERE job_id=?',(job_id,)).fetchone()
    return unseal(row[0]) if row else None

def save_session(job_id,source,revision_hash,checked,note,version):
    p=procedure(source)
    if p['revision_hash']!=revision_hash: raise ValueError('Source changed; reload procedure')
    if any(i<0 or i>=len(p['sections']) for i in checked): raise ValueError('Invalid section')
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        if not c.execute('SELECT 1 FROM jobs WHERE id=?',(job_id,)).fetchone(): raise ValueError('Unknown work order')
        old=c.execute('SELECT payload FROM sessions WHERE job_id=?',(job_id,)).fetchone()
        if (unseal(old[0])['version'] if old else 0)!=version: raise ValueError('Progress changed; reload before saving')
        value={'job_id':job_id,'source':source,'revision_hash':revision_hash,'checked':sorted(set(checked)),'note':note,'version':version+1,'updated':now()}
        c.execute('INSERT OR REPLACE INTO sessions VALUES (?,?)',(job_id,seal(value)))
        event={'id':str(uuid.uuid4()),'kind':'procedure_progress','time':now(),'session':value}
        c.execute('INSERT INTO events(id,payload) VALUES (?,?)',(event['id'],seal(event)))
    return value

def lessons(source):
    with connect() as c: values=[unseal(r[0]) for r in c.execute('SELECT payload FROM lessons')]
    return [v for v in values if v['source']==source]

def add_lesson(job_id,source,text,step=None,kind='observation',sailor=None):
    session(job_id);module=procedure(source)
    if step is not None and (step<0 or step>=len(module['sections'])):raise ValueError('Invalid lesson step')
    value={'id':str(uuid.uuid4()),'job_id':job_id,'source':source,'text':text,'recorded':now(),'status':'Technician observation — unverified','step':step,'kind':kind,'sailor':sailor,'revision_hash':module['revision_hash']}
    with connect() as c:
        c.execute('INSERT INTO lessons VALUES (?,?)',(value['id'],seal(value)))
        event={'id':str(uuid.uuid4()),'kind':'lesson_recorded','time':now(),'lesson':value}
        c.execute('INSERT INTO events(id,payload) VALUES (?,?)',(event['id'],seal(event)))
    return value

def save_log(job_id,name,mime,content):
    import base64,hashlib
    session(job_id)
    from .workspace import read
    from .demo_watch import schedules
    draft=read(job_id)
    context={key:draft.get(key,'') for key in ('ship_id','equipment_id','owner')}
    context['owner']=context['owner'] or schedules().get(job_id,{}).get('assignee','')
    value={'id':str(uuid.uuid4()),'job_id':job_id,'name':name,'mime':mime,'content':base64.b64encode(content).decode(),'sha256':hashlib.sha256(content).hexdigest(),'created':now(),'status':'Stored original · OCR pending','maintenance_context':context}
    with connect() as c:
        c.execute('INSERT INTO logs VALUES (?,?,?)',(value['id'],job_id,seal(value)))
        event={'id':str(uuid.uuid4()),'kind':'handwritten_log_uploaded','time':now(),'log':value}
        c.execute('INSERT INTO events(id,payload) VALUES (?,?)',(event['id'],seal(event)))
    return {k:v for k,v in value.items() if k!='content'}

def logs(job_id):
    with connect() as c: values=[unseal(r[0]) for r in c.execute('SELECT payload FROM logs WHERE job_id=?',(job_id,))]
    return [{k:v for k,v in x.items() if k!='content'} for x in values]

def procedure_catalog(query='',offset=0,limit=24):
    """Browse user uploads only; seeded/imported corpus is not an upload library."""
    items=[]
    with connect() as c:
        for table in ('equipment_documents','schematics'):
            for row in c.execute('SELECT payload FROM '+table):
                d=unseal(row[0])
                equipment=table=='equipment_documents'
                items.append({'id':d['id'],'title':d['name'],'ship_class':d['ship_class'],
                              'equipment_name':d.get('equipment_name','Class schematic'),
                              'revision':d.get('revision','Not specified'),
                              'page_count':d.get('page_count'),
                              'kind':'equipment' if equipment else 'schematic',
                              'download_url':('/api/equipment-documents/'+d['id']+'/file') if equipment else '/api/schematics/'+d['id']+'/download'})
    terms=query.lower().split()[:12]
    items=[d for d in items if all(t in (' '.join(str(v) for v in d.values())).lower() for t in terms)]
    items.sort(key=lambda d:(d['title'].lower(),d['id']))
    return {'items':items[offset:offset+limit],'total':len(items),'offset':offset,'limit':limit}
