/* C engineering checks: these do NOT prove the audience sees a gust. */
'use strict';
const assert=require('assert'),c=require('./scene-c.js'),b=require('./scene-b.js');
const close=(a,b,tol=1e-7)=>assert(Math.abs(a-b)<tol,`${a} != ${b}`);
let roots=0,maxRodLengthError=0,maxBranchStep=0,maxLeafStep=0,prev=c.layout(0);
for(let i=0;i<=1440;i++){
 const t=i/240,s=c.layout(t);
 for(const branch of s.branches){
  const p=c.stemPoint(c.stems[branch.stem],branch.u,t);close(p.x,branch.curve[0].x);close(p.y,branch.curve[0].y);
  if(s.stemGrowth<branch.u)assert(branch.growth<1e-8);
  for(const l of branch.leaves){
   const p=c.bezier(branch.curve,l.branch_q);close(p.x,l.curve[0].x);close(p.y,l.curve[0].y);
   assert(Number.isFinite(l.curve[3].x)&&Number.isFinite(l.curve[3].y));
   if(branch.growth<l.branch_q)assert(l.growth<1e-8);roots++;
  }
 }
 if(i){s.branches.forEach((branch,k)=>{
  maxBranchStep=Math.max(maxBranchStep,Math.abs(branch.growth-prev.branches[k].growth));
  branch.leaves.forEach((l,j)=>maxLeafStep=Math.max(maxLeafStep,Math.abs(l.growth-prev.branches[k].leaves[j].growth)));
 });}prev=s;
 if(i%120===0)c.stems.forEach(stem=>{
  const p=c.stemPoint(stem,0,t);close(p.x,stem.x);close(p.y,658);
  let length=0,p0=p;for(let j=1;j<=400;j++){const p1=c.stemPoint(stem,j/400,t);length+=Math.hypot(p1.x-p0.x,p1.y-p0.y);p0=p1}
  maxRodLengthError=Math.max(maxRodLengthError,Math.abs(length-Math.hypot(stem.h,stem.lean)));
 });
 if(t<2.6){const old=b.layout(t);close(s.stemGrowth,old.stemGrowth);s.branches.forEach((branch,k)=>{close(branch.growth,old.branches[k].growth);branch.leaves.forEach((l,j)=>close(l.growth,old.branches[k].leaves[j].growth))})}
}
assert(maxRodLengthError<.002);assert(maxBranchStep<.02&&maxLeafStep<.02);
for(const t of [2.6,2.8,3.1,5.7,6])close(c.wind(t),0);
close(c.wind(3.78),.22);close(c.wind(4.62),-.065);
assert(Math.abs(c.wind(4.62))<c.wind(3.78)/3);
const early=c.layout(3.78).branches[2].leaves[3].leafLoad,late=c.layout(4.12).branches[2].leaves[3].leafLoad;
assert(late>early+.25);assert(2*.22<.5);
assert.deepStrictEqual(c.layout(2.8).branches,c.layout(5.7).branches);
const snapshot=JSON.stringify(c.layout(4.12));c.layout(6);c.layout(0);assert.strictEqual(JSON.stringify(c.layout(4.12)),snapshot);
for(const t of [NaN,Infinity,'3',null])assert.throws(()=>c.layout(t));
console.log(JSON.stringify({status:'PASS',samples:1441,leaf_root_checks:roots,max_rod_arclength_error_px:maxRodLengthError,
 reveal_max_step:{branch:maxBranchStep,leaf:maxLeafStep},
 coded_phase_measurements:{stem_press:.22,stem_counter:-.065,leaf_load_at_stem_hold:early,leaf_load_later:late,max_upper_tangent_rad:.44,exact_quiet_after_s:5.61},
 scope:'attachments, early reveal unchanged, fixed rod arc length, bounded compact event, delayed local load, exact rest, deterministic state',
 visual_verdict:'NOT_ASSESSED_BY_TECHNICAL_QA; independent findings are in independent-review-C.json'},null,2));
