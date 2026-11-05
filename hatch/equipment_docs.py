"""Encrypted equipment-document repository and page-cited local text retrieval."""
import base64,hashlib,io,re,uuid
import pymupdf
from functools import lru_cache
from collections import Counter
from urllib.parse import unquote,quote
from fastapi import APIRouter,HTTPException,Request,Query
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool
from pypdf import PdfReader
from . import store
from .equipment import resolve
router=APIRouter()
with store.connect() as c:
    c.execute('CREATE TABLE IF NOT EXISTS equipment_documents(id TEXT PRIMARY KEY,payload TEXT NOT NULL)')

def public(doc):return {k:v for k,v in doc.items() if k not in ('content','pages')}
def matching(ship_id,equipment_id):
    item=resolve(ship_id,equipment_id)
    with store.connect() as c:docs=[store.unseal(r[0]) for r in c.execute('SELECT payload FROM equipment_documents ORDER BY rowid DESC')]
    return [d for d in docs if d['model_id']==item['id'] and d['ship_class']==item['ship_class'] and (d['scope']=='class' or d['ship_id']==ship_id)]

def ingest(content,name,item,scope,revision):
    try:
        reader=PdfReader(io.BytesIO(content))
        if reader.is_encrypted:raise HTTPException(422,'Upload an unlocked PDF; encrypted PDFs cannot be indexed')
        if len(reader.pages)>500:raise HTTPException(413,'Maximum 500 pages per PDF; split larger manuals')
        pages=[];empty=[]
        for index,page in enumerate(reader.pages,1):
            text=page.extract_text() or ''
            if len(text)>200000:raise HTTPException(413,'Page text too large to index')
            if text.strip():pages.append({'page':index,'text':text})
            else:empty.append(index)
    except HTTPException:raise
    except Exception:raise HTTPException(422,'Unable to read this PDF; check that it is a valid, undamaged file')
    doc={'id':str(uuid.uuid4()),'name':name,'revision':revision,'ship_id':item['ship_id'],'equipment_id':item['equipment_id'],'model_id':item['id'],'equipment_name':item['name'],'ship_class':item['ship_class'],'scope':scope,'created':store.now(),'sha256':hashlib.sha256(content).hexdigest(),'size':len(content),'page_count':len(reader.pages),'indexed_pages':len(pages),'pages_without_text':empty,'status':'Text indexed' if not empty else 'Stored — inspect pages without text','content':base64.b64encode(content).decode(),'pages':pages}
    with store.connect() as c:
        c.execute('INSERT INTO equipment_documents VALUES (?,?)',(doc['id'],store.seal(doc)))
        event={'id':str(uuid.uuid4()),'kind':'equipment_document_uploaded','time':store.now(),'distribution':{'scope':scope,'ship_id':item['ship_id'] if scope=='ship' else None,'ship_class':item['ship_class'],'model_id':item['id']},'document':doc}
        c.execute('INSERT INTO events(id,payload) VALUES (?,?)',(event['id'],store.seal(event)))
    return public(doc)

@router.get('/api/equipment-documents')
def listing(ship_id:str,equipment_id:str):return [public(d) for d in matching(ship_id,equipment_id)]

@router.post('/api/equipment-documents')
async def upload(request:Request,ship_id:str,equipment_id:str,scope:str=Query(default='ship',pattern='^(ship|class)$'),revision:str=Query(default='Not specified',max_length=100)):
    item=resolve(ship_id,equipment_id)
    chunks=[];size=0
    async for chunk in request.stream():
        size+=len(chunk)
        if size>20*1024*1024:raise HTTPException(413,'Maximum file size is 20 MB')
        chunks.append(chunk)
    data=b''.join(chunks)
    if not data.startswith(b'%PDF-'):raise HTTPException(415,'Select a PDF schematic or manual')
    name=unquote(request.headers.get('X-Filename','equipment.pdf')).replace('\\','/').split('/')[-1][:180]
    return await run_in_threadpool(ingest,data,name,item,scope,revision)

@router.get('/api/equipment-documents/{doc_id}/file')
def download(doc_id:str):
    with store.connect() as c:r=c.execute('SELECT payload FROM equipment_documents WHERE id=?',(doc_id,)).fetchone()
    if not r:raise HTTPException(404,'Document not found')
    d=store.unseal(r[0])
    return Response(base64.b64decode(d['content']),media_type='application/pdf',headers={'Content-Disposition':"attachment; filename*=UTF-8''"+quote(d['name'],safe=''),'X-Content-Type-Options':'nosniff'})

def document(doc_id):
    with store.connect() as c:
        row=c.execute('SELECT payload FROM equipment_documents WHERE id=?',(doc_id,)).fetchone()
    if not row:raise HTTPException(404,'Document not found')
    return store.unseal(row[0])

@lru_cache(maxsize=16)
def visual_manifest(doc_id,sha256):
    d=document(doc_id)
    pages=[]
    with pymupdf.open(stream=base64.b64decode(d['content']),filetype='pdf') as pdf:
        # Repeated path geometry is usually a logo, footer, rule or page frame.
        def signature(d):
            return (tuple(round(v,1) for v in d['rect']),str(d['items']))
        repeated=Counter()
        for page in pdf:
            repeated.update(set(signature(d) for d in page.get_drawings()))
        for index,page in enumerate(pdf,1):
            text=bool(page.get_text().strip())
            drawings=page.get_drawings()
            images=page.get_image_info()
            area=page.rect.get_area()
            graphics=any((pymupdf.Rect(i['bbox']) & page.rect).get_area()>area*.015 for i in images)
            for drawing in drawings:
                rect=drawing['rect'] & page.rect
                # Ignore tiny outlined letters, thin rules, large frames and recurring decorations.
                if repeated[signature(drawing)]>=3:continue
                if rect.width<24 or rect.height<24 or rect.get_area()>area*.65:continue
                if rect.y1<page.rect.height*.08 or rect.y0>page.rect.height*.92:continue
                graphics=True
                break
            has_content=text or bool(images or drawings or list(page.annots() or []))
            kind='Text + graphics' if text and graphics else 'Text' if text else 'Graphics / scan' if graphics else 'Other page content' if has_content else 'No detected content'
            pages.append({'page':index,'kind':kind,'has_text':text,'has_graphics':graphics,
                          'image_url':f'/api/equipment-documents/{doc_id}/pages/{index}/image'})
    return {'pages':pages,'blank_candidates':[p['page'] for p in pages if p['kind']=='No detected content'],
            'note':'Graphics detection excludes small decorations, repeated vector headers and thin rules. It is heuristic; photos, scans and some tables can qualify. No detected content suggests a blank page.'}

@router.get('/api/equipment-documents/{doc_id}/pages')
def page_manifest(doc_id:str):
    d=document(doc_id)
    return visual_manifest(doc_id,d['sha256'])

@router.get('/api/equipment-documents/{doc_id}/pages/{page_number}/image')
def page_image(doc_id:str,page_number:int):
    d=document(doc_id)
    with pymupdf.open(stream=base64.b64decode(d['content']),filetype='pdf') as pdf:
        if page_number<1 or page_number>len(pdf):raise HTTPException(404,'Page not found')
        page=pdf[page_number-1]
        # Bound memory and retain a legible full-page representation of vector and raster graphics.
        scale=min(2.0,2400/max(page.rect.width,page.rect.height))
        png=page.get_pixmap(matrix=pymupdf.Matrix(scale,scale),alpha=False).tobytes('png')
    return Response(png,media_type='image/png',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})


def retrieve(ship_id,equipment_id,query,documents=None):
    terms=set(re.findall(r'[a-z0-9]{3,}',query.lower()))-{'the','and','what','how','this','that','for','with','does','are','can','you'}
    hits=[]
    for d in (matching(ship_id,equipment_id) if documents is None else documents):
        for page in d['pages']:
            for offset in range(0,len(page['text']),2000):
                excerpt=page['text'][offset:offset+2400]
                score=sum(min(excerpt.lower().count(term),5) for term in terms)
                if score:hits.append((score,{'citation':f"PDF-{d['id']}-p{page['page']}",'source':d['name']+' · page '+str(page['page'])+' · revision '+d['revision'],'title':d['equipment_name'],'excerpt':excerpt,'document_id':d['id'],'page':page['page'],'image_url':f"/api/equipment-documents/{d['id']}/pages/{page['page']}/image",'download_url':'/api/equipment-documents/'+d['id']+'/file'}))
    hits.sort(key=lambda x:x[0],reverse=True)
    return [r for _,r in hits[:5]]


@router.get('/api/ships/{ship_id}/equipment-document-manifest')
def shore_manifest(ship_id:str):
    """Simulated cloud pull eligibility, based only on shore-acknowledged uploads."""
    from .ships import BY_ID
    from .equipment import listing as equipment_listing
    ship=BY_ID.get(ship_id)
    if not ship:raise HTTPException(404,'Unknown ship')
    model_ids={x['id'] for x in equipment_listing(ship_id)}
    documents=[]
    with store.connect() as c:
        receipts=c.execute("SELECT payload FROM receipts WHERE target='shore'").fetchall()
    for row in receipts:
        event=store.unseal(row[0])
        if event.get('kind')!='equipment_document_uploaded':continue
        d=event['document']
        if d['ship_class']!=ship['ship_class'] or d['model_id'] not in model_ids:continue
        if d['scope']=='ship' and d['ship_id']!=ship_id:continue
        documents.append({**public(d),'download_url':'/api/equipment-documents/'+d['id']+'/file'})
    return {'simulation':True,'ship_id':ship_id,'documents':documents,'note':'Local shore-receipt simulation; no external cloud or remote ship is connected.'}
