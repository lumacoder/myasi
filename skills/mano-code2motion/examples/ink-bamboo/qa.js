/* Numeric/structural checks only; never an aesthetic or recognition score. */
'use strict';
const assert=require('assert'),fs=require('fs'),path=require('path');
const b=require('./scene-b.js'),a=require('./scene-a.js');
const close=(x,y)=>assert(Math.abs(x-y)<1e-8,`${x} != ${y}`);
function finite(v){if(typeof v==='number')assert(Number.isFinite(v));else if(v&&typeof v==='object')Object.values(v).forEach(finite)}
let samples=0,leaves=0;
for(let i=0;i<=360;i++){
 const t=i/60,state=b.layout(t);finite(state);samples++;
 state.branches.forEach(branch=>{
  const p=b.stemPoint(b.stems[branch.stem],branch.u,t);
  close(branch.curve[0].x,p.x);close(branch.curve[0].y,p.y);
  if(state.stemGrowth<branch.u)assert.strictEqual(branch.growth,0);
  branch.leaves.forEach(l=>{
   const root=b.bezier(branch.curve,l.branch_q);close(root.x,l.anchor.x);close(root.y,l.anchor.y);
   close(l.curve[0].x,root.x);close(l.curve[0].y,root.y);
   if(branch.growth<l.branch_q)assert.strictEqual(l.growth,0);
   assert(l.growth>=0&&l.growth<=1);assert(l.branch_q>=0&&l.branch_q<=1);leaves++;
  });
 });
 b.stems.forEach(s=>{const root=b.stemPoint(s,0,t);close(root.x,s.x);close(root.y,658)});
}
assert.deepStrictEqual(b.layout(2.8),b.layout(2.8));
const snapshot=JSON.stringify(b.layout(3.8));b.layout(6);b.layout(0);b.layout(1.2);
assert.strictEqual(JSON.stringify(b.layout(3.8)),snapshot);
assert.deepStrictEqual(b.layout(-1),b.layout(0));assert.deepStrictEqual(b.layout(9),b.layout(6));
for(const v of [NaN,Infinity,-Infinity,'3',null])assert.throws(()=>b.layout(v));
assert.notDeepStrictEqual(a.layout(2.8),b.layout(2.8));
// Guard against the former support-threshold pop: phase starts must be continuous.
let previous=b.layout(0),maxBranchStep=0,maxLeafStep=0;
for(let i=1;i<=1440;i++){
 const state=b.layout(i/240);
 state.branches.forEach((branch,k)=>{
  maxBranchStep=Math.max(maxBranchStep,Math.abs(branch.growth-previous.branches[k].growth));
  branch.leaves.forEach((l,j)=>maxLeafStep=Math.max(maxLeafStep,Math.abs(l.growth-previous.branches[k].leaves[j].growth)));
 });previous=state;
}
assert(maxBranchStep<.02,`branch reveal pop ${maxBranchStep}`);
assert(maxLeafStep<.02,`leaf reveal pop ${maxLeafStep}`);
console.log(JSON.stringify({status:'PASS',samples,leaf_root_checks:leaves,
 reveal_continuity:{sample_step_s:1/240,max_branch_step:maxBranchStep,max_leaf_step:maxLeafStep},scope:[
 'finite state','branch roots on current stem','leaf roots on current branch','no reveal ahead of support',
 'fixed stem bases','continuous support-derived phase starts','state seek determinism','time clamping','invalid time rejected'],
 not_tested:['visual identity','aesthetics','wind perception','normal-speed rhythm','botanical/physical realism']},null,2));
