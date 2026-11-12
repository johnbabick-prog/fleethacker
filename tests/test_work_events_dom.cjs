const {JSDOM}=require('jsdom'),assert=require('node:assert/strict');
const base=process.env.FLEET_TEST_URL||'http://localhost:8765/';
(async()=>{
 let sent;
 const dom=new JSDOM(await(await fetch(base)).text(),{url:base,runScripts:'outside-only',beforeParse(w){
  w.HTMLElement.prototype.scrollIntoView=function(){};
  w.fetch=(u,o)=>{const url=new URL(u,base);if(o?.method==='POST'){
   assert.equal(url.pathname,'/api/work-events');sent=JSON.parse(o.body);
   return Promise.resolve({ok:true,json:async()=>({job:{id:'WO-TEST'},draft:{owner:sent.owner},schedule:{due_date:sent.due_date}})});
  }return fetch(url,o)};
 }});
 const d=dom.window.document;async function until(fn){for(let i=0;i<100;i++){if(fn())return;await new Promise(r=>setTimeout(r,30))}throw Error('Timed out')}
 try{
  dom.window.eval(await(await fetch(new URL('/app.js',base))).text());await until(()=>d.getElementById('watch-ship-status').textContent.includes('remembered'));
  d.getElementById('new-event-menu').open=true;await dom.window.loadNewEventOptions();assert.equal(d.getElementById('new-event-fields').disabled,true);
  await dom.window.selectDirectoryShip('DDG-76');await until(()=>!d.getElementById('new-event-fields').disabled);
  assert.match(d.getElementById('new-event-ship').textContent,/Higgins/);
  const equipment=d.getElementById('new-event-equipment');equipment.value='DDG-76::water-cooler';equipment.onchange();
  d.getElementById('new-event-title').value='Investigate teller power loss';d.getElementById('new-event-owner').value='FC3 Kluzak';
  d.getElementById('new-event-type').value='corrective';d.getElementById('new-event-date').value='2026-11-05';d.getElementById('new-event-time').value='14:30';d.getElementById('new-event-description').value='No power lights';
  await d.getElementById('new-event-form').onsubmit({preventDefault(){}});
  assert.equal(sent.ship_id,'DDG-76');assert.equal(sent.equipment_id,'DDG-76::water-cooler');assert.equal(sent.owner,'FC3 Kluzak');assert.equal(sent.corrective,true);assert.equal(sent.time,'14:30');
  assert.match(d.getElementById('new-event-status').textContent,/WO-TEST created/);assert.ok(d.querySelector('#new-event-status button'));assert.equal(d.getElementById('new-event-submit').disabled,false);
  console.log('New maintenance form requires a ship, submits equipment and sailor assignments, and confirms creation.');
 }finally{await new Promise(r=>setTimeout(r,100));dom.window.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
