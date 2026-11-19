"""Contract tests + tiny real FFmpeg fixtures. Not evidence of creative quality."""
import array
import copy
import importlib.util
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
import wave
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('motion_production', ROOT / 'scripts/production.py')
production = importlib.util.module_from_spec(spec)
spec.loader.exec_module(production)


def project():
    rights = dict(basis='original', credit='Synthetic test fixture', evidence='Generated locally by this test, no external assets.')
    return dict(version=1, title='Contract fixture', fps=24, width=64, height=36, shots=[
        dict(id=name, start=a, end=b, clip=name + '.mp4', renderer='media', visual='Flat colour test fixture',
             cut_reason='Test exact frame order, not a creative film', identity='fixture', look='flat', rights=copy.deepcopy(rights))
        for name, a, b in (('red', 0, 4), ('blue', 4, 8))])


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.p = project()

    def tearDown(self):
        self.tmp.cleanup()

    def test_case_review_cannot_promote_unheard_audio_or_rename_subject(self):
        review = production.load(ROOT / 'examples/contact-resonance/review-status.json')
        self.assertEqual(review['independent_review']['action_causality'], 'pass')
        self.assertIn('not_reviewed', review['independent_review']['audio_audition'])
        self.assertEqual(review['delivery_gate']['status'], 'blocked')
        self.assertEqual({v['status'] for v in review['gates'].values()}, {'partial'})
        self.assertIn('drum', review['independent_review']['intended_drum_identity'])
        self.assertIn('incomplete', review['preserved_prior_results'])

    def test_valid_has_no_visual_pass(self):
        before = copy.deepcopy(self.p)
        result = production.validate(self.p, self.root)
        self.assertEqual(result['frames'], 8)
        self.assertEqual(set(result['gates'].values()), {'not_reviewed'})
        self.assertEqual(self.p, before)

    def test_source_coverage_all_entrypoints_are_scoped(self):
        audit = production.load(ROOT / 'references/video-studio-kit.audit.json')
        self.assertEqual(len(audit['coverage']), 52)
        self.assertEqual(len({x['skill'] for x in audit['coverage']}), 52)
        self.assertIsNone(audit['licensing']['root_LICENSE'])
        for row in audit['coverage']:
            self.assertIn(audit['commit'], row['url'])
            self.assertFalse(row['upstream_executed'])
            self.assertIn(row['family'], audit['capability_families'])
            for path in audit['capability_families'][row['family']]['landing']:
                self.assertTrue((ROOT / path).is_file(), path)

    def test_unfilled_project_template_is_not_a_valid_rights_declaration(self):
        template = production.load(ROOT / 'templates/production-project.json')
        with self.assertRaises(ValueError):
            production.validate(template, self.root)

    def test_frame_gap_overlap_and_bool(self):
        for value in (3, 5, True, 4.1):
            p = copy.deepcopy(self.p)
            p['shots'][1]['start'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                production.validate(p, self.root)

    def test_unsafe_paths_and_sensitive_inputs(self):
        for name in ('../x.mp4', '/tmp/x.mp4', 'C:/x.mp4', 'https://x/y', 'a\\b.mp4', '.env', '.git/config', 'secrets/a.json'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                production.local(self.root, name)

    def test_duplicate_ids(self):
        self.p['shots'][1]['id'] = 'red'
        with self.assertRaises(ValueError):
            production.validate(self.p, self.root)

    def test_unknown_command_and_quality_fields_rejected(self):
        for field in ('command', 'shell', 'quality_pass'):
            p = copy.deepcopy(self.p)
            p['shots'][0][field] = 'should never execute'
            with self.subTest(field=field), self.assertRaises(ValueError):
                production.validate(p, self.root)

    def test_unknown_rights_blocked(self):
        self.p['shots'][0]['rights']['basis'] = 'unverified'
        with self.assertRaises(ValueError):
            production.validate(self.p, self.root)

    def test_no_media_placeholder(self):
        del self.p['shots'][0]['clip']
        with self.assertRaises(ValueError):
            production.validate(self.p, self.root)

    def test_odd_dimensions_and_noninteger_version(self):
        for key, value in (('width', 63), ('height', True), ('version', 1.0)):
            p = copy.deepcopy(self.p)
            p[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                production.validate(p, self.root)

    def test_rational_rate_and_srt_are_not_rounded_to_30(self):
        self.p['fps'] = '30000/1001'
        self.p['shots'] = [self.p['shots'][0]]
        self.p['shots'][0]['end'] = 60
        self.p['captions'] = [dict(start=30, end=60, text='Exact boundary')]
        self.assertEqual(production.validate(self.p, self.root)['fps'], '30000/1001')
        self.assertIn('00:00:01,001 --> 00:00:02,002', production.srt(self.p, production.Fraction(self.p['fps'])))

    def test_nonfinite_and_bool_rate(self):
        for value in (True, 0, 0.5, 'nan', '1/0', 121):
            p = copy.deepcopy(self.p)
            p['fps'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                production.validate(p, self.root)

    def test_duplicate_and_nonfinite_json(self):
        for content in ('{"a":1,"a":2}', '{"a":NaN}'):
            path = self.root / 'input.json'
            path.write_text(content)
            with self.assertRaises(ValueError):
                production.load(path)

    def test_caption_overlap_and_markup(self):
        for caps in ([dict(start=0, end=5, text='A'), dict(start=4, end=7, text='B')],
                     [dict(start=0, end=4, text='{unsafe}')], [dict(start=0, end=9, text='Outside')]):
            self.p['captions'] = caps
            with self.subTest(caps=caps), self.assertRaises(ValueError):
                production.validate(self.p, self.root)

    def test_caption_position_is_an_enum_not_a_filter_injection(self):
        self.p['caption_position'] = 'top;movie=private'
        with self.assertRaises(ValueError):
            production.validate(self.p, self.root)

    def test_audio_overrun_bad_gain_and_fades(self):
        a = dict(file='tone.wav', start=0, end=4, role='voice', gain_db=0, rights=self.p['shots'][0]['rights'])
        for key, value in (('end', 9), ('gain_db', float('nan')), ('gain_db', 13), ('role', 'provider'), ('fade_in', 5)):
            b = dict(a)
            b[key] = value
            self.p['tracks'] = [b]
            with self.subTest(key=key), self.assertRaises(ValueError):
                production.validate(self.p, self.root)

    def test_risk_frame_is_local_and_half_open(self):
        self.p['shots'][1]['risk_frames'] = [4]
        with self.assertRaises(ValueError):
            production.validate(self.p, self.root)

    def test_missing_declared_source(self):
        self.p['shots'][0]['sources'] = ['missing.js']
        with self.assertRaises(ValueError):
            production.validate(self.p, self.root)

    def test_external_renderer_is_only_provenance(self):
        self.p['shots'][0]['renderer'] = 'uninstalled-blender'
        production.validate(self.p, self.root)
        self.assertEqual(self.p['shots'][0]['renderer'], 'uninstalled-blender')

    def test_beat_warning_is_not_expression_failure(self):
        self.p['beat_grid'] = dict(bpm=120, offset_frame=0, subdivision=1, tolerance_frames=.5)
        result = production.validate(self.p, self.root)
        self.assertTrue(any('off the declared beat' in x for x in result['warnings']))
        self.assertEqual(result['gates']['expression'], 'not_reviewed')

    def test_cjk_does_not_use_english_word_rate_as_a_verdict(self):
        self.p['shots'][0]['narration'] = '这是一次接触'
        self.assertTrue(any('CJK' in s for s in production.validate(self.p, self.root)['warnings']))

    @unittest.skipUnless(shutil.which('node'), 'Node optional: scene kit QA requires Node')
    def test_scene_kit_pure_geometry_and_hooks(self):
        js = """const assert=require('node:assert/strict'); const K=require(process.argv[1]);
assert.equal(K.sample(2,5),K.sample(2,5)); assert.notEqual(K.sample(2,5),K.sample(2,6));
assert.equal(K.onFrames(3/24,24,2),2/24); assert.throws(()=>K.onFrames(0,24,0));
const p=[[0,0],[3,0],[3,9]]; const original=JSON.stringify(p);
assert.deepEqual(K.prefix(p,.5),[[0,0],[3,0],[3,3]]); assert.equal(JSON.stringify(p),original);
assert.deepEqual(K.prefix(p,0),[[0,0]]); assert.deepEqual(K.prefix([],1),[]);
let saved=0; const calls=[];const g={save(){saved++},restore(){saved--},setTransform(){},clearRect(){}};
K.compose(g,2,10,10,{backdrop(){calls.push('look')},post(){calls.push('post')}},()=>calls.push('authored'));
assert.deepEqual(calls,['look','authored','post']); assert.equal(saved,0);
assert.throws(()=>K.compose(g,0,1,1,{},()=>{throw Error('draw') }));assert.equal(saved,0);
console.log('scene kit PASS');"""
        r = subprocess.run([shutil.which('node'), '-e', js, str(ROOT / 'runtime/scene-kit.js')], capture_output=True, text=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'local FFmpeg/ffprobe absent: integration fixtures not executed')
class MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.temp.name)
        cls.inputs = cls.base / 'inputs'
        cls.inputs.mkdir()
        for colour in ('red', 'blue'):
            production.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=' + colour + ':s=64x36:r=24',
                            '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=0.5',
                            '-frames:v', '8', '-c:v', 'libx264', '-threads', '1', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', cls.inputs / (colour + '.mp4')])
        with wave.open(str(cls.inputs / 'tone.wav'), 'wb') as w:
            w.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
            w.writeframes(b''.join(struct.pack('<h', round(6500 * math.sin(i * math.tau * 440 / 48000))) for i in range(12000)))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(dir=self.base))
        self.root = self.work / 'project'
        shutil.copytree(self.inputs, self.root)
        self.p = project()
        self.out = self.work / 'assembly'

    def test_real_frame_count_order_and_source_audio_is_muted(self):
        summary = production.assemble(self.p, self.root, self.out)
        info = production.probe(self.out / 'proof.mp4')
        self.assertIsNone(production.stream(info, 'audio'))
        self.assertEqual(summary['technical_checks']['decoded_frames'], 8)
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(self.out / 'proof.mp4'), '-vf', 'scale=1:1',
                              '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True, timeout=30).stdout
        self.assertGreater(raw[3*3], 200)
        self.assertGreater(raw[4*3+2], 200)
        self.assertEqual(set(summary['gates'].values()), {'not_reviewed'})

    def test_real_rational_output(self):
        self.p['fps'] = '30000/1001'
        production.assemble(self.p, self.root, self.out)
        self.assertEqual(production.stream(production.probe(self.out / 'proof.mp4'), 'video')['avg_frame_rate'], '30000/1001')

    def test_missing_clip_fails_without_placeholder_or_output(self):
        (self.root / 'blue.mp4').unlink()
        with self.assertRaisesRegex(ValueError, 'missing required media'):
            production.assemble(self.p, self.root, self.out)
        self.assertFalse(self.out.exists())

    def test_short_clip_requires_explicit_hold(self):
        self.p['shots'][0]['end'] = self.p['shots'][1]['start'] = 24
        self.p['shots'][1]['end'] = 28
        with self.assertRaisesRegex(ValueError, 'short video'):
            production.assemble(self.p, self.root, self.out)
        self.assertFalse(self.out.exists())
        self.p['shots'][0]['shortfall'] = 'hold'
        summary = production.assemble(self.p, self.root, self.out)
        self.assertTrue(any('explicit last-frame hold' in w for w in summary['warnings']))
        self.assertEqual(summary['technical_checks']['decoded_frames'], 28)

    def test_real_audio_cue_is_delayed_and_present(self):
        self.p['tracks'] = [dict(file='tone.wav', start=2, end=6, role='sfx', gain_db=-3,
                                 rights=self.p['shots'][0]['rights'], fade_out=1)]
        production.assemble(self.p, self.root, self.out)
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(self.out / 'proof.mp4'), '-vn', '-ac', '1', '-ar', '48000',
                              '-f', 's16le', '-'], capture_output=True, check=True, timeout=30).stdout
        values = array.array('h', raw)
        def rms(a, b):
            x = values[round(a*48000):round(b*48000)]
            return math.sqrt(sum(v*v for v in x) / len(x)) / 32768
        self.assertLess(rms(.01, .04), .002)
        self.assertGreater(rms(.12, .16), .02)

    def test_audio_shortfall_has_no_silent_fallback(self):
        self.p['tracks'] = [dict(file='tone.wav', start=0, end=8, role='voice', gain_db=0, rights=self.p['shots'][0]['rights'])]
        with self.assertRaisesRegex(ValueError, 'short audio'):
            production.assemble(self.p, self.root, self.out)
        self.assertFalse(self.out.exists())

    def test_inspect_exact_cut_neighbours_and_draft_allowlist(self):
        production.assemble(self.p, self.root, self.out)
        report = production.inspect(self.p, self.out / 'proof.mp4', self.work / 'inspection')
        self.assertTrue({3,4,5}.issubset({f['frame'] for f in report['frames']}))
        self.assertFalse(report['video_watched'])
        self.assertFalse(report['audio_listened'])
        (self.out / '.env').write_text('SYNTHETIC_FIXTURE=not-a-secret')
        target = self.work / 'draft.zip'
        production.package(self.out, target)
        with zipfile.ZipFile(target) as z:
            self.assertEqual(set(z.namelist()), {'proof.mp4','assembly.json','project.json','captions.srt','CREDITS.md'})
        (self.out / 'captions.srt').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'changed'):
            production.package(self.out, self.work / 'tampered.zip')
        self.assertFalse((self.work / 'tampered.zip').exists())

    def test_refuses_overwrite_and_wrong_inspection_contract(self):
        production.assemble(self.p, self.root, self.out)
        with self.assertRaisesRegex(ValueError, 'NEW directory'):
            production.assemble(self.p, self.root, self.out)
        self.p['height'] = 40
        with self.assertRaisesRegex(ValueError, 'does not match'):
            production.inspect(self.p, self.out / 'proof.mp4', self.work / 'bad-inspection')

    def test_caption_burn_is_actual_and_does_not_turn_gates_green(self):
        if not production.doctor()['features'].get('subtitles'):
            self.skipTest('local FFmpeg lacks libass/subtitles')
        self.p['captions'] = [dict(start=0, end=8, text="It's a caption fixture.")]
        self.p['caption_position'] = 'top'
        self.p['width'], self.p['height'] = 384, 216
        summary = production.assemble(self.p, self.root, self.out, burn=True)
        self.assertTrue(summary['captions_burned'])
        self.assertEqual(summary['gates']['readability'], 'not_reviewed')
        # Check actual white glyph pixels, not the presence of a style label in the command.
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', '0.1', '-i', str(self.out / 'proof.mp4'),
                              '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                             capture_output=True, check=True, timeout=30).stdout
        points = [(i // 3 % 384, i // 3 // 384) for i in range(0, len(raw), 3) if min(raw[i:i+3]) > 170]
        self.assertTrue(points, 'no visible subtitle glyph pixels')
        self.assertLess(max(y for x, y in points), 216 * .25)
        self.assertLess(abs((min(x for x,y in points) + max(x for x,y in points)) / 2 - 192), 384 * .15)


if __name__ == '__main__':
    unittest.main()
