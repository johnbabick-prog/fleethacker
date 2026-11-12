import os,tempfile,unittest
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from unittest.mock import patch
from hatch.symptom_matching import match
from hatch.troubleshooting import similar_records

class SymptomMatching(unittest.TestCase):
 def test_no_power_is_not_door_obstruction(self):
  equipment='Fortis 5000 DS remote teller system'
  query='The system wont turn on'
  door='The door on the teller system wont open what should I do?'
  self.assertEqual(match(query,door,equipment)[0],0)
  self.assertGreater(match(query,'Teller unit has no power',equipment)[0],0)
  self.assertGreater(match("The door won't open",door,equipment)[0],0)
  self.assertEqual(match('There is a problem with the system',door,equipment)[0],0)
  self.assertEqual(match('E101 fault','E102 fault',equipment)[0],0)
  self.assertGreater(match('E101 fault','Interface code E101',equipment)[0],0)
 def test_matching_uses_problem_not_unrelated_repair_text(self):
  rows=[{'id':'jam','job_id':'old-jam','draft_version':1,'equipment_id':'DDG-76::water-cooler','equipment':'Fortis 5000 DS remote teller system','symptom':'The door wont open','actions_taken':'Switched power off and removed a rock','outcome':'Unit can turn on and door opens','resolution_status':'resolved'}, {'id':'power','job_id':'old-power','draft_version':1,'equipment_id':'DDG-76::water-cooler','equipment':'Fortis 5000 DS remote teller system','symptom':'No power to teller unit','actions_taken':'Recorded supply fault','outcome':'Follow-up needed','resolution_status':'unresolved'}]
  with patch('hatch.troubleshooting.records',return_value=rows):
   found=similar_records('Arleigh Burke (DDG)','The system wont turn on','DDG-76::water-cooler')
  self.assertEqual([r['id'] for r in found],['power'])
  self.assertIn('loss of power',found[0]['match_reason'])
 def test_all_distinct_fixes_remain_visible(self):
  rows=[{'id':str(i),'job_id':'same-job','draft_version':1,'equipment_id':'DDG-76::water-cooler','equipment':'Teller system','symptom':'The door is jammed','actions_taken':'Removed rock' if i==0 else 'Released safety latch','outcome':'Door opens','resolution_status':'resolved'} for i in range(12)]
  with patch('hatch.troubleshooting.records',return_value=rows):
   found=similar_records('Arleigh Burke (DDG)','The door is jammed','DDG-76::water-cooler')
  self.assertEqual(len(found),12)
  self.assertEqual({r['id'] for r in found},{str(i) for i in range(12)})
