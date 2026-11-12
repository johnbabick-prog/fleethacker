import os,tempfile,unittest,json
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from fastapi.testclient import TestClient
from hatch.app import app,prepare_question,Question
from hatch import conversations,store

class CaseMemory(unittest.TestCase):
 def test_conversation_reuse_and_immutable_resolution_snapshot(self):
  c=TestClient(app)
  def setup(job,ship,model):
   old=c.get('/api/jobs/'+job+'/draft').json()
   r=c.post('/api/jobs/'+job+'/draft',json={**old,'ship_id':ship,'equipment_id':ship+'::'+model,'owner':'FC3 Kluzak','symptom':'Demo door fault E777','actions_taken':'Inspected the simulated door switch','outcome':'Simulated functional check passed'})
   self.assertEqual(r.status_code,200);return r.json()
  draft=setup('CM-4','DDG-76','water-cooler')
  old=conversations.create(conversations.NewConversation(job_id='CM-4'))
  turn,_=conversations.begin(old['id'],'CM-4','Demo door fault E777 persists; what was checked?',None,0)
  conversations.finish(old['id'],turn,'Inspect the indicated switch according to the applicable manual.')
  r=c.post('/api/jobs/CM-4/troubleshooting',json={'draft_version':draft['version'],'resolution_status':'resolved'})
  self.assertEqual(r.status_code,200);report=r.json()
  self.assertEqual(report['conversation_links'][0]['id'],old['id'])
  self.assertEqual(report['conversation_context'][0]['messages'][1]['content'],'Inspect the indicated switch according to the applicable manual.')
  self.assertEqual(report['resolution_status'],'resolved')
  # More discussion does not rewrite the previously saved report snapshot.
  turn,_=conversations.begin(old['id'],'CM-4','E777 follow-up after recording the result',None,0)
  conversations.finish(old['id'],turn,'Record further observations.')
  with store.connect() as db:
   encrypted=db.execute('SELECT payload FROM troubleshooting WHERE id=?',(report['id'],)).fetchone()[0]
  saved=store.unseal(encrypted);self.assertEqual(len(saved['conversation_context'][0]['messages']),2);self.assertNotIn('door fault E777',encrypted)
  setup('CM-2','DDG-51','water-cooler')
  current=conversations.create(conversations.NewConversation(job_id='CM-2'))
  turn,_=conversations.begin(current['id'],'CM-2','E777 on this unit',None,0);conversations.finish(current['id'],turn,'Current conversation suggestion')
  related=conversations.related_discussions('Arleigh Burke (DDG)','DDG-51::water-cooler','E777',exclude=current['id'])
  self.assertTrue(related);self.assertTrue(all(x['conversation_id']==old['id'] for x in related))
  self.assertEqual(conversations.related_discussions('Nimitz (CVN)','CVN-72::water-cooler','E777'),[])
  self.assertEqual(conversations.related_discussions('Arleigh Burke (DDG)','DDG-51::spy1','E777'),[])
  _,_,refs,context=prepare_question(Question(job_id='CM-2',conversation_id=current['id'],text='What fixed E777 before?'))
  self.assertTrue(any(r.get('conversation_id')==old['id'] for r in refs))
  self.assertTrue(any(r['resolution_status']=='resolved' for r in context['class_troubleshooting_reports']))
  self.assertTrue(all(x['conversation_id']!=current['id'] for x in context['past_equipment_discussions']))
  self.assertNotIn('conversation_context',json.dumps(context['class_troubleshooting_reports']))
  for x in related:self.assertIn('not a verified repair',x['evidence_status'])
