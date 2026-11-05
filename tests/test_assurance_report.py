"""Evidence presentation must fail closed and safely embed scanner text."""
import contextlib
import io
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import readiness_report as report


class AssuranceReport(unittest.TestCase):
    def generate(self, files):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            out = root / 'security/evidence'
            out.mkdir(parents=True)
            for name, value in files.items():
                (out/name).write_text(json.dumps(value))
            with patch.object(report, 'ROOT', root), patch.object(report, 'OUT', out), contextlib.redirect_stdout(io.StringIO()):
                report.build_report()
            page = (out/'readiness.html').read_text()
            payload = re.search(r'<script id="assurance-data" type="application/json">(.*?)</script>', page, re.S).group(1)
            return json.loads(payload), page

    def test_missing_evidence_never_passes(self):
        data, _ = self.generate({})
        self.assertTrue(data['assessments'])
        self.assertTrue(all(a['state'] == 'unverified' for a in data['assessments']))
        self.assertFalse(data['sourceVerified'])
        self.assertFalse(data['probeVerified'])

    def test_failed_audit_cannot_pass_using_old_clean_report(self):
        data, _ = self.generate({
            'scan-run.json': {'checks': [{'name':'pip-audit','status':'error'}]},
            'pip-audit.json': {'dependencies':[{'name':'example','vulns':[]}]},
        })
        self.assertEqual(next(a for a in data['assessments'] if a['key']=='pip-audit')['state'], 'unverified')

    def test_scanner_text_cannot_terminate_embedded_json(self):
        text = '</script><script>alert("untrusted")</script>'
        data, page = self.generate({
            'scan-run.json': {'checks':[{'name':'bandit','status':'findings'}]},
            'bandit.json': {'results':[{'issue_text':text,'issue_severity':'HIGH'}]},
        })
        self.assertEqual(data['findings'][0]['title'], text)
        self.assertNotIn(text, page)
        self.assertIn('\\u003c/script\\u003e', page)

    def test_historical_source_boolean_without_files_is_not_verified(self):
        data, _ = self.generate({'image-source.json':{'verified':True,'image_files':{}}})
        self.assertFalse(data['sourceVerified'])
