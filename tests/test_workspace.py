import os,tempfile,unittest
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from fastapi.testclient import TestClient
from hatch.app import app,store
class Workspace(unittest.TestCase):
 def test_draft_resume_conflict_and_handoff(self):
  c=TestClient(app)
  d=c.get('/api/jobs/WO-002/draft').json()
  body={'version':d['version'],'owner':'Demo watch','location':'Demo compartment','ship_class':'DDG','notes':'Synthetic note','blockers':'Awaiting demo supplies','next_watch':'Verify receipt'}
  r=c.post('/api/jobs/WO-002/draft',json=body)
  self.assertEqual(r.status_code,200)
  self.assertEqual(c.get('/api/jobs/WO-002/draft').json()['notes'],'Synthetic note')
  self.assertEqual(c.post('/api/jobs/WO-002/draft',json=body).status_code,409)
  handoff=c.get('/api/jobs/WO-002/handoff').json()['text']
  self.assertIn('Awaiting demo supplies',handoff)
  self.assertIn('Verify receipt',handoff)
  with store.connect() as db:
   raw=db.execute('SELECT payload FROM drafts WHERE job_id=?',('WO-002',)).fetchone()[0]
   self.assertNotIn('Synthetic note',raw)
  self.assertEqual(c.get('/api/jobs/missing/draft').status_code,404)
 def test_assigned_sailor_controls_ai_experience(self):
  from hatch.app import prepare_question,Question
  c=TestClient(app)
  for sailor,expected in [('FC1 Ochoa','Experienced'),('FC2 Donohue','Intermediate'),('FC3 Kluzak','First time')]:
   draft=c.get('/api/jobs/WO-003/draft').json()
   self.assertEqual(c.post('/api/jobs/WO-003/draft',json={'version':draft['version'],'owner':sailor}).status_code,200)
   _,payload,_,context=prepare_question(Question(text='Explain this task',job_id='WO-003'))
   self.assertEqual(context['technician_experience']['level'],expected)
   self.assertIn('technician_experience',payload['messages'][0]['content'])
 def test_job_greeting_matches_assigned_experience(self):
  c=TestClient(app)
  for sailor,phrase in [('FC1 Ochoa','more than 10 times'),('FC2 Donohue','3–4 times'),('FC3 Kluzak','first time')]:
   draft=c.get('/api/jobs/WO-003/draft').json()
   c.post('/api/jobs/WO-003/draft',json={'version':draft['version'],'owner':sailor})
   response=c.get('/api/jobs/WO-003/greeting')
   self.assertEqual(response.status_code,200)
   self.assertIn(sailor,response.json()['text'])
   self.assertIn(phrase,response.json()['text'])
   self.assertIn('demo',response.json()['mode'])
  self.assertEqual(c.get('/api/jobs/missing/greeting').status_code,404)
 def test_twelve_steps_persist_across_reassignment(self):
  c=TestClient(app)
  source='demo-watch-electrical'
  p=c.get('/api/procedure',params={'source':source}).json()
  self.assertEqual(len(p['sections']),11)
  self.assertTrue(p['structured_steps'])
  old=c.get('/api/jobs/WO-001/procedure').json()['session']
  result=c.post('/api/jobs/WO-001/procedure',json={'source':source,'revision_hash':p['revision_hash'],'checked':[0,1,10],'note':'Demo checklist','version':old['version'] if old else 0})
  self.assertEqual(result.status_code,200)
  draft=c.get('/api/jobs/WO-001/draft').json()
  self.assertEqual(c.post('/api/jobs/WO-001/draft',json={**draft,'owner':'FC3 Kluzak'}).status_code,200)
  self.assertEqual(c.get('/api/jobs/WO-001/procedure').json()['session']['checked'],[0,1,10])
  self.assertIn('first time',c.get('/api/jobs/WO-001/greeting').json()['text'])

 def test_step_corrections_are_sailor_and_step_specific(self):
  from hatch.app import prepare_question,Question
  c=TestClient(app);job='WO-002';source='demo-watch-electrical'
  d=c.get('/api/jobs/'+job+'/draft').json()
  c.post('/api/jobs/'+job+'/draft',json={**d,'owner':'FC3 Kluzak'})
  lesson=c.post('/api/jobs/'+job+'/lessons',json={'source':source,'step':4,'kind':'correction','text':'Exercise: selected the wrong virtual test point; corrected before continuing.'}).json()
  self.assertEqual(lesson['sailor'],'FC3 Kluzak')
  _,_,_,context=prepare_question(Question(text='Help with this step',job_id=job,source=source,section=4))
  self.assertEqual(context['active_step']['number'],5)
  self.assertIn(lesson['id'],[l['id'] for l in context['sailor_recorded_corrections']])
  _,_,_,other=prepare_question(Question(text='Help',job_id=job,source=source,section=5))
  self.assertNotIn(lesson['id'],[l['id'] for l in other['sailor_recorded_corrections']])
  d=c.get('/api/jobs/'+job+'/draft').json();c.post('/api/jobs/'+job+'/draft',json={**d,'owner':'FC1 Ochoa'})
  _,_,_,other=prepare_question(Question(text='Help',job_id=job,source=source,section=4))
  self.assertNotIn(lesson['id'],[l['id'] for l in other['sailor_recorded_corrections']])
  self.assertEqual(c.post('/api/jobs/'+job+'/lessons',json={'source':source,'step':99,'text':'Invalid'}).status_code,400)

 def test_synthetic_coaching_matches_step_and_experience(self):
  c=TestClient(app);source='demo-watch-electrical'
  def coach(sailor,step):return c.get('/api/step-coaching',params={'source':source,'step':step,'sailor':sailor}).json()
  self.assertEqual(coach('FC1 Ochoa',0)['demo_history']['completed_exercises'],12)
  mid=coach('FC2 Donohue',5)
  self.assertEqual(mid['demo_history']['completed_exercises'],4)
  self.assertTrue(len(mid['corrections'])>0)
  self.assertFalse(coach('FC2 Donohue',6)['demo_history']['corrections'])
  novice=coach('FC3 Kluzak',5)
  self.assertEqual(novice['demo_history']['completed_exercises'],0)
  self.assertEqual(novice['demo_history']['corrections'],[])
  self.assertEqual(len(novice['demo_history']['lessons']),1)
  self.assertEqual(c.get('/api/step-coaching',params={'source':source,'step':99}).status_code,400)

 def test_step_help_uses_compact_request(self):
  from hatch.app import prepare_question,Question
  import json
  _,payload,_,_=prepare_question(Question(text='Explain this step',source='demo-watch-electrical',section=4,step_help=True))
  self.assertEqual(payload['max_tokens'],450)
  context=json.loads(payload['messages'][-1]['content'].split('\nQUESTION:')[0])
  self.assertIn('active_step',context)
  self.assertNotIn('jobs',context)
  self.assertNotIn('parts',context)
  self.assertEqual(len(payload['messages']),2)
