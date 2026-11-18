'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
function context(data){const window={PHV_MAP:data};vm.createContext(window);window.window=window;for(const name of ['app/data/config.js','app/js/routing.js'])vm.runInContext(fs.readFileSync(path.join(root,name),'utf8'),window);return window;}
const p=(id,lat,lng)=>({id,lat,lng});
const nodes=[p('s',51.5,-.12),p('a',51.5,-.119),p('b',51.501,-.119),p('e',51.501,-.12)];
const edge=(id,from,to,oneway=false)=>({id,from,to,oneway,name:id,length:from==='s'||from==='b'?69.2:111.2,geometry:[nodes.find(n=>n.id===from),nodes.find(n=>n.id===to)].map(n=>[n.lat,n.lng])});
const data={nodes,edges:[edge('sa','s','a',true),edge('ab','a','b'),edge('ba','b','a'),edge('be','b','e'),edge('eb','e','b'),edge('es','e','s'),edge('se','s','e')],restrictions:[]};
const w=context(data),R=w.PHV_Routing;
const q={start:'s',end:'b',optimalEdges:['sa','ab'],optimalLength:180.4,closedEdges:[]};
assert.equal(R.grade(q,[[51.5,-.12],[51.5,-.119],[51.501,-.119]],22).score,22,'legal optimal route');
assert.equal(R.grade(q,[[51.501,-.119],[51.5,-.119],[51.5,-.12]],22).score,0,'reversed route');
assert.equal(R.grade(q,[],22).score,0,'unanswered route');
const closed=R.grade({...q,closedEdges:['ab']},[[51.5,-.12],[51.5,-.119],[51.501,-.119]],22);
assert(closed.score<22 && closed.details.some(s=>s.includes('Closed road')),'closed-road deduction');
const wrong=R.grade({start:'a',end:'s',optimalLength:69.2},[[51.5,-.119],[51.5,-.12]],22);
assert(wrong.score<22 && wrong.details.some(s=>s.includes('Wrong way')),'one-way deduction');
const off=R.grade(q,[[51.5,-.12],[51.501,-.119]],22);assert(off.score<22&&off.details.some(s=>s.includes('road network')),'diagonal crossing must not snap to the legal dog-leg');
data.restrictions=[{fromEdge:'sa',viaNode:'a',toEdge:'ab',type:'no_turn'}];
const restricted=context(data).PHV_Routing.grade(q,[[51.5,-.12],[51.5,-.119],[51.501,-.119]],22);assert(restricted.score<22&&restricted.details.some(s=>s.includes('Prohibited turn')),'turn restriction');
console.log('PASS: endpoint, reverse, closure, one-way, off-road and prohibited-turn marking tests.');
if(process.argv.includes('--bank')){
 const world={window:{}};vm.createContext(world);for(const name of ['app/data/config.js','app/data/map_data.js','app/data/topo_bank.js','app/js/routing.js'])vm.runInContext(fs.readFileSync(path.join(root,name),'utf8'),world);
 const r=world.window.PHV_Routing,qs=world.window.TOPO_BANK.filter(q=>q.type==='route');let errors=[];
 for(const q of qs){const result=r.grade(q,q.optimalGeometry||r.optimalPoints(q),22);if(result.score!==22)errors.push({id:q.id,score:result.score,details:result.details});}
 if(errors.length){console.error(JSON.stringify(errors.slice(0,12),null,2));throw Error(errors.length+' official computed optimal paths did not receive full simulator marks.');}
 console.log('PASS: all '+qs.length+' map-derived optimal routes receive full marks.');
}
