"""Local, network-disabled app smoke test. Never mounts the user's data directory."""
import json, subprocess, sys, time, uuid
from pathlib import Path
from datetime import datetime, timezone
image=sys.argv[1] if len(sys.argv)>1 else 'fleet-tech:demo'
name='fleet-smoke-'+uuid.uuid4().hex[:8]
out=Path('security/evidence');out.mkdir(parents=True,exist_ok=True)
def run(*args):return subprocess.run(args,check=True,capture_output=True,text=True).stdout
started=time.monotonic()
record={'tested_at':datetime.now(timezone.utc).isoformat(),'image':image,'network_mode':'none','scope':'Application only; no inference server/model or fleet sync transport tested','status':'error'}
try:
    record['image_id']=run('docker','image','inspect',image,'--format','{{.Id}}').strip()
    run('docker','run','--detach','--name',name,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,noexec,nosuid,size=64m','--tmpfs','/data:rw,noexec,nosuid,size=256m,uid=10001,gid=10001',image)
    for _ in range(60):
        health=subprocess.run(['docker','exec',name,'python','-c',"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/healthz',timeout=1)"],capture_output=True)
        if health.returncode==0:break
        time.sleep(.25)
    else:raise RuntimeError('Container health check timed out')
    record['startup_seconds']=round(time.monotonic()-started,3)
    check="""import urllib.request,json,os
from hatch import store
assert os.getuid()==10001
body=json.dumps({'version':1,'note':'Disconnected deployment smoke test'}).encode()
r=urllib.request.Request('http://127.0.0.1:8765/api/jobs/WO-001/complete',body,{'Content-Type':'application/json'})
event=json.load(urllib.request.urlopen(r))['event_id']
with store.connect() as c:
 raw=c.execute('SELECT payload FROM events WHERE id=?',(event,)).fetchone()[0]
 assert 'Disconnected deployment smoke test' not in raw
 assert store.unseal(raw)['job']['meter'] is None
 assert store.unseal(raw)['job']['status']=='Completed locally'
assert oct(os.stat(store.KEY).st_mode & 0o777)=='0o600'
try:
 open('/app/should-not-write','w')
 raise AssertionError('Root filesystem was writable')
except OSError:pass
print(json.dumps({'non_root':True,'root_filesystem_read_only':True,'completion_saved':True,'event_payload_encrypted':True,'device_key_mode':'0600','meter_optional':True}))
"""
    record['checks']=json.loads(run('docker','exec',name,'python','-c',check))
    record['status']='passed'
except Exception as e:
    record['error']=str(e)
finally:
    subprocess.run(['docker','rm','--force',name],capture_output=True)
    (out/'container-smoke.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
if record['status']!='passed':sys.exit(1)
