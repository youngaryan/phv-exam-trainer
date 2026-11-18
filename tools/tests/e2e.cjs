'use strict';
const {chromium}=require('playwright');
const path=require('path'),fs=require('fs'),assert=require('node:assert/strict');
const {pathToFileURL}=require('url');
const root=path.resolve(__dirname,'../..'),url=pathToFileURL(path.join(root,'app/index.html')).href;
const report={started:new Date().toISOString(),checks:[],consoleErrors:[],externalRequests:[]};
let browser,page,context;
async function click(action,extra=''){await page.locator('[data-action="'+action+'"]'+extra).first().click();}
async function shot(name){await page.screenshot({path:path.join(root,'docs/screenshots/test-'+name+'.png'),fullPage:true});}
async function fresh(){await page.goto(url);await page.evaluate(()=>localStorage.clear());await page.reload();await page.waitForSelector('.assessment-card');}
async function mock(exam){await click('choose','[data-exam="'+exam+'"]');await click('instructions-next');await click('begin');await page.waitForSelector('.exam');}
async function qdata(){return page.evaluate(()=>({q:window.PHV_UI.question,a:window.PHV.state.attempt}));}
async function completeCloze(q,drag){
 if(drag){for(const [key,word] of Object.entries(q.blanks)){await page.locator('.word-bank [data-word]').filter({hasText:word}).filter({visible:true}).first().count();const tile=page.locator('.word-bank [data-word]').filter({hasText:new RegExp('^'+word.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'$')});await tile.dragTo(page.locator('.blank-slot[data-blank="'+key+'"]'));}
   for(const word of q.wordBank.filter(w=>!Object.values(q.blanks).includes(w))){await page.locator('.word-bank [data-word]').filter({hasText:new RegExp('^'+word.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'$')}).dragTo(page.locator('.discard-box'));}
 }else for(const [key,word]of Object.entries(q.blanks))await page.locator('select[data-blank="'+key+'"]').selectOption(word);
}
async function plot(points){
 for(const p of points){const pos=await page.evaluate(p=>{const m=window.PHV_UI.map;m.setView(p,17,{animate:false});const xy=m.latLngToContainerPoint(p),r=m.getContainer().getBoundingClientRect();return{x:r.left+xy.x,y:r.top+xy.y};},p);await page.mouse.click(pos.x,pos.y);}
}
async function answerCurrent(drag=true,plotRoute=true){const {q}=await qdata();if(q.type==='cloze')await completeCloze(q,drag);else if(q.type==='route'){if(plotRoute)await plot(q.optimalGeometry);}else if(q.type==='multi'){for(const i of q.answer)await page.locator('input[name="answer"][value="'+i+'"]').check();}else await page.locator('input[name="answer"][value="'+q.answer+'"]').check();return q;}
async function finish(){await click('review');await click('finish-confirm');await page.locator('dialog [data-action="finish"]').click();await page.waitForSelector('.result-hero');}
async function settings(values){await click('nav','[data-page="settings"]');for(const [key,value]of Object.entries(values)){const el=page.locator('[name="'+key+'"]');if(typeof value==='boolean')await el.setChecked(value);else if(key==='candidate')await el.fill(value);else await el.selectOption(value);}await page.locator('#settings-form button[type="submit"]').click();await click('nav','[data-page="home"]');}
(async()=>{
 browser=await chromium.launch({channel:process.env.PHV_BROWSER_CHANNEL||'msedge',headless:true});context=await browser.newContext({viewport:{width:1440,height:960},offline:true,acceptDownloads:true});page=await context.newPage();page.on('pageerror',error=>report.consoleErrors.push(error.message));page.on('console',msg=>{if(msg.type()==='error')report.consoleErrors.push(msg.text());});page.on('request',request=>{if(/^https?:/.test(request.url()))report.externalRequests.push(request.url());});
 await fresh();await shot('home');assert.equal(await page.locator('.assessment-card').count(),2);report.checks.push('Home works from file:// with network disabled.');
 await mock('seru');let first=await qdata();assert.equal(first.a.ids.length,37);assert.equal(first.a.duration,2700);await click('flag');await click('review');assert.equal(await page.locator('.review-question.flagged').count(),1);await shot('review');await click('jump','[data-index="0"]');
 const types=new Set();for(let i=0;i<37;i++){
   let {q}=await qdata();types.add(q.type);
   if(q.type==='cloze'&&!report.checks.includes('Drag red-box rule blocks incomplete disposal.')){const [key,word]=Object.entries(q.blanks)[0];await page.locator('.word-bank [data-word]').filter({hasText:new RegExp('^'+word+'$')}).click();await page.locator('[data-blank="'+key+'"]').click();await click('next');assert.equal((await qdata()).q.id,q.id);assert(await page.locator('.cloze-warning').isVisible());report.checks.push('Drag red-box rule blocks incomplete disposal.');await page.locator('[data-blank="'+key+'"]').click();}
   await answerCurrent(true);if(!report.checks.includes('Screen captured: '+q.type)){await shot('seru-'+q.type);report.checks.push('Screen captured: '+q.type);}
   if(i===0){await page.reload();assert.equal((await qdata()).a.answers[q.id]!==undefined,true);report.checks.push('Answers and flags survive refresh.');}
   if(i<36)await click('next');
 }
 assert.deepEqual([...types].sort(),['cloze','mcq','reading']);assert.equal(await page.locator('[data-action="next"]').count(),0);await finish();assert.equal(await page.locator('.score-ring strong').innerText(),'100%');await shot('seru-results');report.checks.push('Full SERU A mock: 37 questions, all types, drag-and-drop, 100%.');
 await settings({preset:'B',blankStyle:'dropdown',candidate:'Offline Candidate'});await mock('seru');assert.equal((await qdata()).a.ids.length,36);assert.equal((await qdata()).a.duration,3600);for(let i=0;i<36;i++){await answerCurrent(false);if(i<35)await click('next');}await finish();assert.equal(await page.locator('.score-ring strong').innerText(),'100%');report.checks.push('Full SERU B mock: 36 questions, dropdowns, 60-minute timer, 100%.');
 await click('home');await mock('seru');await page.evaluate(()=>{window.PHV.state.attempt.deadline=Date.now()-1000;window.PHV.save();});await page.waitForSelector('.result-hero');assert(await page.getByText('The timer reached zero and your answers were submitted automatically.').isVisible());report.checks.push('Timer automatically submits saved answers.');
 if(process.argv.includes('--seru-only')){assert.deepEqual(report.externalRequests,[]);assert.deepEqual(report.consoleErrors,[]);report.ok=true;return;}
 await click('home');await mock('topo');assert.equal((await qdata()).a.ids.length,24);assert.equal((await qdata()).a.duration,4200);let routeCount=0;
 for(let i=0;i<24;i++){const q=await answerCurrent(false,true);if(q.type==='route'){routeCount++;await shot('topo-route-'+q.routeType);}else if(i===0)await shot('topo-static');if(i<23)await click('next');}
 assert.equal(routeCount,3);await click('legend').catch(()=>{});if(await page.locator('dialog[open]').count()){await shot('legend');await click('close-dialog');}await finish();const topo=await page.evaluate(()=>window.PHV.state.history[0]);assert.equal(topo.total,100);assert.equal(topo.score,100,JSON.stringify(topo.results.filter(r=>!r.correct)));await shot('topo-results');report.checks.push('Full Topographical mock: 3 plotted optimal routes + 21 map questions, 100/100.');
 await click('home');await click('nav','[data-page="settings"]');const downloadPromise=page.waitForEvent('download');await click('export');const download=await downloadPromise;const downloaded=await download.path();const json=JSON.parse(fs.readFileSync(downloaded,'utf8'));assert(json.history.length>=4);await page.locator('#import-file').setInputFiles({name:'backup.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(json))});await click('confirm-import');assert.equal(await page.evaluate(()=>window.PHV.state.history.length),json.history.length);report.checks.push('Progress export/import round trip.');
 await page.setViewportSize({width:900,height:700});await shot('compact-home');assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);report.checks.push('Compact layout has no horizontal overflow.');
 assert.deepEqual(report.externalRequests,[],'zero HTTP requests at runtime');assert.deepEqual(report.consoleErrors,[],'zero browser console errors');report.ok=true;
})().catch(error=>{report.ok=false;report.error=error.stack;console.error(error);process.exitCode=1;}).finally(async()=>{report.finished=new Date().toISOString();fs.writeFileSync(path.join(root,'docs/e2e-report.json'),JSON.stringify(report,null,2));if(browser)await browser.close();console.log(JSON.stringify(report,null,2));});
