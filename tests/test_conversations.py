import os,tempfile,unittest,io,json
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from unittest.mock import patch
from fastapi.testclient import TestClient
from hatch.app import app
from hatch import conversations,store

class Conversations(unittest.TestCase):
 def test_equipment_history_spans_jobs_but_excludes_other_equipment(self):
  client=TestClient(app)
  with patch('hatch.conversations.snapshot',return_value={'equipment_id':'test-ship::teller'}):
   first=client.post('/api/conversations',json={'job_id':'history-one','problem':'Door jam'}).json()
   repeat=client.post('/api/conversations',json={'job_id':'history-two','problem':'Power fault'}).json()
  with patch('hatch.conversations.snapshot',return_value={'equipment_id':'test-ship::sonar'}):
   other=client.post('/api/conversations',json={'job_id':'history-three','problem':'Signal fault'}).json()
  ids={r['id'] for r in client.get('/api/conversations',params={'equipment_id':'test-ship::teller'}).json()}
  self.assertEqual(ids,{first['id'],repeat['id']})
  self.assertNotIn(other['id'],ids)
  self.assertEqual(client.get('/api/conversations',params={'equipment_id':''}).json(),[])

 def test_saved_stream_history_references_and_encryption(self):
  client=TestClient(app);c=client.post('/api/conversations',json={'job_id':'CM-4'}).json()
  seen=[];refs=[{'citation':'PDF-demo-p1','source':'Manual · PDF page 1','title':'Test reference','excerpt':'Saved reference text'}]
  def prepare(q):
   seen.append(q)
   return 'http://127.0.0.1:8080/v1/chat/completions',{'model':'demo','messages':[]},refs,{}
  def response(*args,**kwargs):return io.BytesIO(b'data: {"choices":[{"delta":{"content":"<think>private reasoning</think>Saved final answer"},"finish_reason":"stop"}]}\n\ndata: [DONE]\n')
  with patch('hatch.app.prepare_question',side_effect=prepare),patch('hatch.app.urllib.request.urlopen',side_effect=response):
   r=client.post('/api/chat/stream',json={'conversation_id':c['id'],'job_id':'CM-4','text':'My first question'})
   self.assertEqual(r.status_code,200)
   saved=TestClient(app).get('/api/conversations/'+c['id']).json()
   self.assertEqual([m['content'] for m in saved['messages']],['My first question','Saved final answer'])
   self.assertEqual(saved['messages'][1]['references'],refs)
   self.assertTrue(all(m['status']=='complete' for m in saved['messages']))
   client.post('/api/chat/stream',json={'conversation_id':c['id'],'job_id':'CM-4','text':'Follow-up','history':[{'role':'assistant','content':'Wrong browser history'}]})
  self.assertEqual([h.content for h in seen[1].history],['My first question','Saved final answer'])
  self.assertIn(c['id'],[x['id'] for x in client.get('/api/conversations',params={'job_id':'CM-4'}).json()])
  self.assertEqual(client.post('/api/chat/stream',json={'conversation_id':c['id'],'job_id':'WO-001','text':'Wrong job'}).status_code,409)
  with store.connect() as conn:encrypted=conn.execute('SELECT payload FROM conversations WHERE id=?',(c['id'],)).fetchone()[0]
  self.assertNotIn('My first question',encrypted);self.assertNotIn('private reasoning',json.dumps(conversations.get(c['id'])))
 def test_failure_and_interruption_are_not_successful_answers(self):
  client=TestClient(app);c=client.post('/api/conversations',json={}).json()
  with patch('hatch.app.prepare_question',return_value=('http://127.0.0.1:8080/v1/chat/completions',{'model':'demo'},[],{})),patch('hatch.app.urllib.request.urlopen',side_effect=OSError('offline')):
   client.post('/api/chat/stream',json={'conversation_id':c['id'],'text':'Keep this question'})
  saved=client.get('/api/conversations/'+c['id']).json()
  self.assertEqual(saved['messages'][0]['content'],'Keep this question');self.assertEqual(saved['messages'][1]['status'],'failed')
  turn,history=conversations.begin(c['id'],None,'Interrupted question',None,0)
  self.assertEqual(len(history),1)
  conversations.ACTIVE.discard((c['id'],turn))
  restored=client.get('/api/conversations/'+c['id']).json()
  self.assertEqual(restored['messages'][-1]['status'],'interrupted')
  self.assertEqual(client.get('/api/conversations/missing').status_code,404)

 def test_new_problem_threads_keep_separate_context(self):
  from hatch.app import prepare_question,Question
  c=TestClient(app);jid='CM-4'
  first=c.post('/api/conversations',json={'job_id':jid,'problem':'The door will not open'}).json()
  turn,_=conversations.begin(first['id'],jid,'Door problem',None,0);conversations.finish(first['id'],turn,'Check the matching door references.')
  second=c.post('/api/conversations',json={'job_id':jid,'problem':'The system will not turn on'}).json()
  self.assertNotEqual(first['id'],second['id']);self.assertEqual(second['title'],'The system will not turn on')
  turn,history=conversations.begin(second['id'],jid,'Power problem',None,0);self.assertEqual(history,[]);conversations.finish(second['id'],turn,'Check the matching power references.')
  _,_,_,old_context=prepare_question(Question(job_id=jid,conversation_id=first['id'],text='What next?'))
  _,_,_,new_context=prepare_question(Question(job_id=jid,conversation_id=second['id'],text='What next?'))
  self.assertEqual(old_context['reported_problem'],'The door will not open');self.assertEqual(new_context['reported_problem'],'The system will not turn on')
  self.assertEqual(len(conversations.get(first['id'])['messages']),2)

 def test_empty_thread_reuse_and_topic_titles(self):
  client=TestClient(app)
  first=client.post('/api/conversations',json={}).json()
  second=client.post('/api/conversations',json={}).json()
  self.assertEqual(first['id'],second['id'])
  turn,_=conversations.begin(first['id'],None,'hello',None,0)
  conversations.finish(first['id'],turn,'Hello')
  self.assertEqual(client.get('/api/conversations/'+first['id']).json()['title'],'General discussion')
  turn,_=conversations.begin(first['id'],None,'The system will not turn on',None,0)
  conversations.finish(first['id'],turn,'Check the cited manual')
  named=client.get('/api/conversations/'+first['id']).json()
  self.assertEqual(named['title'],'The system will not turn on')
  self.assertEqual(len(named['messages']),4)
  fresh=client.post('/api/conversations',json={}).json()
  self.assertNotEqual(fresh['id'],first['id'])
  self.assertEqual(client.post('/api/conversations',json={}).json()['id'],fresh['id'])
  title=conversations.topic_title({'messages':[{'role':'user','content':'The sailor reports: The door is jammed\n\nUse analyzed equipment manuals'}]})
  self.assertEqual(title,'The door is jammed')
  self.assertLessEqual(len(conversations.topic_title({'problem':'Long topic ' * 30})),72)

 def test_findings_draft_never_publishes_or_uses_assistant_actions(self):
  c=TestClient(app);thread=c.post('/api/conversations',json={'job_id':'CM-4','problem':'Door jammed'}).json()
  turn,_=conversations.begin(thread['id'],'CM-4','I released the latch and now it works',None,0)
  conversations.finish(thread['id'],turn,'Replace the motor next')
  before=c.get('/api/jobs/CM-4/draft').json()
  proposed={'symptom':'Door jammed','actions_taken':'Technician reports releasing the latch.','outcome':'Technician reports normal operation; verification pending.'}
  with patch('hatch.manual_analysis.local_completion',return_value=json.dumps(proposed)) as model:
   r=c.post('/api/conversations/'+thread['id']+'/findings-draft').json()
  self.assertEqual(r['fields'],proposed);self.assertTrue(r['review_required']);self.assertEqual(r['resolution_status'],'not_verified')
  prompt=model.call_args[0][0]['messages'][-1]['content'];self.assertNotIn('Replace the motor',prompt)
  self.assertEqual(c.get('/api/jobs/CM-4/draft').json(),before)
  with patch('hatch.manual_analysis.local_completion',side_effect=ValueError('Offline')):
   fallback=c.post('/api/conversations/'+thread['id']+'/findings-draft').json()
  self.assertEqual(fallback['mode'],'Conversation excerpts');self.assertIn('released the latch',fallback['fields']['actions_taken'])
