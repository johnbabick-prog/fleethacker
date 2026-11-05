import os,tempfile,unittest
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from fastapi.testclient import TestClient
from hatch.app import app,prepare_question,Question
class Troubleshooting(unittest.TestCase):
 def test_ship_provenance_class_scope_retry_and_ai(self):
  c=TestClient(app);jid='WO-002'
  old=c.get(f'/api/jobs/{jid}/draft').json()
  values={**old,'ship_id':'','equipment_id':'','ship_name':'USS Demo','hull_number':'DDG-DEMO','ship_class':'Arleigh Burke (DDG)','equipment':'Demo lights','symptom':'Intermittent indication','actions_taken':'Reviewed synthetic records','outcome':'Unresolved; further verification needed','owner':'FC2 Donohue'}
  d=c.post(f'/api/jobs/{jid}/draft',json=values).json()
  r=c.post(f'/api/jobs/{jid}/troubleshooting',json={'draft_version':d['version']})
  self.assertEqual(r.status_code,200);report=r.json()
  again=c.post(f'/api/jobs/{jid}/troubleshooting',json={'draft_version':d['version']}).json()
  self.assertEqual(report['id'],again['id'])
  self.assertEqual(report['ship_name'],'USS Demo')
  self.assertTrue(any(x['id']==report['id'] for x in c.get('/api/troubleshooting',params={'ship_class':'Arleigh Burke (DDG)','q':'intermittent'}).json()))
  self.assertFalse(any(x['id']==report['id'] for x in c.get('/api/troubleshooting',params={'ship_class':'Nimitz (CVN)'}).json()))
  _,_,_,ctx=prepare_question(Question(text='Any past reports?',job_id=jid))
  self.assertEqual(ctx['ship_context']['hull_number'],'DDG-DEMO')
  self.assertTrue(any(x['id']==report['id'] for x in ctx['class_troubleshooting_reports']))
  values={**d,'ship_name':'Different ship','ship_class':'DDG'}
  changed=c.post(f'/api/jobs/{jid}/draft',json=values).json()
  self.assertEqual(c.post(f'/api/jobs/{jid}/troubleshooting',json={'draft_version':changed['version']}).status_code,422)
  saved=c.get('/api/troubleshooting',params={'ship_class':'Arleigh Burke (DDG)'}).json()
  self.assertEqual(next(x for x in saved if x['id']==report['id'])['ship_name'],'USS Demo')

 def test_problem_photo_saved_encrypted_and_attached_to_report(self):
  import base64
  from hatch import store
  c=TestClient(app);jid='WO-001'
  old=c.get(f'/api/jobs/{jid}/draft').json()
  d=c.post(f'/api/jobs/{jid}/draft',json={**old,'ship_id':'DDG-76','equipment_id':'DDG-76::sqq89','owner':'FC2 Donohue','symptom':'E101 intermittent connector fault','actions_taken':'Cleaned simulated connector','outcome':'Demo test passed; fault cleared'}).json()
  png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+afoQAAAAASUVORK5CYII=')
  url=f'/api/jobs/{jid}/problem-photos'
  self.assertEqual(c.post(url,content=b'not an image').status_code,422)
  r=c.post(url,content=png);self.assertEqual(r.status_code,200)
  photo=r.json();self.assertNotIn('data',photo)
  self.assertEqual(c.get(photo['url']).content,png)
  self.assertEqual(c.post(url,content=png).json()['id'],photo['id'])
  self.assertEqual(len(c.get(url).json()),1)
  with store.connect() as conn:
   encrypted=conn.execute('SELECT payload FROM problem_photos WHERE id=?',(photo['id'],)).fetchone()[0]
  self.assertNotIn(base64.b64encode(png).decode(),encrypted)
  report=c.post(f'/api/jobs/{jid}/troubleshooting',json={'draft_version':d['version']}).json()
  self.assertEqual(report['problem_photos'][0]['id'],photo['id'])
  matches=c.get('/api/troubleshooting',params={'ship_class':d['ship_class'],'q':'I have an E101 alarm on my console','similar':'true','equipment_id':d['equipment_id']}).json()
  self.assertEqual(matches[0]['id'],report['id'])
  self.assertEqual(c.get('/api/troubleshooting',params={'ship_class':'Nimitz (CVN)','q':'E101','similar':'true'}).json(),[])
  _,_,_,context=prepare_question(Question(text='What fixed this before?',job_id=jid))
  self.assertEqual(context['class_troubleshooting_reports'][0]['id'],report['id'])
