"""Populate only synthetic references in the separate team-review database."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hatch import store
store.init()
modules=[
 ('demo-record-review','DEMO · Maintenance record review',[
  'Synthetic workflow for product evaluation. This is not an aircraft maintenance instruction.',
  'Review the selected demonstration work order. Confirm the displayed demo asset and describe the reported discrepancy in your notes.',
  'Review the synthetic supply snapshot and its timestamp. Record any missing information rather than assuming availability.',
  'Attach a synthetic handwritten record, capture the demonstration meter reading, and save the administrative completion.']),
 ('demo-document-checkout','DEMO · Handwritten log checkout',[
  'Synthetic document-handling workflow. Use invented information for team testing.',
  'Select a demonstration work order and inspect the log you intend to attach.',
  'Upload a synthetic PDF, PNG or JPEG. Download the stored original and confirm it matches your upload.',
  'Record any confusing interface behavior as a technician observation. OCR remains pending in this prototype.']),
 ('demo-supply-reconciliation','DEMO · Supply snapshot reconciliation',[
  'Synthetic administrative exercise; no real part numbers or maintenance instructions are included.',
  'Review the demonstration catalog quantities and reservations.',
  'Record discrepancies in session notes. The historical snapshot does not guarantee present availability.',
  'Save your progress and demonstrate the simulated ship and shore synchronization.'])]
with store.connect() as c:
    c.execute('DELETE FROM corpus')
    for source,title,sections in modules:
        text='\n\n'.join(sections)
        c.execute('INSERT INTO corpus VALUES (?,?,?)',(source,title,text))
print('Shared review database ready: synthetic references only.')
