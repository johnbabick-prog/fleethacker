import json
from pathlib import Path
from fastapi import APIRouter
DATA=json.loads((Path(__file__).resolve().parents[1]/'config/ships.json').read_text())
BY_ID={s['id']:s for s in DATA['ships']}
router=APIRouter()
@router.get('/api/ships')
def directory():return DATA
