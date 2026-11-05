import os,tempfile,unittest
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from fastapi.testclient import TestClient
from hatch.app import app
class Ships(unittest.TestCase):
 def test_directory_and_canonical_selection(self):
  c=TestClient(app);ships=c.get('/api/ships').json()['ships']
  self.assertGreater(len(ships),400)
  self.assertEqual(len({s['id'] for s in ships}),len(ships))
  lincoln=next(s for s in ships if s['hull_number']=='CVN-72')
  self.assertEqual(lincoln['name'],'USS Abraham Lincoln')
  self.assertEqual(lincoln['ship_class'],'Nimitz (CVN)')
  d=c.get('/api/jobs/WO-003/draft').json()
  result=c.post('/api/jobs/WO-003/draft',json={**d,'ship_id':lincoln['id'],'ship_name':'typo','ship_class':'wrong'})
  self.assertEqual(result.status_code,200)
  self.assertEqual(result.json()['ship_name'],lincoln['name'])
  self.assertEqual(result.json()['ship_class'],lincoln['ship_class'])
  self.assertEqual(result.json()['hull_number'],'CVN-72')
  self.assertEqual(c.post('/api/jobs/WO-003/draft',json={**result.json(),'ship_id':'bogus'}).status_code,422)
