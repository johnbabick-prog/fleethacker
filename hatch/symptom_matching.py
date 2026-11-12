"""Conservative symptom matching; equipment names alone never establish relevance."""
import re
STOP=set('the and this that with from have has was were for what when does not are you our any past reports report problem issue system unit equipment teller fortis remote should could would please help fix fixed turn wont cant dont didnt will can did do how now still again on off it my a an to of in is at be no'.split())
CATEGORIES={
 'loss of power':r'\b(no power|power loss|loss of power|power failure|not powering|without power|dead unit|dead system|(?:won t|wont|will not|does not|doesn t|doesnt|can t|cant|cannot|not) (?:turn on|power on|power up|switch on|start up|energize))\b',
 'door movement':r'\bdoor\b.*\b(jam\w*|stuck|obstruct\w*|won t open|wont open|not open|doesn t open|will not open|won t close|wont close|not close|doesn t close|will not close|not mov\w*)\b|\b(jam\w*|stuck|obstruct\w*)\b.*\bdoor\b',
 'leakage':r'\b(leak\w*|seep\w*|dripping)\b',
 'loss of cooling':r'\b(not cooling|no cooling|won t cool|wont cool|doesn t cool|overheat\w*|running hot)\b',
 'restricted airflow':r'\b(no airflow|low airflow|restricted airflow|blocked filter|clogged filter)\b',
 'loss of water flow':r'\b(no water flow|no water comes|not dispensing|won t dispense|wont dispense|low water flow)\b',
 'abnormal noise':r'\b(rattl\w*|grinding|squeal\w*|unusual noise|abnormal noise)\b',
}
def normalize(text):return re.sub(r'[^a-z0-9]+',' ',text.lower()).strip()
def signals(text,equipment=''):
    value=normalize(text)
    categories={name for name,pattern in CATEGORIES.items() if re.search(pattern,value)}
    codes=set(re.findall(r'\b[a-z]{1,3}\d{2,6}\b',value))-set(re.findall(r'\b[a-z]{1,3}\d{2,6}\b',normalize(equipment)))
    terms={word for word in value.split() if len(word)>2 and word not in STOP}-set(normalize(equipment).split())
    return categories,codes,terms

def match(query,symptom,equipment=''):
    if not query.strip() or not symptom.strip():return 0,''
    qcats,qcodes,qterms=signals(query,equipment);rcats,rcodes,rterms=signals(symptom,equipment)
    if qcats and rcats and not qcats & rcats:return 0,''
    if qcodes and rcodes and not qcodes & rcodes:return 0,''
    if qcodes & rcodes:return 10+len(qcodes & rcodes),'Same reported fault code: '+', '.join(sorted(qcodes & rcodes)).upper()
    if qcats & rcats:return 6+len(qterms & rterms),'Matching reported symptom: '+', '.join(sorted(qcats & rcats))
    # Shared generic words or an equipment label are insufficient. Require
    # two specific symptom terms unless a fault code/category matched above.
    shared=qterms & rterms
    if len(shared)<2:return 0,''
    return len(shared),'Shared symptom details: '+', '.join(sorted(shared))
