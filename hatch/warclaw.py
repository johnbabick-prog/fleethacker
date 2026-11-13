"""Host the synthetic FleetHacker workspace behind WarClaw app permissions.

Run as hatch.warclaw:app with HATCH_WARCLAW_APP_ID set to the registered
WarClaw app. No browser receives the upstream model credential.
"""
import asyncio
import json
import os
from http.cookies import SimpleCookie, CookieError
from urllib import request as http, error
from urllib.parse import quote

from starlette.responses import JSONResponse

from .app import app as fleet_app

APP_ID = os.environ.get('HATCH_WARCLAW_APP_ID', '')
AUTH_BASE = os.environ.get('HATCH_WARCLAW_AUTH_URL', 'http://127.0.0.1:9000').rstrip('/')
PUBLIC_ORIGIN = os.environ.get('HATCH_WARCLAW_ORIGIN', 'https://warclaw.edgerunnerai.com').rstrip('/')
MAX_BODY = 24 * 1024 * 1024
POLICY = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'self'"


def authorize(cookie):
    """Delegate session validity and app visibility to WarClaw on every request."""
    if not APP_ID:
        return 503, None
    try:
        cookies = SimpleCookie()
        cookies.load(cookie)
        session = cookies.get('er_session')
        if not session:
            return 401, None
        req = http.Request(AUTH_BASE + '/api/apps/' + quote(APP_ID, safe=''),
                           headers={'Cookie': 'er_session=' + session.value})
        with http.urlopen(req, timeout=5) as response:
            record = json.load(response)
        if isinstance(record, dict) and record.get('shared'):
            # App lookup establishes visibility; the sharing API supplies the
            # current permission. Older WarClaw app responses omit this field.
            shares_req = http.Request(AUTH_BASE + '/api/sharing/with-me?resource_type=app',
                                      headers={'Cookie': 'er_session=' + session.value})
            with http.urlopen(shares_req, timeout=5) as response:
                shares = json.load(response).get('shares', [])
            record['permission'] = next((s.get('permission') for s in shares
                                         if s.get('resource_id') == APP_ID and s.get('resource_type') == 'app'), None)
            if record['permission'] not in {'view', 'edit'}:
                return 404, None
        return 200, record
    except error.HTTPError as exc:
        return (exc.code if exc.code in {401, 403, 404} else 503), None
    except CookieError:
        return 401, None
    except (OSError, ValueError):
        return 503, None


class WarClawWorkspace:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        if scope['path'] == '/_warclaw_health':
            return await JSONResponse({'ok': True, 'synthetic_demo': True})(scope, receive, send)
        headers = {k.decode().lower(): v.decode('latin-1') for k, v in scope['headers']}
        status, record = await asyncio.to_thread(authorize, headers.get('cookie', ''))
        if status != 200 or not isinstance(record, dict):
            detail = 'Sign in to WarClaw to open FleetHacker' if status == 401 else 'App not available' if status == 404 else 'Access denied' if status == 403 else 'WarClaw authentication is unavailable'
            return await JSONResponse({'detail': detail}, status_code=status, headers={'Cache-Control':'no-store'})(scope, receive, send)
        if scope['method'] not in {'GET', 'HEAD', 'OPTIONS'}:
            if headers.get('origin', '').rstrip('/') != PUBLIC_ORIGIN:
                return await JSONResponse({'detail': 'Request origin is not permitted'}, status_code=403, headers={'Cache-Control':'no-store'})(scope, receive, send)
            if record.get('shared') and record.get('permission') != 'edit':
                return await JSONResponse({'detail': 'Edit access is required to change this shared workspace'}, status_code=403, headers={'Cache-Control':'no-store'})(scope, receive, send)
        try:
            length = int(headers.get('content-length', '0'))
        except ValueError:
            length = MAX_BODY + 1
        if length < 0 or length > MAX_BODY:
            return await JSONResponse({'detail': 'Request exceeds the 24 MB limit'}, status_code=413, headers={'Cache-Control':'no-store'})(scope, receive, send)
        received = 0
        async def bounded_receive():
            nonlocal received
            message = await receive()
            if message['type'] == 'http.request':
                received += len(message.get('body', b''))
                if received > MAX_BODY:
                    from fastapi import HTTPException
                    raise HTTPException(413, 'Request exceeds the 24 MB limit')
            return message
        async def secured_send(message):
            if message['type'] == 'http.response.start':
                message['headers'] = [(k, v) for k, v in message.get('headers', []) if k.lower() not in {b'cache-control', b'content-security-policy'}]
                message['headers'] += [(b'cache-control', b'no-store'), (b'content-security-policy', POLICY.encode()),
                                       (b'x-content-type-options', b'nosniff'), (b'x-frame-options', b'SAMEORIGIN'),
                                       (b'referrer-policy', b'same-origin')]
            await send(message)
        return await self.app(scope, bounded_receive, secured_send)


app = WarClawWorkspace(fleet_app)
