import os,tempfile,unittest
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from fastapi.testclient import TestClient
from hatch.app import app,store

class Assignments(unittest.TestCase):
 def test_transfer_preserves_progress_context_and_audit(self):
  c=TestClient(app);jid='DEMO-11'
  old=c.get(f'/api/jobs/{jid}/draft').json()
  d=c.post(f'/api/jobs/{jid}/draft',json={**old,'ship_id':'DDG-76','equipment_id':'DDG-76::spy1','owner':'FC1 Ochoa','notes':'Existing work notes','next_watch':'Verify recorded findings'}).json()
  p=c.get('/api/procedure',params={'source':'demo-watch-electrical'}).json()
  session=store.session(jid)
  store.save_session(jid,p['source'],p['revision_hash'],[0,1],'Handoff progress',session['version'] if session else 0)
  before_session=store.session(jid);before_job=next(j for j in store.jobs() if j['id']==jid)
  log=store.save_log(jid,'assignment-test.pdf','application/pdf',b'%PDF-demo')
  response=c.post(f'/api/jobs/{jid}/assignment',json={'version':d['version'],'owner':'  FC2   Rivera  ','reason':'Leave coverage'})
  self.assertEqual(response.status_code,200);saved=response.json()
  self.assertEqual(saved['owner'],'FC2 Rivera')
  for key in d:
   if key not in {'owner','version','updated'}:self.assertEqual(saved[key],d[key])
  self.assertEqual(store.session(jid),before_session)
  self.assertEqual(next(j for j in store.jobs() if j['id']==jid),before_job)
  self.assertEqual(log['maintenance_context']['owner'],'FC1 Ochoa')
  history=c.get(f'/api/jobs/{jid}/assignments').json()
  self.assertEqual((history[0]['from_owner'],history[0]['to_owner'],history[0]['reason']),('FC1 Ochoa','FC2 Rivera','Leave coverage'))
  self.assertIn('FC2 Rivera',[s['name'] for s in c.get('/api/ships/DDG-76/maintenance-sailors').json()['sailors']])
  self.assertEqual(c.post(f'/api/jobs/{jid}/assignment',json={'version':d['version'],'owner':'FC3 Kluzak'}).status_code,409)
  self.assertEqual(c.post(f'/api/jobs/{jid}/assignment',json={'version':saved['version'],'owner':'   '}).status_code,422)
  repeated=c.post(f'/api/jobs/{jid}/assignment',json={'version':saved['version'],'owner':'fc2 rivera'}).json()
  self.assertEqual(repeated['version'],saved['version'])
  self.assertEqual(len(c.get(f'/api/jobs/{jid}/assignments').json()),len(history))
