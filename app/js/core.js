(function () {
  'use strict';
  const C = window.PHV_CONFIG;
  const KEY = 'phv-exam-trainer-v1';
  const empty = () => ({schema:1,settings:Object.assign({},C.defaults),attempt:null,history:[],seen:{},mistakes:{}});
  let storageWarning = '';
  function valid(data) {
    if (!data || data.schema !== 1 || !data.settings || !Array.isArray(data.history) || !data.seen || !data.mistakes) throw Error('This is not a PHV Trainer progress file.');
    if (data.history.length > 1000 || typeof data.settings.candidate !== 'string' || data.settings.candidate.length > 80) throw Error('Progress file contains invalid values.');
    function checkSettings(s){if(!s||typeof s.candidate!=='string'||s.candidate.length>80||!C.presets[s.preset]||!['drag','dropdown'].includes(s.blankStyle)||!['real','assisted'].includes(s.drawingMode))throw Error('Invalid settings in progress file.');for(const k of ['practiceTimer','partialCredit','clozeBlocking'])if(typeof s[k]!=='boolean')throw Error('Invalid setting: '+k);}
    checkSettings(data.settings);
    const questions = new Map([...(window.SERU_BANK || []),...(window.TOPO_BANK || [])].map(q=>[q.id,q])),ids=new Set(questions.keys());
    const object=value=>value&&typeof value==='object'&&!Array.isArray(value);
    const coords=points=>Array.isArray(points)&&points.length<=10000&&points.every(p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite)&&Math.abs(p[0])<=90&&Math.abs(p[1])<=180);
    function checkAttempt(a,finished) {
      if (!a || typeof a.id!=='string' || !['seru','topo'].includes(a.exam) || !['mock','practice','mistakes'].includes(a.mode) || !Array.isArray(a.ids) || !a.ids.length || a.ids.length > 600 || a.ids.some(id=>!ids.has(id)) || new Set(a.ids).size!==a.ids.length || !object(a.answers) || !Array.isArray(a.flags) || a.flags.some(id=>!a.ids.includes(id)) || !Number.isFinite(a.started) || !Number.isFinite(a.duration) || a.duration<=0 || !a.settings) throw Error('Attempt data is invalid or belongs to a different question pack.');
      checkSettings(a.settings);
      if(!object(a.marks)||a.ids.some(id=>!Number.isFinite(a.marks[id])||a.marks[id]<=0||a.marks[id]>100))throw Error('Invalid question marks.');
      if (!Number.isInteger(a.index) || a.index<0 || a.index>=a.ids.length || (a.deadline!==null && !Number.isFinite(a.deadline))) throw Error('Invalid attempt position or timer.');
      for (const id of Object.keys(a.answers)) {
        if (!a.ids.includes(id)) throw Error('Answer does not belong to the attempt.');
        const ans=a.answers[id],q=questions.get(id);
        if(q.type==='route'){if(!object(ans)||!coords(ans.points)||(ans.undo!==undefined&&(!Array.isArray(ans.undo)||ans.undo.some(i=>!Number.isInteger(i)||i<0||i>ans.points.length))))throw Error('Invalid route coordinates.');}
        else if(q.type==='cloze'){if(!object(ans)||!object(ans.blanks)||!Array.isArray(ans.discarded)||Object.entries(ans.blanks).some(([k,v])=>!Object.hasOwn(q.blanks,k)||!q.wordBank.includes(v))||ans.discarded.some(w=>!q.wordBank.includes(w))||new Set(ans.discarded).size!==ans.discarded.length)throw Error('Invalid sentence-completion answer.');}
        else if(q.type==='multi'){if(!Array.isArray(ans)||ans.length>q.answer.length||new Set(ans).size!==ans.length||ans.some(i=>!Number.isInteger(i)||i<0||i>=q.options.length))throw Error('Invalid multiple-choice selection.');}
        else if(!Number.isInteger(ans)||ans<0||ans>=q.options.length)throw Error('Invalid multiple-choice answer.');
      }
      if(finished){
        if(!Number.isFinite(a.finished)||!Number.isFinite(a.timeUsed)||a.timeUsed<0||!Number.isFinite(a.score)||!Number.isFinite(a.total)||a.total<=0||a.score<0||a.score>a.total||!Array.isArray(a.results)||a.results.length!==a.ids.length)throw Error('Invalid completed attempt.');
        for(let i=0;i<a.results.length;i++){const r=a.results[i];if(!r||r.id!==a.ids[i]||r.total!==a.marks[r.id]||!Number.isFinite(r.score)||r.score<0||r.score>r.total||typeof r.correct!=='boolean'||!Array.isArray(r.details)||r.details.some(d=>typeof d!=='string'))throw Error('Invalid result marks.');if(questions.get(r.id).type==='route'&&(!Number.isFinite(r.length)||!Array.isArray(r.streets)||r.streets.some(v=>typeof v!=='string')||!Array.isArray(r.violations)||r.violations.some(v=>!coords(v.points)||typeof v.label!=='string')))throw Error('Invalid route feedback.');}
        if(Math.abs(a.results.reduce((n,r)=>n+r.score,0)-a.score)>.000001||a.results.reduce((n,r)=>n+r.total,0)!==a.total)throw Error('Inconsistent result totals.');
      }
    }
    if(data.attempt) checkAttempt(data.attempt,false);
    data.history.forEach(a=>checkAttempt(a,true));
    for(const idsSeen of Object.values(data.seen)) if(!Array.isArray(idsSeen)||idsSeen.some(id=>typeof id!=='string')) throw Error('Invalid question history.');
    for(const m of Object.values(data.mistakes)) if(!m || !Number.isFinite(m.due)||!Number.isFinite(m.streak)) throw Error('Invalid revision queue.');
    return data;
  }
  function read() {
    try { const raw=localStorage.getItem(KEY); return raw?valid(JSON.parse(raw)):empty(); }
    catch(e) {storageWarning='Saved progress could not be read. This session will still work; export your progress before closing.'; return empty();}
  }
  let state = read();
  function save() { try {localStorage.setItem(KEY,JSON.stringify(state));} catch(e) {storageWarning='Your browser could not save progress. Export it before closing this window.';} }
  function replace(data) {state=valid(data);save();}
  function reset() {state=empty();save();}
  function shuffle(arr) {const a=arr.slice();for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
  function draw(pool,count,key) {
    if(pool.length<count) throw Error('The question bank has too few items for this selection.');
    let seen=new Set(state.seen.all||Object.values(state.seen).flat()), fresh=shuffle(pool.filter(q=>!seen.has(q.id))), picked=fresh.slice(0,count);
    if(picked.length<count){const poolIds=new Set(pool.map(q=>q.id));seen=new Set(Array.from(seen).filter(id=>!poolIds.has(id)));const used=new Set(picked.map(q=>q.id));picked=picked.concat(shuffle(pool.filter(q=>!used.has(q.id))).slice(0,count-picked.length));}
    picked.forEach(q=>seen.add(q.id));state.seen={all:Array.from(seen)};return picked;
  }
  function answered(q,a) {
    if(a===undefined || a===null) return false;
    if(q.type==='route') return !!(a.points&&a.points.length>=2);
    if(q.type==='cloze') return Object.keys(q.blanks).every(k=>a.blanks&&a.blanks[k]!==undefined&&a.blanks[k]!=='');
    if(q.type==='multi') return Array.isArray(a)&&a.length===(Array.isArray(q.answer)?q.answer.length:2);
    return Number.isInteger(a);
  }
  function mark(q,a,settings,marks) {
    const total=marks===undefined?(q.marks||1):marks;
    if(q.type==='route') return window.PHV_Routing.grade(q,(a&&a.points)||[],total);
    if(q.type==='cloze') {
      const keys=Object.keys(q.blanks), n=keys.filter(k=>a&&a.blanks&&String(a.blanks[k]).trim()===q.blanks[k]).length;
      return {score:settings.partialCredit?total*n/keys.length:(n===keys.length?total:0),total,correct:n===keys.length,details:[n+' of '+keys.length+' blanks correct']};
    }
    const ok=q.type==='multi'?Array.isArray(a)&&a.length===q.answer.length&&q.answer.every(x=>a.includes(x)):a===q.answer;
    return {score:ok?total:0,total,correct:ok,details:[]};
  }
  window.PHV = {get state(){return state;},get warning(){return storageWarning;},save,replace,reset,valid,shuffle,draw,answered,mark};
}());
