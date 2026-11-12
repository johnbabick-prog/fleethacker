"""Future Higgins demo work; dates are fixed on first creation, never rolled forward."""
from datetime import date,timedelta
from . import store

def seed():
    today=date.today()
    with store.connect() as c:
        for index,(source,days) in enumerate([('DEMO-11',1),('DEMO-12',2),('DEMO-21',3),('DEMO-22',5),('DEMO-31',7),('DEMO-32',14)],1):
            jid=f'FUT-{index:02d}'
            if c.execute('SELECT 1 FROM jobs WHERE id=?',(jid,)).fetchone():continue
            job=store.unseal(c.execute('SELECT payload FROM jobs WHERE id=?',(source,)).fetchone()[0])
            dr=c.execute('SELECT payload FROM drafts WHERE job_id=?',(source,)).fetchone()
            draft=store.unseal(dr[0]) if dr else {}
            schedule=store.unseal(c.execute('SELECT payload FROM watch_schedule WHERE job_id=?',(source,)).fetchone()[0])
            from .ships import BY_ID
            from .equipment import resolve
            ship=BY_ID['DDG-76'];model=(draft.get('equipment_id') or {'Electrical':'spy1','Mechanical':'lm2500','SONAR':'sqq89'}[schedule['work_center']]).split('::')[-1];item=resolve(ship['id'],ship['id']+'::'+model)
            job={k:job[k] for k in ('title','asset','priority')}
            job.update(id=jid,status='Open',version=1,corrective=False)
            draft.update(owner=draft.get('owner') or schedule['assignee'],location=draft.get('location',''),ship_id=ship['id'],ship_name=ship['name'],hull_number=ship['hull_number'],ship_class=ship['ship_class'],equipment_id=item['equipment_id'],equipment=item['name'],version=1,updated=store.now(),notes='',symptom='',actions_taken='',outcome='',blockers='',next_watch='')
            schedule.update(due_date=(today+timedelta(days=days)).isoformat(),seeded=today.isoformat(),corrective=False,assignee=draft['owner'])
            c.execute('INSERT INTO jobs VALUES (?,?)',(jid,store.seal(job)))
            c.execute('INSERT INTO drafts VALUES (?,?)',(jid,store.seal(draft)))
            c.execute('INSERT INTO watch_schedule VALUES (?,?)',(jid,store.seal(schedule)))
