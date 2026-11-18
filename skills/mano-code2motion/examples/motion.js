/* MotionSpec v1 evaluator. Input must pass scripts/check.py before export. */
(() => {
  'use strict';
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const cubic = (u, a, b) => 3*(1-u)**2*u*a + 3*(1-u)*u*u*b + u**3;
  function easing(q, ease) {
    q=clamp(q,0,1);
    if(q===0 || q===1) return q;
    switch(ease.kind) {
      case 'linear': return q;
      case 'smoothstep': return q*q*(3-2*q);
      case 'smootherstep': return q*q*q*(q*(q*6-15)+10);
      case 'cubic-bezier': {
        const [x1,y1,x2,y2]=ease.control;
        let lo=0, hi=1;
        for(let i=0;i<50;i++) {
          const mid=(lo+hi)/2;
          if(cubic(mid,x1,x2)<q) lo=mid; else hi=mid;
        }
        return cubic((lo+hi)/2,y1,y2);
      }
      default: throw new Error('Unsupported easing '+ease.kind);
    }
  }
  function stateAt(spec, seconds) {
    if(!Number.isFinite(seconds)) throw new Error('Time must be finite');
    const t=clamp(seconds,0,spec.duration_s);
    const state=Object.fromEntries(spec.objects.map(o=>[o.id,{...o}]));
    for(const tr of [...spec.tracks].sort((a,b)=>a.start_s-b.start_s)) {
      if(t<tr.start_s) continue;
      state[tr.object][tr.property]=tr.from+(tr.to-tr.from)*easing((t-tr.start_s)/tr.duration_s,tr.ease);
    }
    return state;
  }
  function seeded(seed,index) {
    let x=(seed^index)>>>0;
    x=Math.imul(x^(x>>>16),0x7feb352d)>>>0;
    x=Math.imul(x^(x>>>15),0x846ca68b)>>>0;
    return ((x^(x>>>16))>>>0)/4294967296;
  }
  window.Motion={easing,stateAt,seeded};
})();
