"""Export the bundled comparison, using local Chrome + ffmpeg, no Python packages."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import contextlib
import hashlib
import html
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from motion import ROOT, load, report, state_at, seeded


def find_chrome(explicit=None):
    candidates = [explicit] if explicit else [shutil.which(x) for x in
                  ('google-chrome', 'chromium', 'chromium-browser', 'chrome')]
    if not explicit and sys.platform == 'win32':
        for base in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
            candidates.append(str(Path(os.environ.get(base, '')) / 'Google/Chrome/Application/chrome.exe'))
            candidates.append(str(Path(os.environ.get(base, '')) / 'Microsoft/Edge/Application/msedge.exe'))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise RuntimeError('Chrome/Chromium not found; supply --chrome /path/to/executable')


def run(command, timeout=60):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=timeout, encoding='utf8', errors='replace')
    if result.returncode:
        raise RuntimeError('Command failed (%d): %s\n%s' %
                           (result.returncode, command[0], result.stderr[-4000:]))
    return result.stdout


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextlib.contextmanager
def serve(directory):
    def handler(*args, **kwargs):
        return QuietHandler(*args, directory=str(directory), **kwargs)
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield 'http://127.0.0.1:%d' % server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def chrome_call(chrome, url, screenshot=None, width=1280, height=720):
    with tempfile.TemporaryDirectory(prefix='code2motion-chrome-') as profile:
        cmd = [chrome, '--headless=new', '--disable-gpu', '--disable-dev-shm-usage',
               '--disable-background-networking', '--disable-extensions', '--no-first-run',
               '--no-default-browser-check', '--hide-scrollbars', '--force-device-scale-factor=1',
               '--user-data-dir=' + profile, '--window-size=%d,%d' % (width, height),
               '--virtual-time-budget=1200', '--run-all-compositor-stages-before-draw']
        if hasattr(os, 'geteuid') and os.geteuid() == 0:
            cmd.append('--no-sandbox')  # root-only container compatibility; normal desktops keep sandbox
        cmd.append('--screenshot=' + str(screenshot) if screenshot else '--dump-dom')
        cmd.append(url)
        return run(cmd, timeout=45)


def browser_test(chrome, base, spec):
    dom = chrome_call(chrome, base + '/index.html?selftest=1')
    match = re.search(r'<pre id="selftest"[^>]*>(.*?)</pre>', dom, re.S)
    if not match:
        raise RuntimeError('Browser did not return selftest result')
    result = json.loads(html.unescape(match.group(1)))
    if result.get('status') != 'PASS':
        raise RuntimeError('Browser selftest failed: ' + str(result))
    # Validate JS/Python numerical parity instead of testing only duplicated formulas in isolation.
    for sample in result['samples']:
        expected = state_at(spec, sample['t'])
        for ident in expected:
            for prop in ('x_px', 'y_px', 'scale', 'rotation_rad', 'opacity'):
                if abs(expected[ident][prop] - sample['state'][ident][prop]) > 1e-7:
                    raise RuntimeError('Python/JS state mismatch')
    if abs(result['seed'] - seeded(spec['seed'], 31)) > 1e-15:
        raise RuntimeError('Python/JS seed hash mismatch')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, help='New directory outside this repository; no overwrite')
    parser.add_argument('--chrome')
    parser.add_argument('--workers', type=int, default=2, choices=range(1, 5))
    parser.add_argument('--check-only', action='store_true', help='Only run browser seek/parity checks')
    args = parser.parse_args()
    try:
        spec = load(ROOT / 'examples/compare.json')
        chrome = find_chrome(args.chrome)
        out = Path(args.out).resolve()
        # Avoid generated files in any containing repository, not merely in the skill.
        for ancestor in (out,) + tuple(out.parents):
            if (ancestor / '.git').exists() or ancestor == ROOT:
                raise ValueError('--out must be outside the skill and any repository')
        if out.exists():
            raise ValueError('Output exists; choose a new directory (no overwrite)')
        for command in (() if args.check_only else ('ffmpeg', 'ffprobe')):
            if not shutil.which(command):
                raise RuntimeError(command + ' not found on PATH')
        out.mkdir(parents=True)
        with tempfile.TemporaryDirectory(prefix='code2motion-site-') as site_name:
            site = Path(site_name)
            for name in ('index.html', 'motion.js', 'compare.json'):
                shutil.copyfile(ROOT / 'examples' / name, site / name)
            with serve(site) as base:
                result = browser_test(chrome, base, spec)
                (out / 'browser-test.json').write_text(json.dumps(result, indent=2), encoding='utf8')
                if args.check_only:
                    print('Browser seek/pixel and Python-JS parity: PASS')
                    return 0
                frames = out / 'frames'
                frames.mkdir()
                count = round(spec['duration_s'] * spec['fps'])
                def frame(i):
                    path = frames / ('%06d.png' % i)
                    chrome_call(chrome, base + '/index.html?capture=1&time=%.12f' % (i/spec['fps']), path,
                                spec['canvas']['width_px'], spec['canvas']['height_px'])
                    if not path.exists() or path.stat().st_size < 1000:
                        raise RuntimeError('Missing/empty frame %d' % i)
                    return i
                with ThreadPoolExecutor(max_workers=args.workers) as executor:
                    for done, _ in enumerate(executor.map(frame, range(count)), 1):
                        if done % 12 == 0 or done == count:
                            print('Frames %d/%d' % (done, count), flush=True)
        for label, i in (('first', 0), ('middle', count//2), ('last', count-1)):
            shutil.copyfile(frames / ('%06d.png' % i), out / (label + '.png'))
        hashes = [hashlib.sha256((out / (name + '.png')).read_bytes()).hexdigest()
                  for name in ('first', 'middle', 'last')]
        if len(set(hashes)) < 3:
            raise RuntimeError('First/middle/last PNGs unexpectedly identical')
        run(['ffmpeg', '-v', 'error', '-framerate', str(spec['fps']), '-i', str(frames / '%06d.png'),
             '-frames:v', str(count), '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
             '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', str(out / 'compare.mp4')], 180)
        metadata = json.loads(run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams',
                                  '-show_format', '-of', 'json', str(out / 'compare.mp4')]))
        video = [s for s in metadata['streams'] if s['codec_type'] == 'video']
        if len(video) != 1 or any(s['codec_type'] == 'audio' for s in metadata['streams']):
            raise RuntimeError('Unexpected video/audio streams')
        stream = video[0]
        if (int(stream['nb_read_frames']) != count or stream['width'] != spec['canvas']['width_px']
                or stream['height'] != spec['canvas']['height_px']
                or stream['avg_frame_rate'] != '%d/1' % spec['fps']
                or abs(float(metadata['format']['duration'])-spec['duration_s']) > 1/spec['fps']):
            raise RuntimeError('Encoded frame count, dimensions, rate or duration mismatch')
        measurement = report(spec)
        measurement['versions'] = {'chrome': run([chrome, '--version']).strip(),
                                   'ffmpeg': run(['ffmpeg', '-version']).splitlines()[0]}
        measurement['preview_sha256'] = dict(zip(('first', 'middle', 'last'), hashes))
        (out / 'ffprobe.json').write_text(json.dumps(metadata, indent=2), encoding='utf8')
        (out / 'sampling-report.json').write_text(json.dumps(measurement, indent=2), encoding='utf8')
        print('Export verified: %s (%d frames, silent)' % (out / 'compare.mp4', count))
        return 0
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print('Export failed; partial output retained for diagnosis: %s' % exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
