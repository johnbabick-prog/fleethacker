import unittest
from hatch.model_output import final_answer,NO_ANSWER
class ModelOutput(unittest.TestCase):
 def test_reasoning_and_final_channels(self):
  self.assertEqual(final_answer('<|channel>thought\nprivate notes'),NO_ANSWER)
  self.assertEqual(final_answer('<|channel>thought\nprivate notes<|channel>final\nCheck the tag.'),'Check the tag.')
  self.assertEqual(final_answer('<|channel|>analysis\nprivate<|channel|>final\nReady.'),'Ready.')
  self.assertEqual(final_answer('<think>private</think>Check the tag.'),'Check the tag.')
  self.assertEqual(final_answer('<think>unfinished'),NO_ANSWER)
  self.assertEqual(final_answer('Check the tag.'),'Check the tag.')
 def test_gemma4_closed_thought_block_preserves_only_final_answer(self):
  self.assertEqual(final_answer('<|channel>thought\n<channel|>Ready.'),'Ready.')
  self.assertEqual(final_answer('<|channel>thought\nprivate notes<channel|>Check the tag.<turn|>'),'Check the tag.')
  self.assertEqual(final_answer('<|channel>thought\nprivate notes<channel|>'),NO_ANSWER)
  self.assertEqual(final_answer('<|channel>thought\nprivate notes'),NO_ANSWER)
 def test_useful_grounded_fallback(self):
  from hatch.model_output import record_fallback
  answer=record_fallback({'active_step':{'number':1,'total':12,'instruction':'Confirm the equipment identity.'},'lessons':[{'id':'LESSON-1','kind':'observation','text':'Similar names caused a wrong-unit selection.'}]})
  self.assertIn('Confirm the equipment identity.',answer)
  self.assertIn('Recorded lesson',answer)
  self.assertIn('AI explanation unavailable',answer)
