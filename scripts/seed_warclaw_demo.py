"""Associate untouched synthetic watch records with a demo ship; never reset data."""
import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
if os.environ.get('HATCH_SHARED_DEMO')!='1':
    raise SystemExit('Requires the explicitly configured synthetic demo environment')
from hatch import store,workspace,demo_watch
from hatch.ships import BY_ID
ship=BY_ID['DDG-51']
count=0
for row in workspace.watch():
    job=row['job'];draft=row['draft'];schedule=row['schedule'] or {}
    if not job['id'].startswith('DEMO-') or draft.get('version',0)!=0:
        continue
    equipment={'Electrical':'spy1','Mechanical':'lm2500','SONAR':'sqq89'}.get(schedule.get('work_center'))
    if not equipment:continue
    workspace.save_draft(job['id'],workspace.Draft(
        version=0,ship_id=ship['id'],equipment_id=ship['id']+'::'+equipment,
        owner=schedule.get('assignee',''),location='Synthetic demo workspace',
        notes='Invented maintenance exercise for product demonstration; not an operational record.'))
    count+=1
print('Associated untouched synthetic watch records:',count)
