import io,os,tempfile,unittest
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
from fastapi.testclient import TestClient
from hatch.app import app,prepare_question,Question,store

def fixture(text=None):
    # In-memory synthetic parser fixture; not a user-facing PDF artifact.
    writer=PdfWriter();page=writer.add_blank_page(width=400,height=300)
    if text:
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
        stream=DecodedStreamObject();stream.set_data(('BT /F1 12 Tf 20 250 Td ('+text+') Tj ET').encode())
        page[NameObject('/Contents')]=writer._add_object(stream)
    b=io.BytesIO();writer.write(b);return b.getvalue()
class EquipmentDocs(unittest.TestCase):
 def test_ingest_retrieve_scope_and_citations(self):
    c=TestClient(app);raw=fixture('Synthetic calibration note: indicator amber means review the log.')
    p={'ship_id':'DDG-51','equipment_id':'DDG-51::spy1','scope':'ship','revision':'TEST-A'}
    r=c.post('/api/equipment-documents',params=p,content=raw,headers={'X-Filename':'test-manual.pdf'})
    self.assertEqual(r.status_code,200);doc=r.json();self.assertEqual(doc['indexed_pages'],1)
    catalog=c.get('/api/procedures',params={'q':'test-manual.pdf'}).json()
    self.assertIn(doc['id'],[d['id'] for d in catalog['items']])
    self.assertTrue(all(d['kind'] in ('equipment','schematic') for d in catalog['items']))
    self.assertEqual(c.get('/api/procedures',params={'q':'test-manual.pdf','offset':catalog['total']}).json()['items'],[])
    self.assertEqual(c.get('/api/equipment-documents/'+doc['id']+'/file').content,raw)
    self.assertNotIn(doc['id'],[d['id'] for d in c.get('/api/equipment-documents',params={'ship_id':'DDG-52','equipment_id':'DDG-52::spy1'}).json()])
    shared=c.post('/api/equipment-documents',params={**p,'scope':'class'},content=raw).json()
    self.assertIn(shared['id'],[d['id'] for d in c.get('/api/equipment-documents',params={'ship_id':'DDG-52','equipment_id':'DDG-52::spy1'}).json()])
    self.assertEqual(c.get('/api/equipment-documents',params={'ship_id':'DDG-51','equipment_id':'DDG-51::sqq89'}).json(),[])
    draft=c.get('/api/jobs/WO-002/draft').json()
    self.assertEqual(c.post('/api/jobs/WO-002/draft',json={**draft,'ship_id':'DDG-51','equipment_id':'DDG-51::spy1'}).status_code,200)
    _,_,refs,ctx=prepare_question(Question(text='What does amber indicate?',job_id='WO-002'))
    matches=[r for r in refs if r.get('document_id')==doc['id']]
    self.assertEqual(matches[0]['page'],1);self.assertIn('TEST-A',matches[0]['source'])
    blank=c.post('/api/equipment-documents',params=p,content=fixture()).json()
    self.assertEqual(blank['status'],'Stored — inspect pages without text')
    self.assertEqual(c.post('/api/equipment-documents',params=p,content=b'%PDF-broken').status_code,422)

 def test_shore_distribution_respects_scope(self):
    c=TestClient(app);raw=fixture('Synthetic distribution check')
    args={'ship_id':'DDG-51','equipment_id':'DDG-51::spy1','revision':'SCOPE-TEST'}
    private=c.post('/api/equipment-documents',params={**args,'scope':'ship'},content=raw).json()
    shared=c.post('/api/equipment-documents',params={**args,'scope':'class'},content=raw).json()
    manifest=lambda ship:c.get('/api/ships/'+ship+'/equipment-document-manifest').json()['documents']
    self.assertNotIn(shared['id'],[d['id'] for d in manifest('DDG-52')])
    store.sync('ship');store.sync('shore')
    sister={d['id'] for d in manifest('DDG-52')}
    self.assertIn(shared['id'],sister);self.assertNotIn(private['id'],sister)
    own={d['id'] for d in manifest('DDG-51')}
    self.assertIn(private['id'],own)
    self.assertNotIn(shared['id'],[d['id'] for d in manifest('DDG-1000')])
    before=len(manifest('DDG-52'));store.sync('shore');self.assertEqual(len(manifest('DDG-52')),before)

 def test_visual_pages_preserve_drawings_and_identify_blank_pages(self):
    import pymupdf
    pdf=pymupdf.open()
    page=pdf.new_page(width=400,height=300)
    page.insert_text((20,30),'Synthetic diagram')
    page.draw_rect(pymupdf.Rect(30,50,150,150),color=(0,0,0))
    page=pdf.new_page(width=400,height=300)
    page.draw_line((30,40),(200,200),color=(0,0,0))
    pdf.new_page(width=400,height=300)
    raw=pdf.tobytes();pdf.close()
    c=TestClient(app)
    d=c.post('/api/equipment-documents',params={'ship_id':'DDG-51','equipment_id':'DDG-51::spy1'},content=raw).json()
    root='/api/equipment-documents/'+d['id']
    manifest=c.get(root+'/pages').json()
    self.assertEqual([p['kind'] for p in manifest['pages']],['Text + graphics','Graphics / scan','No detected content'])
    self.assertEqual(manifest['blank_candidates'],[3])
    _,_,refs,context=prepare_question(Question(text='Synthetic diagram',document_id=d['id'],graphics_only=True))
    self.assertEqual({r['page'] for r in refs},{1})
    self.assertTrue(all(r['document_id']==d['id'] for r in refs))
    self.assertIn('/pages/1/image',refs[0]['image_url'])
    self.assertNotIn('jobs',context)

    for page in manifest['pages']:
        r=c.get(page['image_url'])
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.content.startswith(b'\x89PNG'))
        self.assertEqual(r.headers['cache-control'],'no-store')
        pix=pymupdf.Pixmap(r.content)
        self.assertLessEqual(max(pix.width,pix.height),2400)
        if page['page']!=3:self.assertLess(min(pix.samples),100)
    self.assertEqual(c.get(root+'/pages/0/image').status_code,404)
    self.assertEqual(c.get(root+'/pages/4/image').status_code,404)
    self.assertEqual(c.get('/api/equipment-documents/missing/pages').status_code,404)

 def test_graphics_filter_excludes_rules_and_repeated_decorations(self):
    import pymupdf
    pdf=pymupdf.open()
    for n in range(3):
        p=pdf.new_page(width=400,height=300)
        p.insert_text((20,30),'Text page')
        p.draw_line((20,45),(380,45),color=(0,0,0))
        p.draw_rect(pymupdf.Rect(20,250,90,280),color=(0,0,0))
        if n==1:p.draw_circle((180,150),40,color=(0,0,0))
    c=TestClient(app)
    d=c.post('/api/equipment-documents',params={'ship_id':'DDG-51','equipment_id':'DDG-51::spy1'},content=pdf.tobytes()).json()
    pages=c.get('/api/equipment-documents/'+d['id']+'/pages').json()['pages']
    self.assertEqual([p['page'] for p in pages if p['has_graphics']],[2])
    pdf.close()
