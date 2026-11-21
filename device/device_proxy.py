#!/usr/bin/env python3
"""Expose paired device routes on a private hotspot; keep state on loopback."""
import argparse
import json
import subprocess
import threading
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

MAX_BODY = 200_000

def select_response(path: str, data: dict) -> dict:
    if path == '/session/offer':
        return {key: data.get(key) for key in ('session_id', 'phase', 'offer_id')}
    if path == '/utterance':
        reply = data.get('reply') or {}
        return {'session_id': data.get('session_id'), 'reply': {key: reply.get(key) for key in ('speech', 'offer_id')}}
    handoff = data.get('handoff') or {}
    reply = data.get('reply') or {}
    return {'session_id': data.get('session_id'), 'handoff': {'status': handoff.get('status')}, 'reply': {'speech': reply.get('speech')}}

class Handler(BaseHTTPRequestHandler):
    session = ''
    upstream = 'http://127.0.0.1:8788'
    voice_lock = threading.Lock()
    voice_result = {'status': 'idle'}

    def respond(self, status: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if parse_qs(url.query) != {'session_id': [self.session]}:
            self.respond(404, {'error': 'not found'}); return
        if url.path == '/utterance/result':
            with Handler.voice_lock: result = dict(Handler.voice_result)
            self.respond(200, result); return
        if url.path != '/session/offer':
            self.respond(404, {'error': 'not found'}); return
        self.forward(url.path + '?' + url.query, None, None)

    def do_POST(self) -> None:
        if self.path not in ('/utterance', '/intent'):
            self.respond(404, {'error': 'not found'}); return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_BODY: raise ValueError()
            raw = self.rfile.read(length)
            content_type = self.headers.get('Content-Type', '')
            if self.path == '/utterance' and content_type.lower().startswith('multipart/form-data;'):
                msg = BytesParser(policy=default).parsebytes(('Content-Type: ' + content_type + '\r\nMIME-Version: 1.0\r\n\r\n').encode() + raw)
                parts = [p for p in msg.iter_parts() if p.get_param('name', header='content-disposition') == 'session_id']
                sid = parts[0].get_payload(decode=True).decode() if len(parts) == 1 else ''
            elif self.path == '/intent' and content_type.lower().startswith('application/json'):
                body = json.loads(raw)
                sid = body.get('session_id')
                if body.get('source') != 'button' or body.get('type') != 'buy': raise ValueError()
                if not isinstance(body.get('offer_id'), str) or not body['offer_id']: raise ValueError()
            else:
                raise ValueError()
            if sid != self.session: raise ValueError()
        except (ValueError, KeyError, TypeError, UnicodeError):
            self.respond(400, {'error': 'invalid device request'}); return
        if self.path == '/utterance':
            with Handler.voice_lock:
                if Handler.voice_result.get('status') == 'pending':
                    self.respond(409, {'error': 'voice request in progress'}); return
                Handler.voice_result = {'status': 'pending'}
            threading.Thread(target=self.process_voice, args=(raw, content_type), daemon=True).start()
            self.respond(202, {'status': 'pending'}); return
        with Handler.voice_lock:
            if Handler.voice_result.get('status') == 'pending':
                self.respond(409, {'error': 'voice request in progress'}); return
        self.forward(self.path, raw, content_type)

    def process_voice(self, raw: bytes, content_type: str) -> None:
        req = Request(self.upstream + '/utterance', data=raw, headers={'Content-Type': content_type})
        try:
            with urlopen(req, timeout=120) as response:
                data = json.load(response)
            clean = select_response('/utterance', data)
            speech = (clean.get('reply') or {}).get('speech')
            if isinstance(speech, str) and speech:
                try:
                    subprocess.Popen(['say', speech], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except OSError:
                    pass
            with Handler.voice_lock: Handler.voice_result = {'status': 'complete', 'result': clean}
            print('device POST /utterance complete', flush=True)
        except (HTTPError, URLError, TimeoutError, ValueError, OSError):
            with Handler.voice_lock: Handler.voice_result = {'status': 'failed'}
            print('device POST /utterance failed', flush=True)

    def forward(self, path: str, raw: bytes | None, content_type: str | None) -> None:
        req = Request(self.upstream + path, data=raw, headers={'Content-Type': content_type} if content_type else {})
        try:
            with urlopen(req, timeout=10) as response:
                data = json.load(response)
            clean = select_response(urlparse(path).path, data)
            speech = (clean.get("reply") or {}).get("speech")
            if isinstance(speech, str) and speech:
                try:
                    subprocess.Popen(["say", speech], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except OSError:
                    pass
            print(f"device {self.command} {urlparse(path).path} complete", flush=True)
            self.respond(200, clean)
        except (HTTPError, URLError, TimeoutError, ValueError, OSError):
            print(f"device {self.command} {urlparse(path).path} failed", flush=True)
            self.respond(502, {'error': 'backend unavailable'})

    def log_message(self, fmt: str, *args: object) -> None:
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True, help='Private hotspot address on this Mac')
    parser.add_argument('--port', type=int, default=8790)
    parser.add_argument('--session', required=True)
    args = parser.parse_args()
    Handler.session = args.session
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
