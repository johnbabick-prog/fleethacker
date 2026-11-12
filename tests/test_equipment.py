import os,tempfile,unittest
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from fastapi.testclient import TestClient
from hatch.app import app,prepare_question,Question
class Equipment(unittest.TestCase):
 def test_class_filter_stock_and_ship_validation(self):
  c=TestClient(app)
  burke=c.get('/api/ships/DDG-51/equipment').json()['items']
  zumwalt=c.get('/api/ships/DDG-1000/equipment').json()['items']
  self.assertEqual(len(burke),7);self.assertEqual(len(zumwalt),2)
  self.assertEqual({x['inventory']['assessment'] for x in burke},{'Ready','Short','Unknown'})
  self.assertEqual(c.get('/api/ships/CVN-72/equipment').json()['items'],[])
  item=next(x for x in burke if x['id']=='spy1')
  self.assertEqual(item['inventory']['available'],1)
  self.assertEqual(item['inventory']['shortage'],1)
  d=c.get('/api/jobs/WO-002/draft').json()
  r=c.post('/api/jobs/WO-002/draft',json={**d,'ship_id':'DDG-51','equipment_id':item['equipment_id'],'equipment':'Wrong name'})
  self.assertEqual(r.status_code,200)
  self.assertEqual(r.json()['equipment'],item['name'])
  _,_,_,ctx=prepare_question(Question(text='Check inventory',job_id='WO-002'))
  self.assertIn('inventory',ctx['selected_demo_equipment'])
  bad=c.post('/api/jobs/WO-002/draft',json={**r.json(),'ship_id':'DDG-1000'})
  self.assertEqual(bad.status_code,422)
