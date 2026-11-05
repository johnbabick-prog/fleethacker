"""Instant, local step reminders from training history."""
import json
from pathlib import Path
from . import store
from .experience import for_sailor
DATA=json.loads((Path(__file__).resolve().parents[1]/'config/demo_performance.json').read_text())
def history(source,revision,sailor,step):
    records=[r for r in DATA['records'] if r['source']==source]
    return {'completed_exercises':sum(r['kind']=='completion' and r['sailor']==sailor for r in records),
            'lessons':[r for r in records if r['kind']=='observation' and r['step']==step],
            'corrections':[r for r in records if r['kind']=='correction' and r['step']==step and r['sailor']==sailor]}
def briefing(source,step,sailor):
    p=store.procedure(source)
    if not 0<=step<len(p['sections']):raise ValueError('Invalid step')
    demo=history(source,p['revision_hash'],sailor,step)
    real=[r for r in store.lessons(source) if r.get('step') in (None,step) and r.get('revision_hash',p['revision_hash'])==p['revision_hash']]
    corrections=[r for r in real if r.get('kind')=='correction' and r.get('sailor')==sailor and r.get('step')==step]
    return {'source':source,'step':step,'sailor':sailor,'instruction':p['sections'][step], 'profile':for_sailor(sailor),
            'demo_history':demo,'lessons':demo['lessons']+[r for r in real if r.get('kind')!='correction'],
            'corrections':demo['corrections']+corrections,'mode':'Local record-based reminders'}
