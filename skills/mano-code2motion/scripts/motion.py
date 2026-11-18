"""MotionSpec v1 reference evaluator. Python 3.8+, standard library only."""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROPERTIES = ('x_px', 'y_px', 'scale', 'rotation_rad', 'opacity')


def schema_check(value, schema, root, path='$'):
    """Only the JSON Schema subset used in our bundled schema; not a general engine."""
    if '$ref' in schema:
        target = root
        for part in schema['$ref'].split('/')[1:]:
            target = target[part]
        return schema_check(value, target, root, path)
    kind = schema.get('type')
    kinds = {'object': lambda x: isinstance(x, dict),
             'array': lambda x: isinstance(x, list),
             'string': lambda x: isinstance(x, str),
             'number': lambda x: type(x) in (int, float) and math.isfinite(x),
             'integer': lambda x: type(x) is int}
    if kind and not kinds[kind](value):
        raise ValueError('%s: expected %s' % (path, kind))
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError('%s: invalid enum' % path)
    if kind == 'object':
        for key in schema.get('required', []):
            if key not in value:
                raise ValueError('%s: missing %s' % (path, key))
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False and set(value) - set(props):
            raise ValueError('%s: unknown fields %s' % (path, sorted(set(value) - set(props))))
        for key in value:
            if key in props:
                schema_check(value[key], props[key], root, path + '.' + key)
    if kind == 'array':
        if len(value) < schema.get('minItems', 0) or len(value) > schema.get('maxItems', math.inf):
            raise ValueError('%s: array length' % path)
        for i, item in enumerate(value):
            schema_check(item, schema['items'], root, '%s[%d]' % (path, i))
    if kind == 'string':
        if len(value) < schema.get('minLength', 0):
            raise ValueError('%s: short string' % path)
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            raise ValueError('%s: pattern mismatch' % path)
    if kind in ('number', 'integer'):
        if value < schema.get('minimum', -math.inf) or value > schema.get('maximum', math.inf):
            raise ValueError('%s: out of range' % path)
        if 'exclusiveMinimum' in schema and value <= schema['exclusiveMinimum']:
            raise ValueError('%s: not above minimum' % path)


def validate(spec):
    schema = json.loads((ROOT / 'references/motion-spec.schema.json').read_text(encoding='utf8'))
    schema_check(spec, schema, schema)
    frames = spec['duration_s'] * spec['fps']
    if abs(frames - round(frames)) > 1e-8:
        raise ValueError('duration_s * fps must be an integer frame count')
    objects = {obj['id']: obj for obj in spec['objects']}
    if len(objects) != len(spec['objects']):
        raise ValueError('duplicate object id')
    grouped = {}
    for track in spec['tracks']:
        if track['object'] not in objects:
            raise ValueError('unknown object reference')
        if track['start_s'] + track['duration_s'] > spec['duration_s'] + 1e-9:
            raise ValueError('track extends beyond timeline')
        ease = track['ease']
        if ease['kind'] == 'cubic-bezier':
            if 'control' not in ease:
                raise ValueError('cubic-bezier needs four control values')
            x1, y1, x2, y2 = ease['control']
            if not (0 <= x1 <= 1 and 0 <= x2 <= 1):
                raise ValueError('temporal bezier x controls must be in [0,1]')
        elif 'control' in ease:
            raise ValueError('only cubic-bezier accepts control')
        prop = track['property']
        values = [track['from'], track['to']]
        if prop == 'opacity' and not all(0 <= v <= 1 for v in values):
            raise ValueError('opacity endpoints outside [0,1]')
        if prop == 'scale' and not all(v > 0 for v in values):
            raise ValueError('scale must remain positive')
        if prop in ('opacity', 'scale') and ease['kind'] == 'cubic-bezier':
            if not all(0 <= ease['control'][i] <= 1 for i in (1, 3)):
                raise ValueError('bounded properties disallow overshooting controls')
        grouped.setdefault((track['object'], prop), []).append(track)
    for (ident, prop), tracks in grouped.items():
        previous_end, previous_value = 0, objects[ident][prop]
        for track in sorted(tracks, key=lambda tr: tr['start_s']):
            if track['start_s'] < previous_end - 1e-9:
                raise ValueError('overlapping property tracks')
            if not math.isclose(track['from'], previous_value, abs_tol=1e-7, rel_tol=0):
                raise ValueError('position/value discontinuity (C0)')
            previous_end = track['start_s'] + track['duration_s']
            previous_value = track['to']
    return spec


def load(path):
    def bad(value):
        raise ValueError('non-finite JSON number: ' + value)
    return validate(json.loads(Path(path).read_text(encoding='utf-8-sig'), parse_constant=bad))


def cubic(u, a, b):
    return 3 * (1-u)**2 * u * a + 3 * (1-u) * u*u * b + u**3


def easing(q, ease):
    q = max(0.0, min(1.0, q))
    if q == 0 or q == 1:
        return q
    kind = ease['kind']
    if kind == 'linear':
        return q
    if kind == 'smoothstep':
        return q*q*(3-2*q)
    if kind == 'smootherstep':
        return q*q*q*(q*(q*6-15)+10)
    if kind != 'cubic-bezier':
        raise ValueError('unsupported easing')
    x1, y1, x2, y2 = ease['control']
    lo, hi = 0.0, 1.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if cubic(mid, x1, x2) < q:
            lo = mid
        else:
            hi = mid
    return cubic((lo+hi)/2, y1, y2)


def state_at(spec, seconds):
    if not math.isfinite(seconds):
        raise ValueError('time must be finite')
    seconds = max(0, min(spec['duration_s'], seconds))
    state = {obj['id']: dict(obj) for obj in spec['objects']}
    for track in sorted(spec['tracks'], key=lambda tr: tr['start_s']):
        if seconds < track['start_s']:
            continue
        q = (seconds-track['start_s']) / track['duration_s']
        value = track['from'] + (track['to']-track['from']) * easing(q, track['ease'])
        state[track['object']][track['property']] = value
    return state


def seeded(seed, index):
    """Stateless 32-bit hash; same result in browser; not cryptographic."""
    x = (seed ^ index) & 0xffffffff
    x = ((x ^ (x >> 16)) * 0x7feb352d) & 0xffffffff
    x = ((x ^ (x >> 15)) * 0x846ca68b) & 0xffffffff
    return ((x ^ (x >> 16)) & 0xffffffff) / 4294967296.0


def report(spec):
    step = 1.0 / spec['fps']
    n = round(spec['duration_s'] * spec['fps'])
    tracks = []
    for track in spec['tracks']:
        start, duration = track['start_s'], track['duration_s']
        distance = track['to'] - track['from']
        # Dense normalized sampling isolates per-segment speed; not continuity proof.
        velocities = [distance / duration * (easing((i+1)/1000, track['ease']) -
                      easing(i/1000, track['ease'])) * 1000 for i in range(1000)]
        peak = max(range(1000), key=lambda i: abs(velocities[i]))
        tracks.append({'object': track['object'], 'property': track['property'],
                       'delta': distance, 'duration_s': duration,
                       'peak_abs_velocity_per_s': abs(velocities[peak]),
                       'peak_time_s_approx': start + (peak+0.5)/1000*duration,
                       'derivative_normalized_step': 0.001})
    return {'frames': n, 'fps': spec['fps'], 'duration_s': spec['duration_s'],
            'last_encoded_time_s': (n-1)*step,
            'notes': ['Measurements, not aesthetic pass thresholds.',
                      'Finite differences do not prove C1/C2 continuity.',
                      'Visual object quality and contact require separate review.'],
            'tracks': tracks}
