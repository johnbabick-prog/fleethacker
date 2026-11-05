"""Draft watch context, saved separately from maintenance certification."""
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from . import store
from . import demo_watch
from .experience import PROFILES
router=APIRouter()
with store.connect() as c:c.execute('CREATE TABLE IF NOT EXISTS drafts(job_id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
def read(job_id):
    if not any(j['id']==job_id for j in store.jobs()):raise HTTPException(404,'Unknown work order')
    with store.connect() as c:r=c.execute('SELECT payload FROM drafts WHERE job_id=?',(job_id,)).fetchone()
    return {'equipment_id':'','ship_id':'','ship_name':'','hull_number':'','equipment':'','symptom':'','actions_taken':'','outcome':'',**store.unseal(r[0])} if r else {'equipment_id':'','ship_id':'','ship_name':'','hull_number':'','equipment':'','symptom':'','actions_taken':'','outcome':'','version':0,'owner':'','location':'','ship_class':'','notes':'','blockers':'','next_watch':''}
class Draft(BaseModel):
    equipment_id:str=Field(default="",max_length=200)
    ship_id:str=Field(default="",max_length=120)
    ship_name:str=Field(default='',max_length=100)
    hull_number:str=Field(default='',max_length=30)
    equipment:str=Field(default='',max_length=200)
    symptom:str=Field(default='',max_length=3000)
    actions_taken:str=Field(default='',max_length=5000)
    outcome:str=Field(default='',max_length=3000)
    version:int=Field(ge=0)
    owner:str=Field(default='',max_length=100)
    location:str=Field(default='',max_length=200)
    ship_class:str=Field(default='',max_length=120)
    notes:str=Field(default='',max_length=5000)
    blockers:str=Field(default='',max_length=2000)
    next_watch:str=Field(default='',max_length=2000)
@router.get('/api/watch')
def watch():
    schedules=demo_watch.schedules()
    return [{'job':j,'draft':read(j['id']),'schedule':schedules.get(j['id'])} for j in store.jobs()]

@router.get('/api/watch-options')
def watch_options():
    from datetime import date,timedelta
    today=date.today();start=today-timedelta(days=today.weekday())
    return {'work_centers':demo_watch.CENTERS,'sailors':demo_watch.SAILORS,'experience_profiles':PROFILES,'today':today.isoformat(),'week_start':start.isoformat(),'week_end':(start+timedelta(days=6)).isoformat()}
@router.get('/api/jobs/{job_id}/draft')
def get_draft(job_id:str):return read(job_id)
@router.post('/api/jobs/{job_id}/draft')
def save_draft(job_id:str,body:Draft):
    import uuid
    from .ships import BY_ID
    if body.ship_id:
        ship=BY_ID.get(body.ship_id)
        if not ship:raise HTTPException(422,'Select a ship from the directory')
        body.ship_name=ship['name'];body.hull_number=ship['hull_number'];body.ship_class=ship['ship_class']
    if body.equipment_id:
        from .equipment import resolve
        item=resolve(body.ship_id,body.equipment_id)
        body.equipment=item['name']
    read(job_id)
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        r=c.execute('SELECT payload FROM drafts WHERE job_id=?',(job_id,)).fetchone()
        version=store.unseal(r[0])['version'] if r else 0
        if version!=body.version:raise HTTPException(409,'Another reviewer changed this draft. Copy your notes before reloading.')
        value={**body.model_dump(),'version':version+1,'updated':store.now()}
        c.execute('INSERT OR REPLACE INTO drafts VALUES (?,?)',(job_id,store.seal(value)))
        event={'id':str(uuid.uuid4()),'kind':'watch_draft_saved','job_id':job_id,'draft':value,'time':store.now()}
        c.execute('INSERT INTO events(id,payload) VALUES (?,?)',(event['id'],store.seal(event)))
    return value

@router.get('/api/jobs/{job_id}/greeting')
def job_greeting(job_id:str):
    from .experience import greeting
    draft=read(job_id)
    job=next(j for j in store.jobs() if j['id']==job_id)
    sailor=draft['owner'] or demo_watch.schedules().get(job_id,{}).get('assignee','')
    resuming=bool(store.session(job_id) or draft['notes'] or draft['blockers'] or draft['next_watch'])
    return {'job_id':job_id,'sailor':sailor,'text':greeting(sailor,job['title'],resuming),'mode':'Profile-based welcome · demo experience'}

@router.get('/api/ships/{ship_id}/maintenance-sailors')
def maintenance_sailors(ship_id:str):
    from .ships import BY_ID
    if ship_id not in BY_ID:raise HTTPException(404,'Unknown ship')
    rows=watch();names={}
    for row in rows:
        if row['draft'].get('ship_id')!=ship_id:continue
        name=row['draft']['owner'] or (row['schedule'] or {}).get('assignee','')
        if name:names.setdefault(name,{'name':name,'work_orders':0,'uploaded_logs':0})['work_orders']+=1
    by_job={r['job']['id']:r for r in rows}
    with store.connect() as c:logs=[store.unseal(r[0]) for r in c.execute('SELECT payload FROM logs')]
    for log in logs:
        row=by_job.get(log['job_id'],{})
        # Legacy logs have no author snapshot; use the linked maintenance record, not an inferred author.
        context=log.get('maintenance_context') or row.get('draft',{})
        if context.get('ship_id')!=ship_id:continue
        name=context.get('owner') or (row.get('schedule') or {}).get('assignee','')
        if name:names.setdefault(name,{'name':name,'work_orders':0,'uploaded_logs':0})['uploaded_logs']+=1
    return {'ship_id':ship_id,'sailors':sorted(names.values(),key=lambda x:x['name']), 'basis':'Saved maintenance records and uploaded logs; legacy logs use the linked work-order assignment.'}
