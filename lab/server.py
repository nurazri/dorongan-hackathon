"""Loopback-only Angular app, chunked tracking API and seekable local video."""
import argparse
import json
import mimetypes
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def create_handler():
    summary = json.loads((ROOT/'.local/summary.json').read_text(encoding='utf-8'))
    tracking = np.load(ROOT/'.local/tracking.npz')
    xy, teams, nearest = tracking['xy'], tracking['teams'], tracking['nearest']
    evidence = {key: tracking[key] for key in ('control_candidate', 'stoppage_evidence', 'restart_evidence', 'restart_context', 'motion_speed')}
    tracking.close()
    videos = json.loads((ROOT/'local_paths.json').read_text(encoding='utf-8'))
    web = ROOT/'ui/dist/interface/browser'

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(web), **kwargs)

        def log_message(self, fmt, *args):
            if args and '/media/' not in str(args[0]):
                super().log_message(fmt, *args)

        def json_response(self, obj):
            data = json.dumps(obj, allow_nan=False).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.headers.get('Host', '').split(':')[0] not in ('127.0.0.1', 'localhost'):
                return self.send_error(403, 'Local host required')
            parsed = urlparse(self.path)
            try:
                if parsed.path == '/api/summary':
                    return self.json_response(summary)
                if parsed.path == '/api/window':
                    frame = max(0, min(summary['frames']-1, int(parse_qs(parsed.query).get('frame', ['0'])[0])))
                    start, end = max(0, frame-125), min(summary['frames'], frame+500)
                    rows = []
                    for i in range(start, end):
                        players = [{'x': float(p[0]), 'y': float(p[1]), 'team': int(teams[j]), 'slot': j+1}
                                   for j,p in enumerate(xy[i,:-1]) if np.isfinite(p).all()]
                        ball = xy[i,-1]
                        rows.append({'players': players,
                                     'ball': [float(v) for v in ball] if np.isfinite(ball).all() else None,
                                     'nearest': [float(v) if np.isfinite(v) else None for v in nearest[i]],
                                     'control': {
                                         'candidate': 'HA'[int(evidence['control_candidate'][i])] if evidence['control_candidate'][i] >= 0 else None,
                                         'motionSpeed': float(evidence['motion_speed'][i]) if np.isfinite(evidence['motion_speed'][i]) else None,
                                         'deadCue': {1:'Sustained outside pitch',2:'Settled far from players',3:'Settled in restart context'}.get(int(evidence['stoppage_evidence'][i])),
                                         'restartContext': bool(evidence['restart_context'][i]),
                                         'restartMotion': bool(evidence['restart_evidence'][i]),
                                     }})
                    return self.json_response({'start': start, 'end': end, 'rows': rows})
                if parsed.path == '/api/export':
                    name = parse_qs(parsed.query).get('model', [''])[0]
                    if name not in summary['models']:
                        return self.send_error(404)
                    return self.send_file(ROOT/'evaluation/results'/f'{name}.csv', attachment=True, download_name='dorongan.csv' if name == 'experimental_control_v5' else None)
                if parsed.path == '/media/tactical.mp4':
                    return self.send_file(Path(videos['BAR-ATH_tactical.mp4']))
                if parsed.path.startswith('/api/') or parsed.path.startswith('/media/'):
                    return self.send_error(404)
                return super().do_GET()
            except (ValueError, IndexError):
                self.send_error(400, 'Invalid request')
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

        def do_HEAD(self):
            if self.headers.get('Host', '').split(':')[0] not in ('127.0.0.1', 'localhost'):
                return self.send_error(403, 'Local host required')
            if urlparse(self.path).path == '/media/tactical.mp4':
                return self.send_file(Path(videos['BAR-ATH_tactical.mp4']), head=True)
            return super().do_HEAD()

        def end_headers(self):
            self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
            self.send_header('X-Content-Type-Options', 'nosniff')
            super().end_headers()

        def send_file(self, path, attachment=False, head=False, download_name=None):
            size = path.stat().st_size
            start, end = 0, size-1
            range_header = self.headers.get('Range')
            if range_header:
                match = re.fullmatch(r'bytes=(\d*)-(\d*)', range_header)
                if not match or not any(match.groups()):
                    return self.send_error(416)
                left, right = match.groups()
                if left:
                    start = int(left)
                    end = min(int(right), end) if right else end
                else:
                    start = max(0, size-int(right))
                if start >= size or end < start:
                    self.send_response(416)
                    self.send_header('Content-Range', f'bytes */{size}')
                    self.end_headers()
                    return
            self.send_response(206 if range_header else 200)
            self.send_header('Content-Type', mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Length', str(end-start+1))
            self.send_header('Cache-Control', 'no-store')
            if range_header:
                self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            if attachment:
                self.send_header('Content-Disposition', f'attachment; filename="{download_name or path.name}"')
            self.end_headers()
            if head:
                return
            with path.open('rb') as stream:
                stream.seek(start)
                remaining = end-start+1
                while remaining:
                    chunk = stream.read(min(1024*1024, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
    return Handler

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), create_handler())
    print(f'Possession Lab: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
