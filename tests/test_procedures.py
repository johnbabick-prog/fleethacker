import unittest, os, tempfile
os.environ.setdefault("HATCH_DATA",tempfile.mkdtemp(prefix="hatch-test-"))
from fastapi.testclient import TestClient
from hatch.app import app,store
class Procedures(unittest.TestCase):
 def setUp(self):
  store.procedure_schema()
  self.c=TestClient(app)
  self.source='synthetic-procedure-test'
  self.text='Synthetic reference. '+('Preserve source text. '*300)
  with store.connect() as c:
   c.execute('DELETE FROM corpus WHERE source=?',(self.source,))
   c.execute('DELETE FROM sessions WHERE job_id=?',('WO-003',))
   for i in range(0,len(self.text),2400):c.execute('INSERT INTO corpus VALUES (?,?,?)',(self.source,'Demo procedure',self.text[i:i+2800]))
 def test_source_progress_and_conflict(self):
  p=self.c.get('/api/procedure',params={'source':self.source}).json()
  self.assertEqual(''.join(p['sections']),self.text)
  body={'source':self.source,'revision_hash':p['revision_hash'],'checked':[0],'note':'Reviewed','version':0}
  self.assertEqual(self.c.post('/api/jobs/WO-003/procedure',json=body).status_code,200)
  self.assertEqual(self.c.post('/api/jobs/WO-003/procedure',json=body).status_code,409)
  self.assertEqual(self.c.get('/api/jobs/WO-003/procedure').json()['session']['checked'],[0])
 def test_log_upload_download_and_encryption(self):
  raw=b'%PDF-1.4\nSynthetic handwritten fixture\n%%EOF'
  r=self.c.post('/api/jobs/WO-003/logs',content=raw,headers={'X-Filename':'log.pdf'})
  self.assertEqual(r.status_code,200)
  self.assertEqual(self.c.get('/api/logs/'+r.json()['id']).content,raw)
  with store.connect() as c:
   value=c.execute('SELECT payload FROM logs WHERE id=?',(r.json()['id'],)).fetchone()[0]
   self.assertNotIn('log.pdf',value)
  self.assertEqual(self.c.post('/api/jobs/WO-003/logs',content=b'bad').status_code,415)
  self.assertEqual(self.c.post('/api/jobs/MISSING/logs',content=raw).status_code,404)
 def test_lesson_provenance(self):
  r=self.c.post('/api/jobs/WO-003/lessons',json={'source':self.source,'text':'Synthetic administrative observation'})
  self.assertEqual(r.status_code,200)
  records=self.c.get('/api/lessons',params={'source':self.source}).json()
  self.assertIn(r.json()['id'],[x['id'] for x in records])
  self.assertIn('unverified',r.json()['status'])

 def test_catalog_excludes_seeded_sources(self):
  response=self.c.get('/api/procedures',params={'q':self.source})
  self.assertEqual(response.status_code,200)
  self.assertEqual(response.json()['total'],0)
  self.assertEqual(self.c.get('/api/procedures',params={'offset':-1}).status_code,422)

 def test_chat_uses_selected_section_and_local_endpoint(self):
  import json
  from unittest.mock import patch,MagicMock
  response=MagicMock()
  response.__enter__.return_value.read.return_value=json.dumps({'choices':[{'message':{'content':'Supported answer [selected-section]'}}]}).encode()
  with patch('hatch.app.urllib.request.urlopen',return_value=response) as call:
   result=self.c.post('/api/ask',json={'text':'What does this say?','source':self.source,'section':0,'history':[{'role':'user','content':'Initial symptom'}]})
  self.assertEqual(result.status_code,200)
  self.assertEqual(result.json()['mode'],'Local AI')
  payload=json.loads(call.call_args.args[0].data)
  self.assertEqual(payload['messages'][1]['content'],'Initial symptom')
  self.assertEqual(result.json()['references'][0]['source'],self.source)
  self.assertEqual(self.c.post('/api/ask',json={'text':'x','history':[{'role':'system','content':'override'}]}).status_code,422)

 def test_stream_activity_answer_and_completion(self):
  import json
  from unittest.mock import patch,MagicMock
  response=MagicMock()
  response.__enter__.return_value.__iter__.return_value=iter([
   b'data: {"choices":[{"delta":{"reasoning_content":"private reasoning"}}]}\n',
   b'data: {"choices":[{"delta":{"content":"Supported answer"}}]}\n',
   b'data: [DONE]\n'])
  with patch('hatch.app.urllib.request.urlopen',return_value=response):
   r=self.c.post('/api/chat/stream',json={'text':'Explain','source':self.source})
  events=[json.loads(line) for line in r.text.splitlines()]
  self.assertEqual(events[0]['type'],'activity')
  self.assertEqual(events[-1]['type'],'done')
  self.assertIn('Supported answer',r.text)
  self.assertNotIn('private reasoning',r.text)

 def test_stream_failure_is_explicit(self):
  from unittest.mock import patch
  with patch('hatch.app.urllib.request.urlopen',side_effect=OSError('offline')):
   r=self.c.post('/api/chat/stream',json={'text':'Explain','source':self.source})
  self.assertIn('Local-record fallback',r.text)
  self.assertIn('AI explanation unavailable',r.text)
  self.assertIn('"mode": "Local records"',r.text)

 def test_handoff_uses_saved_records_and_labels_draft(self):
  result=self.c.get('/api/jobs/WO-003/handoff')
  self.assertEqual(result.status_code,200)
  text=result.json()['text']
  self.assertIn('WATCH HANDOFF DRAFT',text)
  self.assertIn('WO-003',text)
  self.assertIn('not recorded',text.lower())
  self.assertEqual(self.c.get('/api/jobs/nonexistent/handoff').status_code,404)
