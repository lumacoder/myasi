#!/usr/bin/env python3
"""Build this original 6s proof using existing local Chrome/FFmpeg only. No downloads/providers."""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import wave

CASE = Path(__file__).resolve().parent
SKILL = CASE.parents[1]


def contact_wav(path):
    """Analytic demonstration tone; not a real recording or a general-purpose foley model."""
    rate, duration = 48000, 1.5
    path.parent.mkdir(parents=True)
    with wave.open(str(path), 'wb') as f:
        f.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
        pcm = bytearray()
        for i in range(round(duration * rate)):
            t = i / rate
            envelope = (1 - math.exp(-t / .002)) * math.exp(-t * 5)
            tone = sum(a * math.sin(2 * math.pi * hz * t) for a, hz in ((.23, 196), (.1, 311), (.055, 529)))
            pcm.extend(struct.pack('<h', round(32767 * envelope * tone)))
        f.writeframes(pcm)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--chrome')
    p.add_argument('--workers', type=int, choices=(1, 2, 3, 4), default=2)
    a = p.parse_args()
    out = a.out.resolve()
    if out.exists() or SKILL == out or SKILL in out.parents or any((d / '.git').exists() for d in (out,) + tuple(out.parents)):
        p.error('use a NEW output directory outside the skill/repository')
    for tool in ('ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            p.error(tool + ' is required; nothing is installed automatically')
    out.mkdir(parents=True)
    authored = out / 'authored'
    shutil.copytree(CASE, authored, ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(SKILL / 'runtime/scene-kit.js', authored / 'shared/scene-kit.js')
    contact_wav(authored / 'assets/contact.wav')
    project = json.loads((authored / 'project.template.json').read_text(encoding='utf8'))
    manifest = authored / 'project.json'
    manifest.write_text(json.dumps(project, indent=2) + '\n', encoding='utf8')
    (authored / 'clips').mkdir()
    for shot in project['shots']:
        dest = out / ('capture-' + shot['id'])
        cmd = [sys.executable, str(SKILL / 'scripts/render_project.py'), str(authored), '--entry',
               shot['id'] + '/index.html', '--duration', str((shot['end'] - shot['start']) / project['fps']),
               '--fps', str(project['fps']), '--width', str(project['width']), '--height', str(project['height']),
               '--workers', str(a.workers), '--out', str(dest)]
        if a.chrome:
            cmd += ['--chrome', a.chrome]
        subprocess.run(cmd, check=True, timeout=600)
        shutil.copy2(dest / 'film.mp4', authored / shot['clip'])
    pipeline = SKILL / 'scripts/production.py'
    for args in (['plan', str(manifest)], ['assemble', str(manifest), '--out', str(out / 'assembly'), '--burn-captions'],
                 ['inspect', str(manifest), '--video', str(out / 'assembly/proof.mp4'), '--out', str(out / 'inspection')],
                 ['package', str(out / 'assembly'), '--out', str(out / 'draft-proof.zip')]):
        label = args[0]
        with (out / (label + '.log')).open('w', encoding='utf8') as log:
            subprocess.run([sys.executable, str(pipeline)] + args, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)
    print('Proof built; visual/audio review NOT performed: ' + str(out / 'assembly/proof.mp4'))


if __name__ == '__main__':
    main()
