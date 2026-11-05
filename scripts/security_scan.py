"""Generate real local evidence. Missing tools/errors are recorded, never a pass."""
import argparse, hashlib, json, subprocess, time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--image',default='fleet-tech:demo');args=p.parse_args()
out=ROOT/'security/evidence';out.mkdir(parents=True,exist_ok=True)
for stale in ('scan-run.json','image-source.json'):(out/stale).unlink(missing_ok=True)
cache=out/'trivy-cache';cache.mkdir(exist_ok=True)
trivy='aquasec/trivy@sha256:790fd66d1697395d8693d1acaa1ea702406a20f109b6fc7bac8db623eca6c06c'
checks=[]
def check(name,command,report=None,findings_exit=None):
    start=time.monotonic()
    if report:(out/report).unlink(missing_ok=True)
    try:
        r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=600)
        (out/(name+'.log')).write_text(r.stdout+'\n'+r.stderr)
        if report and r.stdout.strip() and name in ('npm-audit','pip-audit'):(out/report).write_text(r.stdout)
        state='completed' if r.returncode==0 else 'findings' if r.returncode==findings_exit else 'error'
        checks.append({'name':name,'command':command,'status':state,'exit_code':r.returncode,'seconds':round(time.monotonic()-start,2),'report':report})
    except (OSError,subprocess.TimeoutExpired) as e:checks.append({'name':name,'command':command,'status':'error','error':str(e),'report':report})
check('bandit',[str(ROOT/'.security-venv/bin/bandit'),'-r','hatch','scripts/launch.py','-f','json','-o',str(out/'bandit.json')],'bandit.json',1)
check('pip-audit',[str(ROOT/'.security-venv/bin/pip-audit'),'-r','requirements.lock','--no-deps','--disable-pip','--format','json'],'pip-audit.json',1)
check('npm-audit',['npm','audit','--json'],'npm-audit.json',1)
check('trivy-source',['docker','run','--rm','-v',str(ROOT)+':/work:ro','-v',str(out)+':/out','-v',str(cache)+':/root/.cache/trivy',trivy,'fs','--scanners','misconfig,secret','--skip-dirs','/work/data,/work/node_modules,/work/.security-venv,/work/security','--format','json','--output','/out/trivy-source.json','/work'],'trivy-source.json')
check('sbom',['syft','docker:'+args.image,'-o','cyclonedx-json='+str(out/'sbom.cdx.json')],'sbom.cdx.json')
check('image-export',['docker','save','-o',str(out/'image.tar'),args.image])
if checks[-1]['status']=='completed':
    check('trivy-image',['docker','run','--rm','-v',str(out)+':/out','-v',str(cache)+':/root/.cache/trivy',trivy,'image','--input','/out/image.tar','--scanners','vuln','--format','json','--output','/out/trivy-image.json'],'trivy-image.json')
check('helm-lint',['helm','lint','deploy/chart'])
check('python-tests',['python3','-m','unittest','discover','-s','tests','-q'])
versions={}
for name,cmd in [('bandit',[str(ROOT/'.security-venv/bin/bandit'),'--version']),('pip-audit',[str(ROOT/'.security-venv/bin/pip-audit'),'--version']),('syft',['syft','version']),('trivy',['docker','run','--rm',trivy,'--version']),('image',['docker','image','inspect',args.image,'--format','{{.Id}}'])]:
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=60);versions[name]=r.stdout.strip() or r.stderr.strip()
    except (OSError,subprocess.TimeoutExpired) as e:versions[name]='ERROR: '+str(e)
files={}
for pattern in ['hatch/*.py','static/*','config/*.json','deploy/**/*','scripts/*.py','requirements*','Dockerfile','.dockerignore','package*.json']:
    for f in ROOT.glob(pattern):
        if f.is_file() and f.name!='security-readiness.html':files[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
image_sources={}
code="import pathlib,hashlib,json; print(json.dumps({str(p.relative_to('/app')):hashlib.sha256(p.read_bytes()).hexdigest() for pattern in ['hatch/*.py','static/*','config/*.json','requirements.lock'] for p in pathlib.Path('/app').glob(pattern) if p.is_file()}))"
r=subprocess.run(['docker','run','--rm','--network','none','--read-only','--entrypoint','python',args.image,'-c',code],capture_output=True,text=True)
try:image_sources=json.loads(r.stdout)
except ValueError:pass
differences=[name for name,h in image_sources.items() if files.get(name)!=h]
(out/'image-source.json').write_text(json.dumps({'image_files':image_sources,'host_differences':differences,'verified':bool(image_sources) and not differences},indent=2)+'\n')
manifest={'generated_at':datetime.now(timezone.utc).isoformat(),'image':args.image,'versions':versions,'checks':checks,'source_files_sha256':files,'source_fingerprint':hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()}
try:manifest['trivy_database']=json.loads((cache/'db/metadata.json').read_text())
except (OSError,ValueError):manifest['trivy_database']={'status':'not recorded'}
(out/'scan-run.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps([{'name':c['name'],'status':c['status']} for c in checks],indent=2))
if any(c['status']=='error' for c in checks):raise SystemExit(2)
