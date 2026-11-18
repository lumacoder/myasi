"""Validate a review evidence record, NOT its visual truth or aesthetic quality."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

STATUSES={'pass','partial','fail','not_reviewed'}
GATES={'technical','readability','expression'}


def text(value,label):
    if not isinstance(value,str) or not value.strip() or 'REPLACE' in value:
        raise ValueError(label+' needs a non-placeholder description')


def evidence(root,value,label):
    text(value,label)
    path=(root/value).resolve()
    if not path.is_file(): raise ValueError(label+' file missing: '+str(path))
    return path


def validate(record,root,require_pass=False):
    if not isinstance(record,dict) or record.get('version')!=1:
        raise ValueError('expected review record version 1')
    root=Path(root)
    text(record.get('project'),'project'); text(record.get('scope'),'scope')
    evidence(root,record.get('brief'),'brief')
    reviews=record.get('reviews')
    if not isinstance(reviews,list) or len(reviews)<2: raise ValueError('need A and B reviews')
    by_id={}
    for review in reviews:
        if not isinstance(review,dict): raise ValueError('review must be an object')
        ident=review.get('id'); text(ident,'review.id')
        if ident in by_id: raise ValueError('duplicate review id')
        by_id[ident]=review
        for key in ('variant','pixels_observed','intent_delta','weakest_moment'):
            text(review.get(key),key)
        t=review.get('time_s')
        if isinstance(t,bool) or not isinstance(t,(int,float)) or not math.isfinite(t) or t<0:
            raise ValueError('review time_s must be finite nonnegative seconds')
        path=evidence(root,review.get('frame'),'review.frame')
        sha=review.get('sha256')
        if sha and sha!=hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError('frame sha256 mismatch')
    revisions=record.get('revisions')
    if not isinstance(revisions,list) or not revisions: raise ValueError('need substantive revision record')
    for revision in revisions:
        for key in ('hypothesis','substantive_change','predicted_pixel_change','observed_result'):
            text(revision.get(key),key)
        a=revision.get('from_review'); b=revision.get('to_review')
        if a not in by_id or b not in by_id or a==b: raise ValueError('invalid revision review link')
        before=evidence(root,revision.get('source_before'),'source_before')
        after=evidence(root,revision.get('source_after'),'source_after')
        if before.read_bytes()==after.read_bytes(): raise ValueError('revision sources are identical')
    comparisons=record.get('comparisons')
    if not isinstance(comparisons,list) or not comparisons: raise ValueError('need same-condition comparison')
    for pair in comparisons:
        a=by_id.get(pair.get('a')); b=by_id.get(pair.get('b'))
        if not a or not b or a is b: raise ValueError('invalid comparison ids')
        if a['time_s']!=b['time_s']: raise ValueError('comparison must use same time')
        conditions=pair.get('same_conditions')
        if not isinstance(conditions,list) or not {'time_s','dimensions'}.issubset(conditions):
            raise ValueError('comparison must declare time and dimensions')
        changes=pair.get('declared_changes')
        if not isinstance(changes,list) or not changes: raise ValueError('declare changed variables')
        for change in changes: text(change,'declared change')
    gates=record.get('gates')
    if not isinstance(gates,dict) or set(gates)!=GATES: raise ValueError('need three independent gates')
    blockers=[]
    for name,gate in gates.items():
        if not isinstance(gate,dict) or gate.get('status') not in STATUSES: raise ValueError('invalid gate status')
        text(gate.get('reason'),name+'.reason')
        items=gate.get('evidence')
        if not isinstance(items,list): raise ValueError('gate evidence must be a list')
        if gate['status'] in ('pass','partial','fail') and not items: raise ValueError('reviewed gate needs evidence')
        for item in items: evidence(root,item,name+'.evidence')
        if gate['status']!='pass': blockers.append(name+':'+gate['status'])
    limits=record.get('limitations')
    if not isinstance(limits,list) or not limits: raise ValueError('record limitations')
    for limit in limits: text(limit,'limitation')
    if require_pass and blockers: raise ValueError('not delivery-approved: '+', '.join(blockers))
    return {'structure':'valid','declared_gate_states':{k:v['status'] for k,v in gates.items()},
            'visual_truth_verified':False,'blockers':blockers}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('record',type=Path)
    p.add_argument('--require-pass',action='store_true');a=p.parse_args(argv)
    try:
        record=json.loads(a.record.read_text(encoding='utf8'))
        print(json.dumps(validate(record,a.record.resolve().parent,a.require_pass),ensure_ascii=False,indent=2))
        return 0
    except (ValueError,OSError,TypeError,KeyError,AttributeError) as exc:
        print('Review record blocked: '+str(exc),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
