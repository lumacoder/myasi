/* Revision C: one readable gust, delayed blade response, one smaller rebound and explicit rest.
 * Original implementation. This is stylized analytic deformation, not fluid/plant simulation.
 * A/B remain unchanged in scene-a.js / scene-b.js. Camera, roots, canvas and paper color are held fixed.
 */
(function(root){
'use strict';
const W=1280,H=720,DURATION=6;
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
function hash(i){let x=(Math.imul(i+11,2654435761)^12721)>>>0;x^=x>>>16;return (x>>>0)/4294967296}
function inverseSmooth(y){
 let lo=0,hi=1;for(let i=0;i<36;i++){const mid=(lo+hi)/2;if(smooth(mid)<y)lo=mid;else hi=mid}return (lo+hi)/2;
}
function bezier(p,q){const u=1-q;return {x:u*u*u*p[0].x+3*u*u*q*p[1].x+3*u*q*q*p[2].x+q*q*q*p[3].x,
 y:u*u*u*p[0].y+3*u*u*q*p[1].y+3*u*q*q*p[2].y+q*q*q*p[3].y}}
const stems=[{x:716,h:555,lean:-35,w:14,ink:.92},{x:535,h:452,lean:-112,w:9,ink:.56},{x:879,h:372,lean:66,w:8,ink:.45}];
// Compact support: there is no idle oscillation outside this one event.
function soft(x){x=clamp(x);return x*x*x*(x*(6*x-15)+10)}
function wind(t){
 if(t<=3.12||t>=5.22)return 0;
 if(t<3.70)return .22*soft((t-3.12)/.58);
 if(t<3.88)return .22;
 if(t<4.62)return .22+(-.065-.22)*soft((t-3.88)/.74);
 return -.065*(1-soft((t-4.62)/.60));
}
function stemPoint(s,u,t){
 const k=2*wind(t),a=Math.atan2(s.lean,s.h),L=Math.hypot(s.h,s.lean);
 if(Math.abs(k)<1e-8)return {x:s.x+s.lean*u,y:658-s.h*u};
 // Integrate a changing tangent along a fixed-length rod, rather than x-shear/stretch.
 return {x:s.x+L*(Math.cos(a)-Math.cos(a+k*u))/k,
         y:658-L*(Math.sin(a+k*u)-Math.sin(a))/k};
}
function branchAngle(d,t){return d[1]*(1.10*wind(t)+.70*wind(t-.10))}
const branchDesign=[
 // stem, height, side, branch length, rise, leaf angle offsets, leaf scale
 [0,.31, 1,124,28,[-.72,-.13,.42,.91],1.05],
 [0,.48,-1,136,64,[-.80,-.35,.20,.68,1.03],1.13],
 [0,.66, 1,142,36,[-.91,-.29,.33,.77],1.10],
 [0,.82,-1, 98,45,[-.65,-.06,.62],1.00],
 [0,.94, 1, 59,40,[-.76,-.12,.53],.80],
 [1,.38,-1, 94,20,[-.62,.04,.64],.86],
 [1,.62, 1, 67,47,[-.80,-.23,.38,.83],.78],
 [1,.85,-1, 89,35,[-.51,.03,.73],.87],
 [2,.29, 1, 90,26,[-.73,-.08,.48],.83],
 [2,.60,-1, 94,51,[-.83,-.23,.42,.93],.84],
 [2,.86, 1, 58,34,[-.63,-.03,.66],.75]
];
function branchCurve(s,d,t){
 const a=stemPoint(s,d[1],t),side=d[2],response=branchAngle(d,t);
 const dx=side*d[3],dy=-d[4];
 const tip={x:a.x+dx*Math.cos(response)-dy*Math.sin(response),y:a.y+dx*Math.sin(response)+dy*Math.cos(response)};
 return [a,{x:a.x+dx*.30,y:a.y-9},{x:tip.x-dx*.26,y:tip.y+11},tip];
}
function leafCurve(x,y,angle,len,bend){
 const cs=Math.cos(angle),sn=Math.sin(angle),p=(u,v)=>({x:x+cs*u-sn*v,y:y+sn*u+cs*v});
 return [p(0,0),p(len*.29,-bend),p(len*.73,bend*.25),p(len,bend*.70)];
}
function layout(seconds){
 if(!Number.isFinite(seconds))throw Error('finite seconds required');
 const t=clamp(seconds,0,DURATION),stemGrowth=smooth((t-.15)/2.0),branches=[];
 branchDesign.forEach((d,i)=>{
  const s=stems[d[0]],curve=branchCurve(s,d,t);
  // Derive phase start from the support brush's ARRIVAL, not an independent clock
  // abruptly masked by a threshold. This preserves continuous reveal at attachment.
  const arrival=.15+2*inverseSmooth(d[1]);
  const growth=smooth((t-arrival)/.40);
  const leaves=d[5].map((offset,j)=>{
   const q=Math.min(.98,.56+j*.105+.045*hash(i*17+j)),anchor=bezier(curve,q);
   const side=d[2];
   const baseAngle=(side<0?Math.PI:0)+side*offset;
   const leafDelay=.25+.035*j,leafLoad=wind(t-leafDelay)/.22;
   // Blades align leeward later than the stem, while their roots follow the CURRENT branch.
   const leafAngleDelta=-Math.sin(baseAngle)*.34*leafLoad;
   const angle=baseAngle+branchAngle(d,t)+leafAngleDelta;
   const length=(76+39*hash(i*31+j))*d[6];
   const leafArrival=arrival+.40*inverseSmooth(q);
   const g=smooth((t-leafArrival)/.38);
   return {anchor,branch_q:q,leafDelay,leafLoad,leafAngleDelta,curve:leafCurve(anchor.x,anchor.y,angle,length,(11+12*hash(i*23+j))*(1+.45*Math.abs(leafLoad))),
      width:(6.2+5.4*hash(i*13+j))*d[6],growth:g,seed:1000+i*101+j};
  });
  branches.push({stem:d[0],curve,u:d[1],growth,leaves,seed:100+i});
 });
 return {t,stemGrowth,branches};
}
// Centerline -> tangent/normal -> variable-pressure polygon.
// The material coordinates travel with each stroke. No time-dependent texture noise.
function brush(ctx,point,width,growth,alpha,seed,dryness=.25){
 if(growth<=0)return;
 const n=70,left=[],right=[],samples=[];
 for(let i=0;i<=n;i++){
  const q=i/n*growth,p=point(q),a=point(Math.max(0,q-.001)),b=point(Math.min(1,q+.001));
  const dx=b.x-a.x,dy=b.y-a.y,l=Math.hypot(dx,dy)||1;
  const w=Math.max(.10,width(q))*(1+.045*Math.sin(q*83+seed));
  const nx=-dy/l,ny=dx/l;
  samples.push({p,nx,ny,w,q});left.push({x:p.x+nx*w,y:p.y+ny*w});right.push({x:p.x-nx*w,y:p.y-ny*w});
 }
 ctx.save();ctx.globalAlpha=alpha;
 ctx.beginPath();left.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));
 right.reverse().forEach(p=>ctx.lineTo(p.x,p.y));ctx.closePath();
 const a=samples[0].p,b=samples[samples.length-1].p;
 const ink=ctx.createLinearGradient(a.x,a.y,b.x,b.y);
 ink.addColorStop(0,'#35473d');ink.addColorStop(.32,'#172b22');ink.addColorStop(.76,'#20372d');ink.addColorStop(1,'#526354');
 ctx.fillStyle=ink;ctx.fill();ctx.clip();
 // Fine longitudinal unloaded bristles, in stroke-local coordinates.
 for(let k=0;k<4;k++){
  const start=.12+.16*hash(seed+k),end=.62+.35*hash(seed+19+k);
  const offset=(hash(seed+43+k)*1.7-.85);
  ctx.beginPath();let first=true;
  samples.forEach(s=>{if(s.q<start||s.q>end)return;
   const f=offset+.06*Math.sin(s.q*23+seed+k),x=s.p.x+s.nx*s.w*f,y=s.p.y+s.ny*s.w*f;
   first?ctx.moveTo(x,y):ctx.lineTo(x,y);first=false});
  ctx.strokeStyle='rgba(241,236,223,'+(dryness*(.4+.6*hash(seed+k+5)))+')';
  ctx.lineWidth=.35+.5*hash(seed+9+k);ctx.stroke();
 }
 ctx.restore();
}
function drawStem(ctx,s,t,g,si){
 const nodes=[0,.135,.285,.445,.615,.785,.95,1];
 for(let k=0;k<nodes.length-1;k++){
  const a=nodes[k]+(k? .003:0),b=nodes[k+1]-.005;
  if(g<a)continue;const q=clamp((g-a)/(b-a));
  brush(ctx,u=>stemPoint(s,a+(b-a)*u,t),u=>s.w*.5*(1-.56*(a+(b-a)*u))*(.95+.06*Math.sin(u*Math.PI)),q,s.ink,si*71+k,.52);
 }
 nodes.slice(1,-1).forEach((u,k)=>{if(g<u)return;const p=stemPoint(s,u,t),w=s.w*.5*(1-.56*u);
  ctx.save();ctx.globalAlpha=s.ink;ctx.strokeStyle='#243a2e';ctx.lineWidth=1.7;
  ctx.beginPath();ctx.moveTo(p.x-w-1,p.y+1);ctx.quadraticCurveTo(p.x,p.y-2.4,p.x+w+1,p.y+.4);ctx.stroke();
  ctx.lineWidth=.75;ctx.beginPath();ctx.moveTo(p.x-w,p.y-2.6);ctx.lineTo(p.x-w-2,p.y-4.2);ctx.stroke();ctx.restore();
 });
}
function drawWindApproach(ctx,t){
 // Three brief ink hairlines communicate direction once; no captions, no repeated particles.
 const alpha=.20*soft((t-2.96)/.12)*(1-soft((t-3.48)/.15));
 if(alpha<=0)return;
 ctx.save();ctx.globalAlpha=alpha;ctx.strokeStyle='#6f8070';ctx.lineWidth=1.1;
 [185,305,435].forEach((y,i)=>{
  const x=-60+(t-2.96)*1150+i*46,dy=[-11,6,-5][i];
  ctx.beginPath();ctx.moveTo(x-90,y);ctx.bezierCurveTo(x-63,y+dy,x-28,y+dy,x,y);ctx.stroke();
 });ctx.restore();
}
function renderAt(seconds){
 if(!Number.isFinite(seconds))throw Error('finite seconds required');
 const ctx=document.getElementById('art').getContext('2d');
 ctx.setTransform(1,0,0,1,0,0);ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
 ctx.clearRect(0,0,W,H);ctx.fillStyle='#f1ecdf';ctx.fillRect(0,0,W,H);
 const state=layout(seconds),t=state.t;ctx.lineCap='round';ctx.lineJoin='round';
 drawWindApproach(ctx,t);
 // Back to front: identity/depth is carried by ink load, not a blur filter.
 [1,2,0].forEach(si=>{
  const s=stems[si];drawStem(ctx,s,t,state.stemGrowth,si);
  state.branches.filter(b=>b.stem===si).forEach(b=>{
   brush(ctx,q=>bezier(b.curve,q),q=>1.25*(1-q)+.12,b.growth,s.ink,b.seed,.2);
   b.leaves.forEach(l=>brush(ctx,q=>bezier(l.curve,q),q=>
     l.width*Math.pow(Math.max(0,Math.sin(Math.PI*q)),.75)*(.72+.28*q),
     l.growth,s.ink,l.seed,.32));
  });
 });return state;
}
const api={layout,stemPoint,stems,wind,bezier,branchCurve,branchDesign,branchAngle,inverseSmooth,drawWindApproach,brush,renderAt,DURATION};
if(typeof module!=='undefined')module.exports=api;
root.InkBamboo=api;root.renderAt=renderAt;
})(typeof window!=='undefined'?window:globalThis);
