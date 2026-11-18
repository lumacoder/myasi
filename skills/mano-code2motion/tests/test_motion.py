import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from motion import cubic, easing, load, report, seeded, state_at, validate


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.spec = load(ROOT / 'examples/compare.json')

    def invalid(self, change):
        change(self.spec)
        with self.assertRaises(ValueError):
            validate(self.spec)

    def test_valid_example(self):
        self.assertEqual(report(self.spec)['frames'], 96)

    def test_endpoints_and_clamp(self):
        for tr in self.spec['tracks']:
            self.assertEqual(easing(-1, tr['ease']), 0)
            self.assertEqual(easing(2, tr['ease']), 1)
        self.assertEqual(state_at(self.spec, -2), state_at(self.spec, 0))
        self.assertEqual(state_at(self.spec, 20), state_at(self.spec, 4))

    def test_css_bezier_inverts_x_not_t(self):
        ease = {'kind': 'cubic-bezier', 'control': [.42, 0, 1, 1]}
        self.assertAlmostEqual(easing(.5, ease), .31535681257253934, places=12)
        self.assertNotAlmostEqual(easing(.5, ease), cubic(.5, 0, 1), places=3)

    def test_css_degenerate_x_still_solved(self):
        for controls in ([0, 0, 0, 1], [1, 0, 1, 1]):
            values = [easing(i/100, {'kind': 'cubic-bezier', 'control': controls}) for i in range(101)]
            self.assertTrue(all(a <= b for a, b in zip(values, values[1:])))

    def test_smoothstep_is_not_c2_at_rest(self):
        h = 1e-4
        ease = {'kind': 'smoothstep'}
        acc = (easing(2*h, ease)-2*easing(h, ease)+easing(0, ease))/h**2
        self.assertGreater(abs(acc), 5)

    def test_smootherstep_has_zero_endpoint_velocity_acceleration(self):
        h, ease = 1e-5, {'kind': 'smootherstep'}
        velocity = (easing(h, ease)-easing(0, ease))/h
        acceleration = (easing(2*h, ease)-2*easing(h, ease)+easing(0, ease))/h**2
        self.assertLess(abs(velocity), 1e-6)
        self.assertLess(abs(acceleration), .001)

    def test_world_velocity_scales_by_distance_over_duration(self):
        tr = self.spec['tracks'][0]
        t, h = 1, .0001
        v = (state_at(self.spec, t+h)['linear']['x_px']-state_at(self.spec, t-h)['linear']['x_px'])/(2*h)
        self.assertAlmostEqual(v, (tr['to']-tr['from'])/tr['duration_s'], places=6)

    def test_same_distance_and_duration(self):
        self.assertEqual({tr['to']-tr['from'] for tr in self.spec['tracks']}, {870})
        self.assertEqual({tr['duration_s'] for tr in self.spec['tracks']}, {2.6})
        self.assertEqual({tr['start_s'] for tr in self.spec['tracks']}, {.5})

    def test_heavy_late_peak_no_rebound(self):
        data = report(self.spec)['tracks']
        self.assertGreater(data[2]['peak_time_s_approx'], data[1]['peak_time_s_approx'])
        x = [state_at(self.spec, i/100)['heavy']['x_px'] for i in range(401)]
        self.assertTrue(all(a <= b+1e-9 for a,b in zip(x, x[1:])))
        self.assertLessEqual(max(x), 1170)

    def test_seek_is_stateless(self):
        original = copy.deepcopy(self.spec)
        expected = state_at(self.spec, 1.375)
        for t in (3.9, .01, 1.9, 0, 4):
            state_at(self.spec, t)
        self.assertEqual(state_at(self.spec, 1.375), expected)
        self.assertEqual(self.spec, original)

    def test_seed_is_stateless(self):
        self.assertEqual(seeded(17, 31), seeded(17, 31))
        self.assertNotEqual(seeded(17, 31), seeded(18, 31))
        self.assertTrue(all(0 <= seeded(17, i) < 1 for i in range(100)))

    def test_duplicate_object_rejected(self):
        self.invalid(lambda s: s['objects'].append(copy.deepcopy(s['objects'][0])))

    def test_unknown_fields_rejected(self):
        self.invalid(lambda s: s.update(camera={}))

    def test_unknown_ease_rejected(self):
        self.invalid(lambda s: s['tracks'][0]['ease'].update(kind='magic-smooth'))

    def test_reference_rejected(self):
        self.invalid(lambda s: s['tracks'][0].update(object='missing'))

    def test_ends_outside_timeline_rejected(self):
        self.invalid(lambda s: s['tracks'][0].update(start_s=3))

    def test_zero_duration_rejected(self):
        self.invalid(lambda s: s['tracks'][0].update(duration_s=0))

    def test_fractional_frame_count_rejected(self):
        self.invalid(lambda s: s.update(duration_s=4.001))

    def test_nonfinite_rejected(self):
        self.invalid(lambda s: s['tracks'][0].update(to=math.inf))

    def test_boolean_numeric_rejected(self):
        self.invalid(lambda s: s.update(fps=True))

    def test_bad_bezier_x_rejected(self):
        self.invalid(lambda s: s['tracks'][2]['ease'].update(control=[-1, 0, 1, 1]))

    def test_missing_bezier_controls_rejected(self):
        self.invalid(lambda s: s['tracks'][2]['ease'].pop('control'))

    def test_extraneous_controls_rejected(self):
        self.invalid(lambda s: s['tracks'][0]['ease'].update(control=[0,0,1,1]))

    def test_overlap_rejected(self):
        self.invalid(lambda s: s['tracks'].append(copy.deepcopy(s['tracks'][0])))

    def test_c0_discontinuity_rejected(self):
        self.invalid(lambda s: s['tracks'][0].update(**{'from': 0}))

    def test_c0_connected_segments_and_gap_hold(self):
        self.spec['tracks'][0]['duration_s'] = 1
        self.spec['tracks'].append({'object':'linear','property':'x_px','start_s':2,
                                   'duration_s':1,'from':1170,'to':1200,'ease':{'kind':'linear'}})
        validate(self.spec)
        self.assertEqual(state_at(self.spec, 1.9)['linear']['x_px'], 1170)
        self.assertEqual(state_at(self.spec, 3)['linear']['x_px'], 1200)

    def test_opacity_endpoints_rejected(self):
        self.invalid(lambda s: s['tracks'][0].update(property='opacity', **{'from':1, 'to':2}))

    def test_overshoot_position_allowed_but_opacity_not(self):
        self.spec['tracks'][2]['ease']['control'] = [.4, -1, .7, 2]
        validate(self.spec)
        self.spec['tracks'][2].update(property='opacity', **{'from':1,'to':0})
        with self.assertRaises(ValueError):
            validate(self.spec)

    def test_nan_json_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bad.json'
            p.write_text('{"x":NaN}', encoding='utf8')
            with self.assertRaises(ValueError):
                load(p)

    def test_time_nan_rejected(self):
        with self.assertRaises(ValueError):
            state_at(self.spec, math.nan)

    def test_vocabulary_has_context_counterexamples_verification(self):
        data = json.loads((ROOT/'references/vocabulary.json').read_text(encoding='utf8'))
        self.assertEqual(len(data['terms']), 10)
        for item in data['terms']:
            self.assertGreaterEqual(len(item['context_branches']), 2)
            self.assertTrue(item['counterexample'])
            self.assertTrue(item['verification'])

    def test_json_files_parse(self):
        for path in ROOT.rglob('*.json'):
            json.loads(path.read_text(encoding='utf8'))


if __name__ == '__main__':
    unittest.main()
