import os,tempfile,unittest,json,uuid
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from unittest.mock import patch
from fastapi.testclient import TestClient
from hatch.app import app,prepare_question,Question
from hatch import store
from hatch import manual_analysis as analysis

class ManualAnalysis(unittest.TestCase):
 def fixture(self):
  doc={'id':str(uuid.uuid4()),'name':'Test manual.pdf','sha256':str(uuid.uuid4()),'revision':'A','ship_id':'DDG-76','equipment_id':'DDG-76::water-cooler','model_id':'water-cooler','equipment_name':'Fortis 5000 DS remote teller system','ship_class':'Arleigh Burke (DDG)','scope':'ship','page_count':3,'indexed_pages':2,'pages_without_text':[3],'pages':[{'page':1,'text':'Operation and door status. '*300},{'page':2,'text':'Door fault checks. '*300}],'content':''}
  with store.connect() as c:c.execute('INSERT INTO equipment_documents VALUES (?,?)',(doc['id'],store.seal(doc)))
  return doc
 def test_batches_cover_every_character(self):
  doc=self.fixture();parts=analysis.batches(doc)
  for p in doc['pages']:self.assertEqual(''.join(x['text'] for b in parts for x in b if x['page']==p['page']),p['text'])
 def test_checkpoint_resume_and_prompt_grounding(self):
  doc=self.fixture();calls=[]
  def worker(batch):
   calls.append(batch)
   if len(calls)==2:raise OSError('model offline')
   return {'overview':'Door operation','facts':[{'text':'Check recorded door status','pages':[batch[0]['page']]}],'pages':sorted({p['page'] for p in batch})}
  with patch.object(analysis,'analyze_batch',side_effect=worker):analysis.run(doc['id'])
  failed=analysis.read(doc['id']);self.assertEqual(failed['status'],'failed');self.assertEqual(len(failed['sections']),1)
  with patch.object(analysis,'analyze_batch',side_effect=worker):analysis.run(doc['id'])
  done=analysis.status(doc['id']);self.assertEqual(done['status'],'complete');self.assertEqual(done['pages_analyzed'],2);self.assertEqual(done['pages_without_text'],[3]);self.assertFalse(done['visual_analysis'])
  client=TestClient(app);self.assertEqual(client.get('/api/equipment-documents/'+doc['id']+'/analysis').json()['status'],'complete')
  old=client.get('/api/jobs/CM-4/draft').json();client.post('/api/jobs/CM-4/draft',json={**old,'ship_id':'DDG-76','equipment_id':'DDG-76::water-cooler','symptom':'Door fault'})
  _,payload,refs,ctx=prepare_question(Question(job_id='CM-4',text='How does this system work?'))
  self.assertTrue(any(m['document']=='Test manual.pdf' for m in ctx['manual_knowledge']['manuals']))
  self.assertTrue(any(r.get('document_id')==doc['id'] for r in refs))
  self.assertEqual(ctx['reported_problem'],'Door fault')
  with store.connect() as c:encrypted=c.execute('SELECT payload FROM manual_analysis WHERE document_id=?',(doc['id'],)).fetchone()[0]
  self.assertNotIn('Door operation',encrypted)
 def test_invalid_citation_and_nonlocal_endpoint_rejected(self):
  with patch.object(analysis,'local_completion',return_value=json.dumps({'overview':'Example','facts':[{'text':'Wrong page','pages':[99]}]})):
   with self.assertRaises(ValueError):analysis.analyze_batch([{'page':1,'text':'Example'}])
  with patch.dict(os.environ,{'HATCH_LLM_URL':'https://example.com/v1/chat/completions'}):
   with self.assertRaises(ValueError):analysis.local_completion({})
 def test_definition_question_uses_manual_not_old_fault(self):
  c=TestClient(app);old=c.get('/api/jobs/CM-4/draft').json()
  c.post('/api/jobs/CM-4/draft',json={**old,'ship_id':'DDG-76','equipment_id':'DDG-76::water-cooler','symptom':'The door is jammed'})
  doc=self.fixture();doc['pages']=[{'page':14,'text':'Teller Unit Operation. Teller Night Lock closes the inside teller door and disables send and recall functions.'},{'page':19,'text':'Troubleshooting: night lock on. Turn night lock off. Night lock switch. Night lock.'}]
  from hatch.equipment_docs import retrieve
  refs=retrieve(None,None,'what is the night lock?',documents=[doc]);self.assertEqual(refs[0]['page'],14)
  with patch('hatch.equipment_docs.matching',return_value=[doc]):
   _,payload,evidence,context=prepare_question(Question(job_id='CM-4',source='demo-corrective-teller-system',text='what is the night lock?',history=[{'role':'user','content':'Give troubleshooting steps for a jammed door'}]))
  self.assertIn('Explain the term',context['task']);self.assertNotIn('class_troubleshooting_reports',context)
  self.assertNotIn('active_step',context);self.assertEqual(evidence[0]['page'],14)
  self.assertEqual(len(payload['messages']),2);self.assertIn('disables send and recall',payload['messages'][-1]['content'])
