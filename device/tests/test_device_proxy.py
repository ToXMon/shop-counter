"""Exercise the private device proxy without live checkout or audio files."""
import json
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location('device_proxy', Path(__file__).resolve().parents[1] / 'device_proxy.py')
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)

class FakeBackend(BaseHTTPRequestHandler):
    last_body = None
    hold_voice = threading.Event()
    voice_started = threading.Event()
    hold_voice.set()
    def do_GET(self):
        self.reply({'session_id': 's_test', 'phase': 'pick', 'offer_id': 'offer-a', 'continue_url': 'private-canary'})
    def do_POST(self):
        raw = self.rfile.read(int(self.headers['Content-Length']))
        type(self).last_body = json.loads(raw) if self.path == '/intent' else raw
        if self.path == '/utterance':
            self.voice_started.set()
            self.hold_voice.wait(5)
        self.reply({'session_id': 's_test', 'handoff': {'status': 'ready', 'continue_url': 'private-canary'}, 'reply': {'speech': '', 'audio_b64': 'private-canary'}})
    def reply(self, data):
        raw = json.dumps(data).encode(); self.send_response(200); self.send_header('Content-Length', str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def log_message(self, *args): pass

class ProxyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backend = ThreadingHTTPServer(('127.0.0.1', 0), FakeBackend)
        proxy.Handler.upstream = f'http://127.0.0.1:{cls.backend.server_port}'
        proxy.Handler.session = 's_test'
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), proxy.Handler)
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'
        for server in (cls.backend, cls.server): threading.Thread(target=server.serve_forever, daemon=True).start()
    @classmethod
    def tearDownClass(cls):
        for server in (cls.server, cls.backend): server.shutdown(); server.server_close()
    def test_device_pairing_strips_private_fields(self):
        with urllib.request.urlopen(self.base + '/session/offer?session_id=s_test') as r: response = json.load(r)
        self.assertEqual(response, {'session_id': 's_test', 'phase': 'pick', 'offer_id': 'offer-a'})
        with self.assertRaises(urllib.error.HTTPError) as raised: urllib.request.urlopen(self.base + '/state')
        raised.exception.close()
        with self.assertRaises(urllib.error.HTTPError) as raised: urllib.request.urlopen(self.base + '/session/offer?session_id=other')
        raised.exception.close()
    def test_audio_is_bound_to_the_session_and_response_is_filtered(self):
        raw = (b'--test\r\nContent-Disposition: form-data; name="session_id"\r\n\r\ns_test\r\n'
               b'--test\r\nContent-Disposition: form-data; name="audio"; filename="a.wav"\r\n'
               b'Content-Type: audio/wav\r\n\r\nFAKE\r\n--test--\r\n')
        request = urllib.request.Request(self.base + '/utterance', data=raw, headers={'Content-Type': 'multipart/form-data; boundary=test'})
        with urllib.request.urlopen(request) as r:
            self.assertEqual(r.status, 202)
        for _ in range(30):
            with urllib.request.urlopen(self.base + '/utterance/result?session_id=s_test') as r: result = json.load(r)
            if result['status'] != 'pending': break
            time.sleep(0.05)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(FakeBackend.last_body, raw)
        self.assertNotIn('private-canary', json.dumps(result))
        request = urllib.request.Request(self.base + '/utterance', data=raw.replace(b's_test', b'other'), headers={'Content-Type': 'multipart/form-data; boundary=test'})
        with self.assertRaises(urllib.error.HTTPError) as raised: urllib.request.urlopen(request)
        raised.exception.close()
    def test_inflight_voice_blocks_intent(self):
        FakeBackend.voice_started.clear()
        FakeBackend.hold_voice.clear()
        raw = (b'--test\r\nContent-Disposition: form-data; name="session_id"\r\n\r\ns_test\r\n--test--\r\n')
        request = urllib.request.Request(self.base + '/utterance', data=raw, headers={'Content-Type': 'multipart/form-data; boundary=test'})
        try:
            with urllib.request.urlopen(request) as r: self.assertEqual(r.status, 202)
            self.assertTrue(FakeBackend.voice_started.wait(2))
            body = {'session_id': 's_test', 'type': 'buy', 'source': 'button', 'offer_id': 'offer-a'}
            request = urllib.request.Request(self.base + '/intent', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
            with self.assertRaises(urllib.error.HTTPError) as raised: urllib.request.urlopen(request)
            self.assertEqual(raised.exception.code, 409)
            raised.exception.close()
        finally:
            FakeBackend.hold_voice.set()
    def test_button_intent_preserves_offer_and_strips_checkout(self):
        body = {'session_id': 's_test', 'type': 'buy', 'source': 'button', 'offer_id': 'offer-a'}
        request = urllib.request.Request(self.base + '/intent', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request) as r: result = json.load(r)
        self.assertEqual(FakeBackend.last_body, body)
        self.assertEqual(result['handoff'], {'status': 'ready'})
        self.assertNotIn('private-canary', json.dumps(result))
        body['source'] = 'badge'
        request = urllib.request.Request(self.base + '/intent', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
        with self.assertRaises(urllib.error.HTTPError) as raised: urllib.request.urlopen(request)
        raised.exception.close()

if __name__ == '__main__': unittest.main()
