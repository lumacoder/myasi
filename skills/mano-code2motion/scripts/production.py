#!/usr/bin/env python3
"""Original, offline scene-contract/FFmpeg pipeline. No generators, downloads or shell commands.
Frame intervals are half-open. Metrics and declared rights are not aesthetic/legal verification.
"""
import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from fractions import Fraction
from pathlib import Path


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON: ' + x)))


def integer(n, name, minimum=0):
    if isinstance(n, bool) or not isinstance(n, int) or n < minimum:
        raise ValueError(name + ': expected integer >= ' + str(minimum))
    return n


def number(n, name, low, high):
    if isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n) or not low <= n <= high:
        raise ValueError(name + ': outside finite range ' + str((low, high)))
    return n


def text(s, name):
    if not isinstance(s, str) or not s.strip() or s.strip().lower().startswith(('replace with', 'todo', 'tbd')) or any(ord(c) < 32 and c != '\n' for c in s):
        raise ValueError(name + ': nonempty plain text required')
    return s


def keys(obj, required, optional=()):
    if not isinstance(obj, dict) or set(required) - set(obj) or set(obj) - set(required) - set(optional):
        raise ValueError('missing/unknown fields: expected ' + str(required) + ', optional ' + str(optional))


def local(root, name):
    if not isinstance(name, str) or not name or ':' in name or '\\' in name:
        raise ValueError('relative local path required')
    p = Path(name)
    root = Path(root).resolve()
    result = (root / p).resolve()
    if any(part.lower() in ('.git', '.ssh', '.aws', 'credentials', 'secrets') or part.lower().startswith('.env') for part in p.parts):
        raise ValueError('credential/configuration path is not a production input')
    if p.is_absolute() or '..' in p.parts or result == root or root not in result.parents:
        raise ValueError('path escapes project: ' + name)
    return result


def rights(value):
    keys(value, ('basis', 'credit', 'evidence'))
    if value['basis'] not in ('original', 'permission', 'public-domain', 'licensed'):
        raise ValueError('unverified rights are blocked; record basis and evidence')
    text(value['credit'], 'credit')
    text(value['evidence'], 'rights evidence')


def validate(p, root):
    keys(p, ('version', 'title', 'fps', 'width', 'height', 'shots'),
         ('captions', 'caption_position', 'tracks', 'landmarks', 'beat_grid', 'notes'))
    if integer(p['version'], 'version', 1) != 1:
        raise ValueError('project version must be 1')
    text(p['title'], 'title')
    if isinstance(p['fps'], bool) or not isinstance(p['fps'], (str, int)):
        raise ValueError('fps must be an integer or rational string (e.g. 30000/1001)')
    try:
        fps = Fraction(p['fps'])
    except (ValueError, ZeroDivisionError):
        raise ValueError('invalid fps')
    if not 1 <= fps <= 120:
        raise ValueError('fps outside 1..120')
    for k in ('width', 'height'):
        integer(p[k], k, 2)
        if p[k] % 2 or p[k] > 7680:
            raise ValueError('even video dimensions <= 7680 required')
    if not isinstance(p['shots'], list) or not p['shots']:
        raise ValueError('at least one shot required')
    ids, end, warnings = set(), 0, []
    for s in p['shots']:
        keys(s, ('id', 'start', 'end', 'clip', 'renderer', 'visual', 'cut_reason', 'identity', 'look', 'rights'),
             ('source_in', 'shortfall', 'risk_frames', 'sources', 'narration', 'notes'))
        if not isinstance(s['id'], str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', s['id']) or s['id'] in ids:
            raise ValueError('unique safe shot ids required')
        ids.add(s['id'])
        if integer(s['start'], 'start') != end or integer(s['end'], 'end', 1) <= end:
            raise ValueError('shots must be positive and contiguous from frame 0')
        length = s['end'] - s['start']
        end = s['end']
        local(root, s['clip'])
        for k in ('renderer', 'visual', 'cut_reason', 'identity', 'look'):
            text(s[k], k)
        rights(s['rights'])
        integer(s.get('source_in', 0), 'source_in')
        if s.get('shortfall', 'reject') not in ('reject', 'hold'):
            raise ValueError('shortfall must be reject or explicitly hold')
        for f in s.get('risk_frames', []):
            if integer(f, 'local risk frame') >= length:
                raise ValueError('risk frame outside shot')
        for name in s.get('sources', []):
            if not local(root, name).is_file():
                raise ValueError('missing declared source: ' + name)
        n = s.get('narration', '')
        if not isinstance(n, str):
            raise ValueError('narration must be text')
        if re.search(r'[\u3400-\u9fff]', n):
            warnings.append(s['id'] + ': CJK speech density needs language-aware timing; no English WPS verdict')
        elif len(n.split()) / float(Fraction(length, 1) / fps) > 2.4:
            warnings.append(s['id'] + ': narration > 2.4 words/s; estimate only, measure recorded speech')
    if p.get('caption_position', 'bottom') not in ('top', 'bottom'):
        raise ValueError('caption_position must be top or bottom')
    for c in p.get('captions', []):
        keys(c, ('start', 'end', 'text'))
        interval(c, end)
        text(c['text'], 'caption')
        if any(x in c['text'] for x in '<>{}\\') or len(c['text'].splitlines()) > 2:
            raise ValueError('captions support <= 2 plain lines, no HTML/ASS markup')
        if max(len(x) for x in c['text'].splitlines()) > 52:
            warnings.append('long caption: inspect actual font width at delivery size')
    caps = sorted(p.get('captions', []), key=lambda c: c['start'])
    if any(a['end'] > b['start'] for a, b in zip(caps, caps[1:])):
        raise ValueError('overlapping captions are not supported')
    for a in p.get('tracks', []):
        keys(a, ('file', 'start', 'end', 'role', 'gain_db', 'rights'), ('source_in', 'fade_in', 'fade_out'))
        interval(a, end)
        local(root, a['file'])
        rights(a['rights'])
        if a['role'] not in ('voice', 'music', 'sfx', 'ambience'):
            raise ValueError('unknown audio role')
        number(a['gain_db'], 'gain_db', -60, 12)
        integer(a.get('source_in', 0), 'source_in')
        for k in ('fade_in', 'fade_out'):
            integer(a.get(k, 0), k)
        if a.get('fade_in', 0) + a.get('fade_out', 0) > a['end'] - a['start']:
            raise ValueError('audio fades exceed cue duration')
    for l in p.get('landmarks', []):
        keys(l, ('frame', 'purpose'))
        if integer(l['frame'], 'landmark') >= end:
            raise ValueError('landmark outside film')
        text(l['purpose'], 'landmark purpose')
    if 'beat_grid' in p:
        g = p['beat_grid']
        keys(g, ('bpm', 'offset_frame', 'subdivision', 'tolerance_frames'))
        number(g['bpm'], 'bpm', 20, 300)
        integer(g['offset_frame'], 'offset_frame')
        integer(g['subdivision'], 'subdivision', 1)
        number(g['tolerance_frames'], 'tolerance_frames', 0, 1)
        step = fps * 60 / Fraction(str(g['bpm'])) / g['subdivision']
        for s in p['shots'][1:]:
            q = Fraction(s['start'] - g['offset_frame'], 1) / step
            if abs(q - round(q)) * step > g['tolerance_frames'] + 1e-9:
                warnings.append(s['id'] + ': cut is off the declared beat grid (not automatically bad editing)')
    return {'frames': end, 'fps': str(fps), 'seconds': float(end / fps), 'warnings': warnings,
            'gates': {'technical': 'not_reviewed', 'readability': 'not_reviewed', 'expression': 'not_reviewed'},
            'rights_note': 'Declarative provenance only; no automated legal verification.'}


def interval(item, end):
    if not 0 <= integer(item['start'], 'start') < integer(item['end'], 'end', 1) <= end:
        raise ValueError('interval outside film')


def seconds(frame, fps):
    return format(float(Fraction(frame, 1) / fps), '.12f')


def run(args):
    r = subprocess.run([str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       encoding='utf8', errors='replace', timeout=600)
    if r.returncode:
        raise ValueError(str(args[0]) + ' failed: ' + r.stderr[-2400:])
    return r


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams',
                           '-show_format', '-of', 'json', path]).stdout)


def stream(info, kind):
    return next((s for s in info['streams'] if s['codec_type'] == kind), None)


def duration(info, kind):
    s = stream(info, kind)
    if not s:
        raise ValueError('missing ' + kind + ' stream')
    return float(s.get('duration', info['format'].get('duration', 'nan')))


def srt(p, fps):
    def stamp(f):
        ms = round(Fraction(f * 1000, 1) / fps)
        return '%02d:%02d:%02d,%03d' % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)
    return '\n\n'.join(str(i + 1) + '\n' + stamp(c['start']) + ' --> ' + stamp(c['end']) + '\n' + c['text']
                        for i, c in enumerate(sorted(p.get('captions', []), key=lambda c: c['start']))) + '\n'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def assemble(p, root, out, burn=False):
    summary = validate(p, root)
    fps, total = Fraction(summary['fps']), summary['frames']
    if burn and not p.get('captions'):
        raise ValueError('--burn-captions requested without captions')
    # Fail before creating output; no silent placeholder, unapproved speed change or narration fallback.
    inputs = []
    for item, kind, name in ([(s, 'video', 'clip') for s in p['shots']] +
                             [(a, 'audio', 'file') for a in p.get('tracks', [])]):
        f = local(root, item[name])
        if not f.is_file():
            raise ValueError('missing required media: ' + item[name])
        info = probe(f)
        have = duration(info, kind)
        needed = float(Fraction(item.get('source_in', 0) + item['end'] - item['start'], 1) / fps)
        if not math.isfinite(have) or have <= float(Fraction(item.get('source_in', 0), 1) / fps):
            raise ValueError('empty/outside source media: ' + item[name])
        if have + 0.00001 < needed and (kind != 'video' or item.get('shortfall', 'reject') != 'hold'):
            raise ValueError('short ' + kind + ': ' + item[name] + '; explicitly redesign timing or permit video hold')
        if have < needed:
            summary['warnings'].append('explicit last-frame hold: ' + item[name])
        inputs.append({'file': item[name], 'sha256': sha(f)})
    out = Path(out).resolve()
    if out.exists() or out == Path(root).resolve() or Path(root).resolve() in out.parents:
        raise ValueError('output must be a NEW directory outside the authored project')
    out.mkdir(parents=True)
    (out / 'captions.srt').write_text(srt(p, fps), encoding='utf8')
    ff = ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y', '-threads', '1']
    with tempfile.TemporaryDirectory(prefix='motion-', dir=str(out)) as work:
        work = Path(work)
        parts = []
        for i, s in enumerate(p['shots']):
            part = work / ('part-%03d.mp4' % i)
            count = s['end'] - s['start']
            vf = ('fps=' + str(fps) + ',scale=' + str(p['width']) + ':' + str(p['height']) +
                  ':force_original_aspect_ratio=decrease,pad=' + str(p['width']) + ':' + str(p['height']) +
                  ':(ow-iw)/2:(oh-ih)/2:color=0x11151c,setsar=1')
            if s.get('shortfall') == 'hold':
                vf += ',tpad=stop_mode=clone:stop_duration=' + seconds(count, fps)
            run(ff + ['-ss', seconds(s.get('source_in', 0), fps), '-i', local(root, s['clip']), '-an',
                      '-vf', vf, '-frames:v', str(count), '-r', str(fps), '-c:v', 'libx264', '-threads', '1',
                      '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p', part])
            parts.append(part)
        # MP4 format durations may be millisecond-rounded; use the frame contract at every splice.
        (work / 'clips.txt').write_text(''.join("file '" + f.name + "'\nduration " +
            seconds(s['end'] - s['start'], fps) + '\n' for f, s in zip(parts, p['shots'])), encoding='utf8')
        silent = work / 'picture.mp4'
        run(ff + ['-f', 'concat', '-safe', '1', '-i', work / 'clips.txt', '-an', '-c:v', 'copy', silent])
        tracks = p.get('tracks', [])
        cmd = ff + ['-i', silent]
        filters, labels = [], []
        for i, a in enumerate(tracks, 1):
            cmd += ['-i', local(root, a['file'])]
            length = a['end'] - a['start']
            filt = ('[' + str(i) + ':a]atrim=start=' + seconds(a.get('source_in', 0), fps) +
                    ':duration=' + seconds(length, fps) + ',asetpts=PTS-STARTPTS,aresample=48000,' +
                    'aformat=sample_fmts=fltp:channel_layouts=stereo,volume=' + str(a['gain_db']) + 'dB')
            if a.get('fade_in'):
                filt += ',afade=t=in:d=' + seconds(a['fade_in'], fps)
            if a.get('fade_out'):
                filt += ',afade=t=out:st=' + seconds(length - a['fade_out'], fps) + ':d=' + seconds(a['fade_out'], fps)
            filt += ',adelay=' + str(round(Fraction(a['start'] * 48000, 1) / fps)) + 'S:all=1[a' + str(i) + ']'
            filters.append(filt)
            labels.append('[a' + str(i) + ']')
        if tracks:
            # Deliberate gains preserved; limiter is a safety net, not a loudness or listening verdict.
            filters.append(''.join(labels) + 'amix=inputs=' + str(len(labels)) +
                           ':normalize=0:duration=longest,apad,atrim=duration=' + seconds(total, fps) +
                           ',alimiter=limit=0.89:level=0:latency=1[mix]')
            cmd += ['-filter_complex', ';'.join(filters), '-map', '0:v:0', '-map', '[mix]', '-c:a', 'aac', '-b:a', '192k']
        else:
            cmd += ['-map', '0:v:0', '-an']
        if burn:
            # Use a local basename under cwd, avoiding Windows drive/filter escaping and arbitrary filter text.
            shutil.copy2(out / 'captions.srt', work / 'captions.srt')
            # Tested force_style values, not assumed ASS-file numpad semantics; pixel regression below is authoritative.
            alignment = '6' if p.get('caption_position') == 'top' else '2'
            cmd += ['-vf', "subtitles=filename=captions.srt:force_style='Alignment=" + alignment + ",FontSize=18,MarginV=28,Outline=1'",
                    '-c:v', 'libx264', '-threads', '1', '-crf', '18', '-pix_fmt', 'yuv420p']
        else:
            cmd += ['-c:v', 'copy']
        cmd += ['-t', seconds(total, fps), '-movflags', '+faststart', out / 'proof.mp4']
        r = subprocess.run([str(x) for x in cmd], cwd=work, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           encoding='utf8', errors='replace', timeout=600)
        if r.returncode:
            raise ValueError('mux failed (output incomplete): ' + r.stderr[-2400:])
    info = probe(out / 'proof.mp4')
    v = stream(info, 'video')
    if not v or int(v.get('nb_read_frames', -1)) != total or (int(v['width']), int(v['height'])) != (p['width'], p['height']) or Fraction(v['avg_frame_rate']) != fps:
        raise ValueError('output frame count/dimensions/rate mismatch: expected ' + str((total, p['width'], p['height'], str(fps))) +
                         '; got ' + str(None if not v else (v.get('nb_read_frames'), v.get('width'), v.get('height'), v.get('avg_frame_rate'))))
    if bool(stream(info, 'audio')) != bool(p.get('tracks')):
        raise ValueError('unexpected output audio presence')
    (out / 'project.json').write_text(json.dumps(p, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    sources = {n: sha(local(root, n)) for s in p['shots'] for n in s.get('sources', [])}
    summary.update(pipeline_sha256=sha(Path(__file__)), inputs=inputs, declared_sources=sources, output_sha256=sha(out / 'proof.mp4'),
                   technical_checks={'decoded_frames': total, 'width': p['width'], 'height': p['height'], 'fps': str(fps)},
                   audio_listened=False, captions_burned=burn, caption_position=p.get('caption_position', 'bottom'), renderers_executed_by_assembler=[],
                   note='External renderers are provenance, not commands. No visual/audio quality pass is inferred.')
    credits = ['# Media provenance (declarations; licences require human review)', '']
    for item in p['shots'] + p.get('tracks', []):
        credits.append('- ' + item.get('clip', item.get('file', '')) + ': ' + json.dumps(item['rights'], ensure_ascii=False))
    (out / 'CREDITS.md').write_text('\n'.join(credits) + '\n', encoding='utf8')
    summary['artifacts'] = {n: sha(out / n) for n in ('proof.mp4', 'project.json', 'captions.srt', 'CREDITS.md')}
    (out / 'assembly.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    return summary


def inspect(p, video, out):
    """Decode the actual output; extract exact frame neighbours, not source-code labels."""
    out = Path(out).resolve()
    if out.exists():
        raise ValueError('inspection output must be new')
    info = probe(video)
    v = stream(info, 'video')
    fps, total = Fraction(p['fps']), p['shots'][-1]['end']
    if not v or int(v.get('nb_read_frames', -1)) != total or Fraction(v['avg_frame_rate']) != fps or (int(v['width']), int(v['height'])) != (p['width'], p['height']):
        raise ValueError('inspection video does not match contract')
    out.mkdir(parents=True)
    frames = {0, total - 1}
    for s in p['shots']:
        frames.add((s['start'] + s['end']) // 2)
        frames.update(s['start'] + f for f in s.get('risk_frames', []))
    for s in p['shots'][1:]:
        frames.update(f for f in (s['start'] - 1, s['start'], s['start'] + 1) if 0 <= f < total)
    rows = []
    for i, f in enumerate(sorted(frames)):
        name = 'frame-%03d.png' % i
        run(['ffmpeg', '-nostdin', '-v', 'error', '-i', video, '-vf', 'select=eq(n\\,' + str(f) +
             '),scale=384:-2', '-frames:v', '1', '-threads', '1', out / name])
        rows.append({'file': name, 'frame': f, 'seconds': float(Fraction(f, 1) / fps)})
    run(['ffmpeg', '-nostdin', '-v', 'error', '-framerate', '1', '-i', str(out / 'frame-%03d.png'),
         '-vf', 'tile=4x' + str(math.ceil(len(rows) / 4)), '-frames:v', '1', '-threads', '1', out / 'sheet.jpg'])
    args = ['ffmpeg', '-nostdin', '-hide_banner', '-xerror', '-i', video, '-vf',
            'blackdetect=d=0.15:pix_th=0.05,freezedetect=n=-55dB:d=0.7']
    if stream(info, 'audio'):
        args += ['-af', 'ebur128=peak=true,silencedetect=noise=-45dB:d=0.3']
    log = run(args + ['-f', 'null', '-']).stderr
    (out / 'decode.log').write_text(log, encoding='utf8')
    deltas = []
    for shot in p['shots'][1:]:
        f = shot['start']
        raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(video), '-vf',
            'select=eq(n\\,' + str(f - 1) + ')+eq(n\\,' + str(f) + '),scale=64:36,format=gray',
            '-vsync', '0', '-threads', '1', '-f', 'rawvideo', '-'], capture_output=True, timeout=600)
        if raw.returncode or len(raw.stdout) != 2 * 64 * 36:
            raise ValueError('could not decode cut-neighbour pixels')
        a, b = raw.stdout[:64 * 36], raw.stdout[64 * 36:]
        deltas.append({'frame': f, 'gray_mean_abs_delta_0_255': sum(abs(x-y) for x, y in zip(a, b)) / len(a),
                       'meaning': 'Measured image change, not proof of a good cut or intended action.'})
    report = {'video_sha256': sha(video), 'frames': rows, 'decoded_frames': total,
              'cut_pixel_deltas': deltas,
              'diagnostic_events': [line.strip() for line in log.splitlines() if re.search(r'black_start|freeze_|silence_|I:|Peak:', line)],
              'interpretation': 'Black/freeze/silence are observations; compare intended holds, cuts and quiet. Not quality gates.',
              'gates': {'technical': 'not_reviewed', 'readability': 'not_reviewed', 'expression': 'not_reviewed'},
              'audio_listened': False, 'video_watched': False}
    (out / 'inspection.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    return report


def package(out, destination):
    """Draft artifact allowlist only; never sweep source trees, credentials or reference pixels."""
    out, destination = Path(out), Path(destination)
    record = load(out / 'assembly.json')
    names = ('proof.mp4', 'project.json', 'assembly.json', 'captions.srt', 'CREDITS.md')
    for name in names:
        f = out / name
        if f.is_symlink() or not f.is_file():
            raise ValueError('missing/linked delivery artifact: ' + name)
        if name != 'assembly.json' and sha(f) != record['artifacts'].get(name):
            raise ValueError('delivery artifact changed: ' + name)
    with zipfile.ZipFile(destination, 'x', zipfile.ZIP_DEFLATED) as z:
        for name in names:
            z.write(out / name, name)
    return {'file': str(destination), 'sha256': sha(destination), 'status': 'draft; independent review still required'}


def doctor():
    tools = {n: shutil.which(n) for n in ('ffmpeg', 'ffprobe', 'node')}
    features = {}
    if tools['ffmpeg']:
        filters = run(['ffmpeg', '-hide_banner', '-filters']).stdout
        encoders = run(['ffmpeg', '-hide_banner', '-encoders']).stdout
        features = {n: n in filters for n in ('subtitles', 'ebur128', 'blackdetect', 'freezedetect')}
        features['libx264'] = 'libx264' in encoders
    return {'tools': tools, 'features': features, 'network_used': False, 'installed': [],
            'note': 'Canvas capture additionally needs local Chrome; no external renderer/provider is installed by this CLI.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('plan', 'assemble', 'inspect'):
        a = sub.add_parser(command)
        a.add_argument('project', type=Path)
        if command != 'plan':
            a.add_argument('--out', required=True, type=Path)
        if command == 'assemble':
            a.add_argument('--burn-captions', action='store_true')
        if command == 'inspect':
            a.add_argument('--video', required=True, type=Path)
    sub.add_parser('doctor')
    a = sub.add_parser('package')
    a.add_argument('assembly', type=Path)
    a.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'doctor':
            result = doctor()
        elif args.command == 'package':
            result = package(args.assembly, args.out)
        else:
            p = load(args.project)
            result = validate(p, args.project.parent)
            if args.command == 'assemble':
                result = assemble(p, args.project.parent, args.out, args.burn_captions)
            elif args.command == 'inspect':
                result = inspect(p, args.video, args.out)
            else:
                result['shots'] = [{'id': s['id'], 'frames': [s['start'], s['end']],
                    'seconds': [float(Fraction(s[k], 1) / Fraction(p['fps'])) for k in ('start', 'end')],
                    'renderer': s['renderer'], 'clip': s['clip'], 'cut_reason': s['cut_reason']}
                    for s in p['shots']]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, subprocess.TimeoutExpired, KeyError, TypeError) as e:
        print('production: ' + str(e), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
