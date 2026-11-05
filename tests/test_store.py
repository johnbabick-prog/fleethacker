import os, tempfile, unittest
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from hatch import store
class Workflow(unittest.TestCase):
 def setUp(self):
  store.init()
  with store.connect() as c:
   c.execute('DELETE FROM events')
   c.execute('DELETE FROM receipts')
   c.execute('DELETE FROM jobs')
  store.init()
 def test_offline_completion_and_idempotent_delivery(self):
  store.init()
  eid=store.complete('WO-001',1,123.4,'Reviewed demo work')
  with store.connect() as c:
   raw=c.execute('SELECT payload FROM events WHERE id=?',(eid,)).fetchone()[0]
   self.assertNotIn('Reviewed demo work',raw)
  self.assertEqual(store.sync('shore'),0)
  self.assertEqual(store.sync('ship'),1)
  self.assertEqual(store.sync('ship'),0)
  self.assertEqual(store.sync('shore'),1)
  self.assertEqual(store.sync('shore'),0)
  with self.assertRaises(ValueError):store.complete('WO-001',1,123.4,'Duplicate')
  self.assertEqual(store.jobs()[0]['status'],'Completed locally')
 def test_search_preserves_source(self):
  store.init()
  with store.connect() as c:c.execute('INSERT INTO corpus VALUES (?,?,?)',('test-module','Lighting record','Synthetic lighting reference'))
  self.assertEqual(store.search('lighting')[0]['source'],'test-module')
  self.assertEqual(store.search('" OR *'),[])
 def test_completion_without_reading_and_real_zero(self):
  from fastapi.testclient import TestClient
  from hatch.app import app
  c=TestClient(app)
  for job,payload in [('WO-001',{}),('WO-002',{'meter':None}),('WO-003',{'meter':0})]:
   result=c.post('/api/jobs/'+job+'/complete',json={'version':1,'note':'Inspection complete',**payload})
   self.assertEqual(result.status_code,200)
  jobs={j['id']:j for j in store.jobs()}
  self.assertIsNone(jobs['WO-001']['meter'])
  self.assertIsNone(jobs['WO-002']['meter'])
  self.assertEqual(jobs['WO-003']['meter'],0)
  self.assertNotIn('Meter reading:',c.get('/api/jobs/WO-001/handoff').json()['text'])
  self.assertIn('Meter reading: 0',c.get('/api/jobs/WO-003/handoff').json()['text'])
