import os,tempfile,unittest
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from fastapi.testclient import TestClient
from hatch.app import app,store
class ShipMaintenance(unittest.TestCase):
 def test_ship_sailors_and_log_snapshot(self):
  c=TestClient(app)
  def assign(job,ship,sailor):
   d=c.get('/api/jobs/'+job+'/draft').json()
   response=c.post('/api/jobs/'+job+'/draft',json={**d,'ship_id':ship,'owner':sailor,'equipment_id':''})
   self.assertEqual(response.status_code,200)
  assign('WO-001','DDG-51','Snapshot Sailor')
  log=store.save_log('WO-001','test.pdf','application/pdf',b'%PDF-test')
  assign('WO-001','DDG-52','Other Sailor')
  sailors=c.get('/api/ships/DDG-51/maintenance-sailors').json()['sailors']
  saved=next(s for s in sailors if s['name']=='Snapshot Sailor')
  self.assertEqual(saved['uploaded_logs'],1)
  self.assertNotIn('Other Sailor',[s['name'] for s in sailors])
  self.assertEqual(log['maintenance_context']['ship_id'],'DDG-51')
  self.assertEqual(c.get('/api/ships/unknown/maintenance-sailors').status_code,404)
