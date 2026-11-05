"""Demo watch schedule, anchored to first-run host date."""
from datetime import date,timedelta
from . import store
from .demo_procedures import TASKS,CORRECTIVE_TASKS,structured
CENTERS=['Electrical','Mechanical','SONAR']
SAILORS=['FC1 Ochoa','FC3 Kluzak','FC2 Donohue']
CORRECTIVE_SOURCES=['demo-corrective-electrical','demo-corrective-mechanical','demo-corrective-sonar']
def seed():
    today=date.today()
    with store.connect() as c:
        c.execute('CREATE TABLE IF NOT EXISTS watch_schedule(job_id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        for task_source in TASKS:
            procedure=structured(task_source)
            c.execute('DELETE FROM corpus WHERE source=?',(task_source,))
            c.execute('INSERT INTO corpus VALUES (?,?,?)',(task_source,procedure['title'],procedure['scope']+'\n\n'+'\n'.join(procedure['sections'])))
        for n,center in enumerate(CENTERS):
            source='demo-watch-'+center.lower()
            for k,(label,offset,time) in enumerate([('due today',0,'09:00'),('overdue',-2,'10:30'),('completed',0,'13:00')]):
                jid=f'DEMO-{n+1}{k+1}'
                task_source=source if k==0 else source+'-'+str(k+1)
                task_title,asset,_=TASKS[task_source]
                existing=c.execute('SELECT payload FROM watch_schedule WHERE job_id=?',(jid,)).fetchone()
                if existing:
                    schedule=store.unseal(existing[0]);schedule['procedure_source']=task_source
                    c.execute('UPDATE watch_schedule SET payload=? WHERE job_id=?',(store.seal(schedule),jid))
                    row=c.execute('SELECT payload FROM jobs WHERE id=?',(jid,)).fetchone()
                    if row:
                        job=store.unseal(row[0]);job.update(title=task_title,asset=asset)
                        c.execute('UPDATE jobs SET payload=? WHERE id=?',(store.seal(job),jid))
                    continue
                completed=k==2
                job={'id':jid,'title':task_title,'asset':asset,'status':'Completed locally' if completed else 'Open','priority':'High' if k==1 else 'Routine','version':1}
                if completed:job['completed']=today.isoformat()+'T08:00:00'
                record={'work_center':center,'assignee':SAILORS[n],'due_date':(today+timedelta(days=offset)).isoformat(),'time':time,'duration_minutes':30,'procedure_source':task_source,'seeded':today.isoformat()}
                c.execute('INSERT OR IGNORE INTO jobs VALUES (?,?)',(jid,store.seal(job)))
                c.execute('INSERT INTO watch_schedule VALUES (?,?)',(jid,store.seal(record)))
        # Give the original demo jobs the same checklist workflow as later jobs.
        for jid,source,center,assignee in [
            ('WO-001','demo-corrective-electrical','Electrical','FC2 Donohue'),
            ('WO-002','demo-equipment-condition','Electrical','FC3 Kluzak'),
            ('WO-003','demo-consumables-check','Mechanical','FC2 Donohue'),
        ]:
            if not c.execute('SELECT 1 FROM jobs WHERE id=?',(jid,)).fetchone():continue
            existing=c.execute('SELECT payload FROM watch_schedule WHERE job_id=?',(jid,)).fetchone()
            record=store.unseal(existing[0]) if existing else {
                'work_center':center,'assignee':assignee,'due_date':today.isoformat(),
                'time':'14:00','duration_minutes':30,'seeded':today.isoformat(),
            }
            record['procedure_source']=source
            record['corrective']=source in CORRECTIVE_TASKS
            c.execute('INSERT OR REPLACE INTO watch_schedule VALUES (?,?)',(jid,store.seal(record)))
        # Corrective maintenance jobs — something is broken
        for n,(csource,center) in enumerate(zip(CORRECTIVE_SOURCES,CENTERS)):
            jid=f'CM-{n+1}'
            task_title,asset,_=TASKS[csource]
            existing=c.execute('SELECT payload FROM watch_schedule WHERE job_id=?',(jid,)).fetchone()
            if existing:
                schedule=store.unseal(existing[0]);schedule['procedure_source']=csource
                c.execute('UPDATE watch_schedule SET payload=? WHERE job_id=?',(store.seal(schedule),jid))
                row=c.execute('SELECT payload FROM jobs WHERE id=?',(jid,)).fetchone()
                if row:
                    job=store.unseal(row[0]);job.update(title=task_title,asset=asset)
                    c.execute('UPDATE jobs SET payload=? WHERE id=?',(store.seal(job),jid))
                continue
            job={'id':jid,'title':task_title,'asset':asset,'status':'Open','priority':'Urgent','version':1,'corrective':True}
            record={'work_center':center,'assignee':SAILORS[n],'due_date':today.isoformat(),'time':'07:30','duration_minutes':60,'procedure_source':csource,'seeded':today.isoformat(),'corrective':True}
            c.execute('INSERT OR IGNORE INTO jobs VALUES (?,?)',(jid,store.seal(job)))
            c.execute('INSERT INTO watch_schedule VALUES (?,?)',(jid,store.seal(record)))
def schedules():
    with store.connect() as c:return {r[0]:store.unseal(r[1]) for r in c.execute('SELECT * FROM watch_schedule')}
seed()
