'use strict';
const fs=require('fs'),vm=require('vm'),path=require('path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
function load(blocked=false){const data=new Map();const w={window:{},localStorage:{getItem(k){if(blocked)throw Error('Storage blocked');return data.get(k)||null;},setItem(k,v){if(blocked)throw Error('Storage blocked');data.set(k,v);}}};vm.createContext(w);for(const f of ['app/data/config.js','app/data/seru_bank.js','app/js/core.js'])vm.runInContext(fs.readFileSync(path.join(root,f),'utf8'),w);return w.window;}
const w=load(),p=w.PHV,q=w.SERU_BANK.find(q=>q.type==='mcq'),cloze=w.SERU_BANK.find(q=>q.type==='cloze');
const base=()=>JSON.parse(JSON.stringify({schema:1,settings:w.PHV_CONFIG.defaults,history:[],seen:{},mistakes:{},attempt:{id:'test',exam:'seru',mode:'mock',ids:[q.id],index:0,answers:{},flags:[],started:Date.now(),deadline:Date.now()+2700000,duration:2700,settings:w.PHV_CONFIG.defaults,marks:{[q.id]:1}}}));
assert(p.valid(base()));
for(const mutate of [d=>delete d.attempt.marks,d=>d.attempt.marks[q.id]=-10,d=>d.attempt.answers[q.id]=999,d=>d.attempt.settings={},d=>{d.attempt.ids=[cloze.id];d.attempt.marks={[cloze.id]:1};d.attempt.answers[cloze.id]={blanks:{},discarded:'invalid'};}]){const d=base();mutate(d);assert.throws(()=>p.valid(d));}
const partial=p.mark(cloze,{blanks:{[Object.keys(cloze.blanks)[0]]:Object.values(cloze.blanks)[0]}},{partialCredit:true},1);assert.equal(partial.score,.5);assert.equal(p.mark(cloze,{blanks:{}},{partialCredit:false},1).score,0);
const pool=w.SERU_BANK.filter(q=>q.type==='mcq').slice(0,12),first=p.draw(pool,5,'first'),second=p.draw(pool,5,'second');assert(!first.some(q=>second.some(r=>q.id===r.id)),'shared seen list must prevent repeated questions across selection keys');const third=p.draw(pool,5,'third');assert.equal(new Set(third.map(q=>q.id)).size,5,'recycling never duplicates within a draw');
const blocked=load(true);assert(blocked.PHV.warning);blocked.PHV.save();assert(blocked.PHV.warning);assert.equal(blocked.PHV.state.history.length,0);
console.log('PASS: import validation, cloze partial credit, question recycling and unavailable-storage fallback.');
