/* Initial authored design A. Original code; no external assets. Keep frozen for comparison. */
(function(root){
'use strict';
const W=1280,H=720,DURATION=6;
const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
function hash(i){let x=(Math.imul(i+11,2654435761)^12721)>>>0;x^=x>>>16;return (x>>>0)/4294967296}
const stems=[{x:716,h:555,lean:-35,w:14,ink:.92},{x:535,h:452,lean:-112,w:9,ink:.56},{x:879,h:372,lean:66,w:8,ink:.45}];
function wind(t){return 0.12*Math.exp(-(((t-3.65)/.45)**2))-.025*Math.exp(-(((t-4.5)/.55)**2))}
function stemPoint(s,u,t){return {x:s.x+s.lean*u+wind(t)*s.h*u*u,y:658-s.h*u}}
function layout(t){
 t=clamp(t,0,DURATION);const branches=[];
 stems.forEach((s,si)=>{for(let k=1;k<=5;k++){
 const u=.18+k*.125,side=(k+si)%2?-1:1,anchor=stemPoint(s,u,t),l=88+35*hash(si*19+k);
 const tip={x:anchor.x+side*l,y:anchor.y-42};
 const leaves=[];for(let j=0;j<5;j++){
  const q=.32+j*.14,base={x:anchor.x+(tip.x-anchor.x)*q,y:anchor.y+(tip.y-anchor.y)*q};
  const angle=(side<0?Math.PI:0)+(j%2?-.75:.75)+wind(t-.08*j)*1.2;
  leaves.push({x:base.x,y:base.y,angle,length:67+22*hash(si*71+k*11+j),width:12,
   growth:smooth((t-(.55+u*1.6+j*.06))/.5)});
 }
 branches.push({stem:si,u,anchor,tip,side,leaves,growth:smooth((t-(.35+u*1.5))/.65)});
 }});return {t,branches};
}
function renderAt(seconds){
 if(!Number.isFinite(seconds))throw Error('finite seconds required');
 const c=document.getElementById('art'),ctx=c.getContext('2d');
 ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,W,H);ctx.fillStyle='#f1ecdf';ctx.fillRect(0,0,W,H);
 const state=layout(seconds),t=state.t;ctx.lineCap='round';ctx.lineJoin='round';
 stems.forEach(s=>{
  const g=smooth((t-.15)/2.0);ctx.strokeStyle='rgba(22,36,32,'+s.ink+')';ctx.lineWidth=s.w;
  ctx.beginPath();for(let i=0;i<=64;i++){const p=stemPoint(s,g*i/64,t);i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y)}ctx.stroke();
  for(let k=1;k<=6;k++){const u=k/7;if(u>g)continue;const p=stemPoint(s,u,t);ctx.lineWidth=3;
   ctx.beginPath();ctx.moveTo(p.x-10,p.y+2);ctx.lineTo(p.x+10,p.y+2);ctx.stroke()}
 });
 state.branches.forEach(b=>{
  const s=stems[b.stem];ctx.strokeStyle='rgba(22,36,32,'+s.ink+')';ctx.lineWidth=2;
  ctx.beginPath();ctx.moveTo(b.anchor.x,b.anchor.y);ctx.lineTo(b.anchor.x+(b.tip.x-b.anchor.x)*b.growth,b.anchor.y+(b.tip.y-b.anchor.y)*b.growth);ctx.stroke();
  b.leaves.forEach(l=>{if(l.growth<=0)return;ctx.save();ctx.translate(l.x,l.y);ctx.rotate(l.angle);
   const len=l.length*l.growth;ctx.fillStyle='rgba(22,36,32,'+s.ink+')';ctx.beginPath();ctx.moveTo(0,0);
   ctx.bezierCurveTo(len*.3,-l.width,len*.65,-l.width,len,0);
   ctx.bezierCurveTo(len*.65,l.width,len*.3,l.width,0,0);ctx.fill();ctx.restore()});
 });
 return state;
}
const api={layout,stemPoint,stems,wind,renderAt,DURATION};if(typeof module!=='undefined')module.exports=api;
root.InkBamboo=api;root.renderAt=renderAt;
})(typeof window!=='undefined'?window:globalThis);
