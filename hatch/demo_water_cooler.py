"""Idempotent Higgins teller-system demo event; preserve subsequent user edits."""
from datetime import date
from . import store
from .equipment import resolve
from .ships import BY_ID

def seed():
    today=date.today().isoformat()
    ship=BY_ID['DDG-76'];item=resolve('DDG-76','DDG-76::water-cooler')
    job={'id':'CM-4','title':'Troubleshoot and repair Fortis 5000 DS teller system','asset':item['name'],'status':'Open','priority':'High','version':1,'corrective':True}
    schedule={'work_center':'Electrical','assignee':'FC3 Kluzak','due_date':today,'time':'15:00','duration_minutes':60,'procedure_source':'demo-corrective-teller-system','seeded':today,'corrective':True}
    draft={'version':1,'owner':'FC3 Kluzak','ship_id':ship['id'],'ship_name':ship['name'],'hull_number':ship['hull_number'],'ship_class':ship['ship_class'],'equipment_id':item['equipment_id'],'equipment':item['name'],'location':'','notes':'','blockers':'','next_watch':'','symptom':'Reported teller-system malfunction. Confirm the exact symptoms with the reporting sailor.','actions_taken':'','outcome':'','updated':store.now()}
    with store.connect() as c:
        c.execute('INSERT OR IGNORE INTO jobs VALUES (?,?)',(job['id'],store.seal(job)))
        c.execute('INSERT OR IGNORE INTO watch_schedule VALUES (?,?)',(job['id'],store.seal(schedule)))
        c.execute('INSERT OR IGNORE INTO drafts VALUES (?,?)',(job['id'],store.seal(draft)))

        # Retain the original stable equipment ID so existing PDFs stay linked.
        row=c.execute('SELECT payload FROM jobs WHERE id=?',('CM-4',)).fetchone()
        saved=store.unseal(row[0])
        if saved['title']=='Troubleshoot and repair water cooler':
            saved.update(title=job['title'],asset=item['name'],version=saved['version']+1)
            c.execute('UPDATE jobs SET payload=? WHERE id=?',(store.seal(saved),'CM-4'))
            current_schedule=store.unseal(c.execute('SELECT payload FROM watch_schedule WHERE job_id=?',('CM-4',)).fetchone()[0])
            current_schedule.update(work_center='Electrical',procedure_source='demo-corrective-teller-system')
            c.execute('UPDATE watch_schedule SET payload=? WHERE job_id=?',(store.seal(current_schedule),'CM-4'))
            current_draft=store.unseal(c.execute('SELECT payload FROM drafts WHERE job_id=?',('CM-4',)).fetchone()[0])
            current_draft.update(equipment=item['name'],version=current_draft['version']+1,updated=store.now())
            if current_draft.get('symptom')=='Reported water-cooler malfunction. Confirm the exact symptoms with the reporting sailor.':
                current_draft['symptom']=draft['symptom']
            c.execute('UPDATE drafts SET payload=? WHERE job_id=?',(store.seal(current_draft),'CM-4'))
        for row in c.execute('SELECT id,payload FROM equipment_documents').fetchall():
            doc=store.unseal(row['payload'])
            if doc.get('model_id')=='water-cooler' and doc.get('equipment_name')=='Potable-water cooler':
                doc['equipment_name']=item['name']
                c.execute('UPDATE equipment_documents SET payload=? WHERE id=?',(store.seal(doc),row['id']))
        c.execute('DELETE FROM corpus WHERE source=?',('demo-corrective-water-cooler',))
