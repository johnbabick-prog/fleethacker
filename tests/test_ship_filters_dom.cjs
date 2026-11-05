const {JSDOM}=require('jsdom');const assert=require('node:assert/strict');
const base=process.env.FLEET_TEST_URL||'http://localhost:8765/';
(async()=>{
 const rows=await(await fetch(new URL('/api/watch',base))).json();
 const fixture=rows.map(r=>({...r,draft:{...r.draft,ship_id:'',equipment_id:''}}));
 const first=fixture.find(r=>r.job.id==='DEMO-11'),second=fixture.find(r=>r.job.id==='DEMO-12');
 for(const [row,equipment] of [[first,'spy1'],[second,'sqq89']])Object.assign(row.draft,{ship_id:'DDG-51',ship_name:'USS Arleigh Burke',hull_number:'DDG-51',ship_class:'Arleigh Burke (DDG)',owner:'FC1 Ochoa',equipment_id:'DDG-51::'+equipment});
 const posts=[];
 const html=await(await fetch(base)).text();const script=await(await fetch(new URL('/app.js',base))).text();
 const makeDOM=(saved='')=>new JSDOM(html,{url:base,runScripts:'outside-only',beforeParse(w){if(saved)w.localStorage.setItem('fleet-current-ship',saved);w.HTMLElement.prototype.scrollIntoView=function(){};w.fetch=(u,o)=>{const url=new URL(u,base);if(o?.method==='POST')posts.push(url.pathname);if(url.pathname==='/api/watch')return Promise.resolve({ok:true,json:async()=>fixture});if(url.pathname.endsWith('/maintenance-sailors'))return Promise.resolve({ok:true,json:async()=>({sailors:url.pathname.includes('DDG-51')?[{name:'FC1 Ochoa'}]:[]})});return fetch(url,o)}}});
 const dom=makeDOM();const d=dom.window.document;
 async function until(fn){for(let i=0;i<100;i++){if(fn())return;await new Promise(r=>setTimeout(r,30));}throw Error('Timed out');}
 try{
  dom.window.eval(script);await until(()=>d.getElementById('watch-ship-status').textContent.includes('remembered'));assert.equal(d.querySelectorAll('#jobs [data-open-job]').length,0);assert.equal(d.querySelectorAll('#today-schedule [data-open-job]').length,0);
  assert.ok(d.querySelector('details#maintenance-steps > summary'));
  assert.ok(d.querySelector('#maintenance-steps #procedure-content'));
  assert.ok(d.querySelector('details#problem-report > summary'));
  assert.ok(d.querySelector('#problem-report .class-history-top'));
  assert.ok(d.querySelector('#problem-report #problem-saved-photos'));
  assert.equal(d.getElementById('problem-report').hidden,false);
  assert.ok(d.querySelector('#work #ship-search'));assert.ok(!d.querySelector('#procedure #ship-search'));assert.ok(d.querySelector('#procedure #equipment-search'));
  await dom.window.selectDirectoryShip('DDG-51');
  assert.deepEqual([...d.getElementById('watch-sailor').options].map(o=>o.value),['','FC1 Ochoa']);
  assert.equal(d.querySelectorAll('#jobs [data-open-job]').length,2);
  assert.equal(d.getElementById('draft-owner').selectedOptions[0].textContent,'All sailors');
  assert.deepEqual([...d.getElementById('procedure-job').options].map(o=>o.value).filter(Boolean),['DEMO-11','DEMO-12']);
  d.getElementById('equipment-selector').value='DDG-51::spy1';await d.getElementById('equipment-selector').onchange();
  assert.deepEqual([...d.getElementById('procedure-job').options].map(o=>o.value).filter(Boolean),['DEMO-11']);
  assert.match(d.getElementById('procedure-job').textContent,/FC1 Ochoa/);
  assert.equal(d.getElementById('equipment-document-equipment').value,'DDG-51::spy1');
  assert.match(d.getElementById('equipment-upload-destination').textContent,/AN\/SPY-1D/);
  d.getElementById('watch-sailor').value='FC1 Ochoa';await d.getElementById('watch-sailor').onchange();
  await until(()=>d.getElementById('equipment-selector').querySelector('[value="DDG-51::spy1"]'));
  dom.window.renderEquipmentOptions('');
  assert.match(d.querySelector('[data-select-equipment="DDG-51::spy1"] .equipment-workload').textContent,/1 open · 1 assigned to FC1 Ochoa/);
  assert.match(d.querySelector('[data-select-equipment="DDG-51::lm2500"] .equipment-workload').textContent,/0 open/);
  d.getElementById('equipment-selector').value='DDG-51::spy1';await d.getElementById('equipment-selector').onchange();
  assert.deepEqual([...d.getElementById('procedure-job').options].map(o=>o.value).filter(Boolean),['DEMO-11']);
  d.getElementById('equipment-selector').value='DDG-51::sqq89';await d.getElementById('equipment-selector').onchange();
  assert.deepEqual([...d.getElementById('procedure-job').options].map(o=>o.value).filter(Boolean),['DEMO-12']);
  assert.equal(d.getElementById('equipment-document-equipment').value,'DDG-51::sqq89');
  assert.equal(dom.window.localStorage.getItem('fleet-current-ship'),'DDG-51');
  const restored=makeDOM(dom.window.localStorage.getItem('fleet-current-ship'));
  try{restored.window.eval(script);await until(()=>restored.window.document.querySelectorAll('#jobs [data-open-job]').length===2);assert.equal(restored.window.document.getElementById('ship-search').value,'USS Arleigh Burke');}finally{restored.window.close()}
  await dom.window.selectDirectoryShip('');assert.equal(dom.window.localStorage.getItem('fleet-current-ship'),null);assert.equal(d.querySelectorAll('#jobs [data-open-job]').length,0);assert.equal(d.querySelectorAll('#today-schedule [data-open-job]').length,0);
  await dom.window.selectDirectoryShip('CVN-72');
  assert.equal(d.getElementById('watch-sailor').options.length,1);assert.ok(d.getElementById('watch-sailor').disabled);assert.equal(d.querySelectorAll('#jobs [data-open-job]').length,0);
  assert.equal(posts.length,0,'Filtering must not mutate job assignments');
  console.log('Ship selection, recorded sailors, equipment filtering and non-mutating navigation passed.');
 }finally{dom.window.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
