"""Build the self-contained product assurance center from recorded local evidence."""
import collections
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'security/evidence'
TEMPLATE = ROOT / 'security/templates/assurance.html'


def read(name):
    try:
        value = json.loads((OUT / name).read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def build_report():
    OUT.mkdir(parents=True, exist_ok=True)
    run = read('scan-run.json')
    smoke = read('container-smoke.json')
    probes = read('http-probes.json')
    source = read('image-source.json')
    image_id = run.get('versions', {}).get('image', '')
    manifest = {c['name']: c for c in run.get('checks', [])}
    assessments = []
    artifacts = []

    def assessment(title, key, filename, detail, valid, clean, category):
        check = manifest.get(key, {})
        verified = check.get('status') in ('completed', 'findings') and valid
        state = 'passed' if verified and clean else 'review' if verified else 'unverified'
        item = dict(title=title, key=key, artifact=filename, detail=detail, state=state,
                    category=category, seconds=check.get('seconds'))
        assessments.append(item)
        return item

    bandit = read('bandit.json')
    bandit_counts = dict(collections.Counter(r.get('issue_severity', 'UNKNOWN') for r in bandit.get('results', [])))
    assessment('Static application analysis', 'bandit', 'bandit.json',
               f"{len(bandit.get('results', []))} code findings for engineering review", isinstance(bandit.get('results'), list),
               not bandit.get('results'), 'Application')
    pip = read('pip-audit.json')
    pip_count = sum(len(d.get('vulns', [])) for d in pip.get('dependencies', []))
    assessment('Python dependency audit', 'pip-audit', 'pip-audit.json',
               f'{pip_count} advisories across {len(pip.get("dependencies", []))} locked dependencies',
               isinstance(pip.get('dependencies'), list), pip_count == 0, 'Supply chain')
    npm = read('npm-audit.json').get('metadata', {}).get('vulnerabilities', {})
    assessment('JavaScript dependency audit', 'npm-audit', 'npm-audit.json',
               f'{npm.get("total", "Unknown")} advisories in UI test dependencies', 'total' in npm, npm.get('total') == 0, 'Supply chain')
    config = read('trivy-source.json')
    misconfig = [v for r in config.get('Results', []) for v in r.get('Misconfigurations', [])]
    secrets = [v for r in config.get('Results', []) for v in r.get('Secrets', [])]
    assessment('Configuration & secret detection', 'trivy-source', 'trivy-source.json',
               f'{len(misconfig)} configuration findings · {len(secrets)} potential secrets', bool(config.get('SchemaVersion')),
               not misconfig and not secrets, 'Configuration')
    image = read('trivy-image.json')
    vulns = [dict(id=v.get('VulnerabilityID'), package=v.get('PkgName'), installed=v.get('InstalledVersion'),
                  fixed=v.get('FixedVersion') or 'No fix reported', severity=v.get('Severity', 'UNKNOWN'),
                  title=v.get('Title') or v.get('VulnerabilityID'), category='Container', target=r.get('Target'))
             for r in image.get('Results', []) for v in r.get('Vulnerabilities', [])]
    severities = dict(collections.Counter(v['severity'] for v in vulns))
    assessment('Container vulnerability scan', 'trivy-image', 'trivy-image.json',
               f'{len(vulns)} package/advisory findings · {severities.get("HIGH", 0)} high · {severities.get("CRITICAL", 0)} critical',
               bool(image.get('SchemaVersion')), not vulns, 'Container')
    sbom = read('sbom.cdx.json')
    assessment('Software bill of materials', 'sbom', 'sbom.cdx.json',
               f'{len(sbom.get("components", []))} inventoried components · CycloneDX', bool(sbom.get('bomFormat')),
               bool(sbom.get('components')), 'Supply chain')
    assessment('Deployment chart validation', 'helm-lint', 'helm-lint.log',
               'Helm lint completed; cluster admission and UDS deployment remain untested', (OUT/'helm-lint.log').is_file(),
               manifest.get('helm-lint', {}).get('status') == 'completed', 'Configuration')
    test_log = (OUT/'python-tests.log').read_text() if (OUT/'python-tests.log').exists() else ''
    executed = re.search(r'Ran (\d+) tests?', test_log)
    assessment('Application regression suite', 'python-tests', 'python-tests.log',
               f'{executed.group(1) if executed else "Unknown number of"} regression tests executed', bool(executed),
               manifest.get('python-tests', {}).get('status') == 'completed', 'Application')
    smoke_valid = bool(image_id) and smoke.get('image_id') == image_id and bool(smoke.get('checks'))
    smoke_ok = smoke_valid and smoke.get('status') == 'passed' and all(smoke['checks'].values())
    assessments.append(dict(title='Isolated runtime hardening', key='runtime', artifact='container-smoke.json',
                            detail=f'{smoke.get("startup_seconds", "Unknown")}s to healthy · non-root · read-only root · network disabled',
                            state='passed' if smoke_ok else 'unverified', category='Runtime'))
    probe_script = ROOT/'scripts/security_probe.py'
    probe_valid = (bool(image_id) and probes.get('image_id') == image_id and probe_script.is_file()
                   and probes.get('probe_sha256') == hashlib.sha256(probe_script.read_bytes()).hexdigest()
                   and probes.get('status') in ('passed', 'findings') and bool(probes.get('checks')))
    probe_checks = probes.get('checks', []) if probe_valid else []
    probe_findings = [c for c in probe_checks if c.get('status') == 'finding']
    assessments.append(dict(title='Live HTTP security probes', key='http-probes', artifact='http-probes.json',
                            detail=f'{len(probe_checks)} bounded checks · {len(probe_findings)} findings · disposable data',
                            state=('review' if probe_findings else 'passed') if probe_valid else 'unverified', category='Application'))
    source_files = source.get('image_files', {})
    source_valid = bool(source_files) and source.get('verified') and all(
        (ROOT/path).is_file() and hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest
        for path, digest in source_files.items())
    findings = [dict(id=f'HTTP-{i+1:02}', title=c['name'], severity=c['severity'], category='HTTP probes',
                     package='Application API', installed='', fixed=c['remediation'], evidence=c['evidence'])
                for i, c in enumerate(probe_findings)]
    findings += [dict(id=r.get('test_id'), title=r.get('issue_text'), severity=r.get('issue_severity'),
                      category='Static analysis', package=r.get('filename'), installed='',
                      fixed='Review the code path and document its disposition.',
                      evidence={'line':r.get('line_number'), 'confidence':r.get('issue_confidence')})
                 for r in bandit.get('results', []) if manifest.get('bandit', {}).get('status') in ('completed', 'findings')]
    if manifest.get('trivy-image', {}).get('status') in ('completed', 'findings'):
        findings += vulns
    artifact_specs = [
        ('scan-run.json', 'Scan manifest', {'image_id':image_id, 'versions':run.get('versions'), 'database':run.get('trivy_database'), 'checks':run.get('checks')}),
        ('sbom.cdx.json', 'Software inventory', {'format':sbom.get('bomFormat'), 'components':len(sbom.get('components', []))}),
        ('trivy-image.json', 'Container CVE report', {'severity_counts':severities, 'package_advisory_findings':len(vulns), 'unique_advisories':len({v['id'] for v in vulns})}),
        ('http-probes.json', 'HTTP probe report', {'status':probes.get('status'), 'checks':probe_checks, 'limitations':probes.get('limitations')}),
        ('container-smoke.json', 'Runtime hardening report', smoke),
        ('bandit.json', 'Static analysis report', {'severity_counts':bandit_counts, 'findings':len(bandit.get('results', []))}),
        ('pip-audit.json', 'Python dependency report', {'advisories':pip_count, 'dependencies':len(pip.get('dependencies', []))}),
        ('npm-audit.json', 'JavaScript dependency report', {'advisories':npm}),
        ('trivy-source.json', 'Configuration & secret report', {'configuration_findings':len(misconfig), 'potential_secrets':len(secrets), 'scope':'Source/config; uploads, databases and secret match content excluded from this page.'}),
        ('image-source.json', 'Source correspondence', {'verified_at_scan':source.get('verified'), 'current_application_files_match':bool(source_valid), 'files_checked':len(source_files)}),
        ('helm-lint.log', 'Deployment lint log', {'status':manifest.get('helm-lint', {}).get('status')}),
        ('python-tests.log', 'Regression test log', {'executed_tests':int(executed.group(1)) if executed else None, 'status':manifest.get('python-tests', {}).get('status')}),
    ]
    for filename, title, summary in artifact_specs:
        path = OUT/filename
        if path.is_file():
            artifacts.append(dict(filename=filename, title=title, bytes=path.stat().st_size,
                                  sha256=hashlib.sha256(path.read_bytes()).hexdigest(), summary=summary))
    hashes = {f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in OUT.iterdir()
              if f.suffix in ('.json', '.yaml', '.log') and f.name != 'checksums.json'}
    (OUT/'checksums.json').write_text(json.dumps(hashes, indent=2)+'\n')
    model = dict(product='Fleet Tech', generatedAt=run.get('generated_at'),
                 renderedAt=datetime.now(timezone.utc).isoformat(), image=run.get('image'), imageId=image_id,
                 sourceFingerprint=run.get('source_fingerprint'), sourceVerified=bool(source_valid),
                 assessments=assessments, findings=findings, imageSeverities=severities,
                 probeChecks=probe_checks, probeVerified=probe_valid, probeLimitations=probes.get('limitations', []),
                 smoke=smoke if smoke_valid else {}, artifacts=artifacts, database=run.get('trivy_database', {}),
                 banditCounts=bandit_counts, regressionTests=int(executed.group(1)) if executed else None)
    # Escape HTML/script terminators even if a scanner includes hostile package or finding text.
    payload = json.dumps(model, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    page = TEMPLATE.read_text().replace('__ASSURANCE_DATA__', payload)
    (OUT/'readiness.html').write_text(page)
    print(OUT/'readiness.html')


if __name__ == '__main__':
    build_report()
