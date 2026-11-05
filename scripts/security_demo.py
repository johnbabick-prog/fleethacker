"""Build, scan, probe and render evidence. Exit 1 means review findings; 2 means an error."""
import argparse
import collections
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'security/evidence'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', default='fleet-tech:security-demo')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    stages = []
    commands = [
        ('build', ['docker','build','-t',args.image,'.'], (0,)),
        ('smoke', [sys.executable,'scripts/container_smoke.py',args.image], (0,)),
        ('scan', [sys.executable,'scripts/security_scan.py','--image',args.image], (0,)),
        ('http-probes', [sys.executable,'scripts/security_probe.py','--image',args.image], (0,1)),
        ('report', [sys.executable,'scripts/readiness_report.py'], (0,)),
    ]
    for name, command, allowed in commands:
        print(f'Running {name} ...', flush=True)
        try:
            with (OUT/('demo-'+name+'.log')).open('w') as log:
                result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=1800)
            state = 'completed' if result.returncode in allowed else 'error'
            stages.append({'name':name,'status':state,'exit_code':result.returncode})
        except (OSError, subprocess.SubprocessError) as exc:
            stages.append({'name':name,'status':'error','error':str(exc)})
        # A failed build must never cause a scan of an old image with the same tag.
        if name == 'build' and stages[-1]['status'] == 'error':
            break
    summary = {'generated_at':datetime.now(timezone.utc).isoformat(), 'image':args.image,
               'stages':stages, 'status':'error'}
    if not any(s['status']=='error' for s in stages):
        try:
            def read(name):
                return json.loads((OUT/name).read_text())
            image = read('trivy-image.json')
            vulnerabilities = [v for r in image.get('Results',[]) for v in r.get('Vulnerabilities',[])]
            counts = collections.Counter(v.get('Severity','UNKNOWN') for v in vulnerabilities)
            bandit = read('bandit.json')['results']
            probes = read('http-probes.json')
            scan = read('scan-run.json')
            source = read('image-source.json')
            findings = [c for c in probes['checks'] if c['status']=='finding']
            summary.update(image_id=scan['versions']['image'], image_findings=dict(counts),
                           bandit_findings=len(bandit), http_checks=len(probes['checks']),
                           http_findings=len(findings))
            if (probes['status'] == 'error' or probes['image_id'] != summary['image_id']
                    or not source.get('verified')):
                raise ValueError('Probe/image/source evidence did not match')
            needs_review = (counts['HIGH'] or counts['CRITICAL'] or findings
                            or any(r['issue_severity'] in ('MEDIUM','HIGH') for r in bandit)
                            or any(c['status']=='findings' for c in scan['checks']))
            summary['status'] = 'findings' if needs_review else 'passed_tested_gates'
        except (OSError, ValueError, KeyError) as exc:
            summary['error'] = str(exc)
    (OUT/'security-demo.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    print('Open security/evidence/readiness.html or /security/readiness in the app.')
    return 2 if summary['status']=='error' else 1 if summary['status']=='findings' else 0


if __name__ == '__main__':
    raise SystemExit(main())
