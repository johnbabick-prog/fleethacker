"""Resolve a local inference endpoint at launch, then start HATCH."""
import json
import os
import sys
import urllib.request
from urllib.parse import urlparse


def resolve():
    override = os.environ.get('HATCH_LLM_URL')
    candidates = [override] if override else [
        f'http://127.0.0.1:{port}/v1/chat/completions'
        for port in (18080, 8080, 8000, 8002, 8003, 8001)
    ]
    requested = os.environ.get('HATCH_MODEL')
    for endpoint in candidates:
        if urlparse(endpoint).hostname not in ('127.0.0.1', 'localhost', '::1'):
            print('Skipping non-loopback AI endpoint', file=sys.stderr)
            continue
        models_url = endpoint.rsplit('/chat/completions', 1)[0] + '/models'
        try:
            with urllib.request.urlopen(models_url, timeout=3) as response:
                ids = [m['id'] for m in json.load(response).get('data', []) if isinstance(m.get('id'), str)]
            if not ids:
                continue
            if requested and requested not in ids:
                print(f'{models_url}: requested model {requested!r} is not advertised', file=sys.stderr)
                continue
            ids = [m for m in ids if 'embed' not in m.lower()]
            if not ids:
                continue
            model = requested or next((m for m in ids if 'combat' in m.lower()), next((m for m in ids if 'thinking' not in m.lower()), ids[0]))
            return endpoint, model
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(f'Local AI probe {models_url}: {error}', file=sys.stderr)
    return None


def main():
    result = resolve()
    if result:
        endpoint, model = result
        os.environ['HATCH_LLM_URL'] = endpoint
        os.environ['HATCH_MODEL'] = model
        print(f'HATCH local AI endpoint: {endpoint}\nHATCH model: {model}', flush=True)
    else:
        print('No compatible local model API found. HATCH will start in evidence-only mode. '
              'Start/load a model in Garrison, then restart HATCH.', file=sys.stderr, flush=True)
    os.execv(sys.executable, [sys.executable, '-m', 'uvicorn', 'hatch.app:app',
                            '--host', os.environ.get('HATCH_HOST', '127.0.0.1'),
                            '--port', os.environ.get('HATCH_PORT', '8765')])


if __name__ == '__main__':
    main()
