import os,tempfile,unittest
from unittest.mock import patch
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-test-'))
from fastapi.testclient import TestClient
from hatch.app import app
class DeploymentEvidence(unittest.TestCase):
 def test_health_and_missing_evidence_are_explicit(self):
  c=TestClient(app)
  self.assertEqual(c.get('/healthz').json(),{'status':'ok'})
  with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'HATCH_SECURITY_EVIDENCE':d}):
   response=c.get('/security/readiness')
   self.assertEqual(response.status_code,503)
   self.assertIn('No readiness claim',response.text)
 def test_evidence_report_is_served_without_caching(self):
  from pathlib import Path
  c=TestClient(app)
  with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,{'HATCH_SECURITY_EVIDENCE':d}):
   Path(d,'readiness.html').write_text('<h1>Evidence fixture</h1>')
   response=c.get('/security/readiness')
   self.assertEqual(response.status_code,200)
   self.assertEqual(response.headers['cache-control'],'no-store')
