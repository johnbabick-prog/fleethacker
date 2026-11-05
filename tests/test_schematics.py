import os,tempfile,unittest
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from fastapi.testclient import TestClient
from hatch.app import app,store
class Schematics(unittest.TestCase):
 def test_class_scoped_upload_and_download(self):
  c=TestClient(app)
  catalog=c.get('/api/ship-classes').json()
  self.assertIn('Arleigh Burke (DDG)',catalog['groups']['Surface combatants'])
  raw=b'%PDF-1.4\nSynthetic drawing\n%%EOF'
  a='Arleigh Burke (DDG)';b='Nimitz (CVN)'
  result=c.post('/api/schematics',params={'ship_class':a},content=raw,headers={'X-Filename':'drawing.pdf'})
  self.assertEqual(result.status_code,200)
  item=result.json()
  self.assertIn(item['id'],[f['id'] for f in c.get('/api/schematics',params={'ship_class':a}).json()])
  self.assertNotIn(item['id'],[f['id'] for f in c.get('/api/schematics',params={'ship_class':b}).json()])
  self.assertEqual(c.get('/api/schematics/'+item['id']+'/download').content,raw)
  with store.connect() as db:
   encrypted=db.execute('SELECT payload FROM schematics WHERE id=?',(item['id'],)).fetchone()[0]
   self.assertNotIn('drawing.pdf',encrypted)
  self.assertEqual(c.post('/api/schematics',params={'ship_class':a},content=b'not a drawing').status_code,415)
  self.assertEqual(c.post('/api/schematics',params={'ship_class':'bogus'},content=raw).status_code,422)
  custom='Custom: Test class'
  self.assertEqual(c.post('/api/schematics',params={'ship_class':custom},content=raw).status_code,200)
  self.assertIn(custom,c.get('/api/ship-classes').json()['custom'])
