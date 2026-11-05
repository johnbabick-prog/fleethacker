"""Replaceable class-level demo equipment and ship-scoped inventory."""
import json
from pathlib import Path
from fastapi import APIRouter,HTTPException
from . import store
from .ships import BY_ID
CATALOG=json.loads((Path(__file__).resolve().parents[1]/'config/demo_equipment.json').read_text())
router=APIRouter()
with store.connect() as c:
    c.execute('CREATE TABLE IF NOT EXISTS demo_equipment_stock(ship_id TEXT, part_id TEXT, on_hand INTEGER, reserved INTEGER, snapshot TEXT, PRIMARY KEY(ship_id,part_id))')
    for ship in BY_ID.values():
        for item in CATALOG['items']:
            if ship['ship_class']==item['ship_class'] and item['scenario']!='unknown':
                on_hand,reserved=(5,1) if item['scenario']=='ready' else (2,1)
                c.execute('INSERT OR IGNORE INTO demo_equipment_stock VALUES (?,?,?,?,?)',(ship['id'],item['demo_part_id'],on_hand,reserved,store.now()))

def listing(ship_id):
    ship=BY_ID.get(ship_id)
    if not ship:raise HTTPException(404,'Select a valid ship first')
    output=[]
    with store.connect() as c:
        for template in CATALOG['items']:
            if template['ship_class']!=ship['ship_class']:continue
            row=c.execute('SELECT * FROM demo_equipment_stock WHERE ship_id=? AND part_id=?',(ship_id,template['demo_part_id'])).fetchone()
            available=max(0,row['on_hand']-row['reserved']) if row else None
            output.append({**template,'equipment_id':ship_id+'::'+template['id'],'ship_id':ship_id,'inventory':{'part_id':template['demo_part_id'],'name':template['demo_part_name'],'required':template['demo_required'],'on_hand':row['on_hand'] if row else None,'reserved':row['reserved'] if row else None,'available':available,'snapshot':row['snapshot'] if row else None,'assessment':'Unknown' if available is None else 'Ready' if available>=template['demo_required'] else 'Short','shortage':None if available is None else max(0,template['demo_required']-available),'basis':'Test requirements and stock levels for demonstration.'}})
    return output

def resolve(ship_id,equipment_id):
    item=next((x for x in listing(ship_id) if x['equipment_id']==equipment_id),None)
    if not item:raise HTTPException(422,'Equipment does not belong to the selected demo ship register')
    return item
@router.get('/api/ships/{ship_id}/equipment')
def equipment(ship_id:str):return {'items':listing(ship_id),'scope':CATALOG['scope']}
