import os,tempfile,unittest
os.environ.setdefault('HATCH_DATA',tempfile.mkdtemp(prefix='hatch-hosting-test-'))
from unittest.mock import patch
from starlette.testclient import TestClient
from hatch import warclaw

class HostingTests(unittest.TestCase):
 def setUp(self):
  self.client=TestClient(warclaw.app)
 def test_unauthenticated_and_unshared_requests_are_denied(self):
  for status in [401,403,404,503]:
   with patch.object(warclaw,'authorize',return_value=(status,None)):
    r=self.client.get('/api/state');self.assertEqual(r.status_code,status);self.assertNotIn('jobs',r.json())
 def test_owner_and_shared_read_access(self):
  for record in [{},{'shared':True,'permission':'view'}]:
   with patch.object(warclaw,'authorize',return_value=(200,record)):
    r=self.client.get('/api/state');self.assertEqual(r.status_code,200)
    self.assertEqual(r.headers['cache-control'],'no-store')
 def test_origin_and_edit_permissions_protect_mutations(self):
  with patch.object(warclaw,'authorize',return_value=(200,{})):
   self.assertEqual(self.client.post('/api/sync',json={'target':'ship'}).status_code,403)
   self.assertEqual(self.client.post('/api/sync',json={'target':'ship'},headers={'Origin':'https://evil.example'}).status_code,403)
   self.assertEqual(self.client.post('/api/sync',json={'target':'ship'},headers={'Origin':warclaw.PUBLIC_ORIGIN}).status_code,200)
  with patch.object(warclaw,'authorize',return_value=(200,{'shared':True,'permission':'view'})):
   self.assertEqual(self.client.post('/api/sync',json={'target':'ship'},headers={'Origin':warclaw.PUBLIC_ORIGIN}).status_code,403)
 def test_bounded_uploads(self):
  with patch.object(warclaw,'authorize',return_value=(200,{})):
   self.assertEqual(self.client.post('/api/sync',content=b'{}',headers={'Origin':warclaw.PUBLIC_ORIGIN,'Content-Length':str(warclaw.MAX_BODY+1)}).status_code,413)
 def test_health_does_not_expose_workspace_data(self):
  self.assertEqual(self.client.get('/_warclaw_health').json(),{'ok':True,'synthetic_demo':True})
 def test_only_session_cookie_is_delegated_to_warclaw(self):
  with patch.object(warclaw,'APP_ID','app-test'),patch.object(warclaw.http,'urlopen') as call:
   import io
   call.return_value=io.BytesIO(b'{}');call.return_value.status=200
   self.assertEqual(warclaw.authorize('other=private; er_session=verified-session')[0],200)
   req=call.call_args.args[0]
   self.assertEqual(req.get_header('Cookie'),'er_session=verified-session')

 def test_shared_permission_is_rechecked_using_warclaw_sharing_api(self):
  import io
  for permission in ['view','edit',None]:
   def response(req,**kwargs):
    value={'shared':True} if '/api/apps/' in req.full_url else {'shares':([] if permission is None else [{'resource_type':'app','resource_id':'app-test','permission':permission}])}
    import json
    r=io.BytesIO(json.dumps(value).encode());r.status=200;return r
   with patch.object(warclaw,'APP_ID','app-test'),patch.object(warclaw.http,'urlopen',side_effect=response):
    status,record=warclaw.authorize('er_session=valid')
    self.assertEqual(status,404 if permission is None else 200)
    if record:self.assertEqual(record['permission'],permission)
