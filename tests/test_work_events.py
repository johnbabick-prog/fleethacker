import os,tempfile,unittest
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from fastapi.testclient import TestClient
from hatch.app import app,store

class WorkEvents(unittest.TestCase):
 def test_create_and_validate(self):
  c=TestClient(app)
  body=dict(ship_id='DDG-76',equipment_id='DDG-76::water-cooler',owner=' fc3 kluzak ',title='Diagnose no power',work_center='Electrical',due_date='2026-11-05',time='13:30',corrective=True,description='No lights or sound')
  response=c.post('/api/work-events',json=body);self.assertEqual(response.status_code,201,response.text)
  r=response.json();jid=r['job']['id']
  self.assertEqual(r['draft']['owner'],'FC3 Kluzak');self.assertEqual(r['job']['status'],'Open')
  self.assertEqual(r['draft']['equipment_id'],body['equipment_id']);self.assertEqual(r['draft']['symptom'],body['description'])
  self.assertEqual(r['schedule']['due_date'],body['due_date']);self.assertIsNone(r['schedule']['procedure_source'])
  self.assertIn(jid,[r['job']['id'] for r in c.get('/api/watch').json()])
  self.assertEqual(c.get(f'/api/jobs/{jid}/draft').json()['owner'],'FC3 Kluzak')
  with store.connect() as conn:
   payload=conn.execute('SELECT payload FROM jobs WHERE id=?',(jid,)).fetchone()[0];self.assertNotIn(body['title'],payload)
   events=[store.unseal(r[0]) for r in conn.execute('SELECT payload FROM events')]
  self.assertTrue(any(e.get('job_id')==jid and e.get('kind')=='work_order_created' for e in events))
  count=len(store.jobs())
  for changes in [{'equipment_id':'DDG-51::spy1'},{'ship_id':'unknown'},{'owner':'  '},{'title':'  '},{'due_date':'invalid'},{'work_center':'invalid'}]:
   self.assertIn(c.post('/api/work-events',json={**body,**changes}).status_code,[404,422])
  self.assertEqual(len(store.jobs()),count)

 def test_repeat_keeps_original_and_resets_completion(self):
  c=TestClient(app)
  r=c.post('/api/work-events',json=dict(ship_id='DDG-76',equipment_id='DDG-76::water-cooler',owner='FC3 Kluzak',title='Teller maintenance',work_center='Electrical',due_date='2026-11-05',time='09:00',description='Routine inspection')).json()
  jid=r['job']['id'];job=r['job'];job.update(status='Completed locally',completed=store.now(),note='Finished last visit')
  with store.connect() as conn:conn.execute('UPDATE jobs SET payload=? WHERE id=?',(store.seal(job),jid))
  response=c.post(f'/api/jobs/{jid}/repeat',json={'due_date':'2026-12-05','time':'10:30'});self.assertEqual(response.status_code,201,response.text)
  new=response.json();self.assertNotEqual(new['job']['id'],jid);self.assertEqual(new['job']['repeated_from'],jid);self.assertEqual(new['job']['status'],'Open');self.assertNotIn('completed',new['job'])
  self.assertEqual(new['draft']['equipment_id'],r['draft']['equipment_id']);self.assertEqual(new['draft']['owner'],'FC3 Kluzak');self.assertEqual(new['draft']['notes'],'Routine inspection');self.assertEqual(new['draft']['outcome'],'')
  self.assertEqual(new['schedule']['due_date'],'2026-12-05');self.assertIsNone(store.session(new['job']['id']))
  self.assertEqual(next(j for j in store.jobs() if j['id']==jid),job)
  self.assertEqual(c.post('/api/jobs/'+new['job']['id']+'/repeat',json={'due_date':'2026-12-05','time':'10:30'}).status_code,409)
