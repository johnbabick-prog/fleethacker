const {JSDOM}=require('jsdom');const assert=require('node:assert/strict');
const base=process.env.FLEET_TEST_URL||'http://localhost:8765/';
(async()=>{
 const rows=await(await fetch(new URL('/api/watch',base))).json();
 const row=rows.find(r=>r.job.id==='DEMO-12');Object.assign(row.draft,{ship_id:'DDG-76',ship_name:'USS Higgins',hull_number:'DDG-76',ship_class:'Arleigh Burke (DDG)',equipment_id:'DDG-76::lm2500',equipment:'LM2500 gas turbine',owner:'FC1 Ochoa'});
 const teller=rows.find(r=>r.job.id==='CM-4');teller.job.status='Completed locally';teller.draft.owner='FC3 Kluzak';
 const writes=[];const json=data=>({ok:true,json:async()=>structuredClone(data)});
 const dom=new JSDOM(await(await fetch(base)).text(),{url:base,runScripts:'outside-only',beforeParse(w){
  w.localStorage.setItem('fleet-current-ship','DDG-76');w.HTMLElement.prototype.scrollIntoView=function(){};
  w.HTMLDialogElement.prototype.showModal=function(){this.open=true};w.HTMLDialogElement.prototype.close=function(){this.open=false};
  w.fetch=(u,o)=>{const url=new URL(u,base),path=url.pathname;
   if(path==='/api/watch')return Promise.resolve(json(rows));
   if(path.endsWith('/maintenance-sailors'))return Promise.resolve(json({sailors:[...new Set(rows.map(r=>r.draft.owner).filter(Boolean))].map(name=>({name}))}));
   if(path==='/api/jobs/DEMO-12/draft')return Promise.resolve(json(row.draft));
   if(path.endsWith('/assignments'))return Promise.resolve(json([]));
   if(o?.method==='POST'){
    assert.equal(path,'/api/jobs/DEMO-12/assignment');const body=JSON.parse(o.body);writes.push(body);
    row.draft={...row.draft,owner:body.owner,version:row.draft.version+1};return Promise.resolve(json(row.draft));
   }
   return fetch(url,o);
  };
 }});
 const d=dom.window.document;async function until(fn){for(let i=0;i<100;i++){if(fn())return;await new Promise(r=>setTimeout(r,30));}throw Error('Timed out');}
 try{
  dom.window.eval(await(await fetch(new URL('/app.js',base))).text());await until(()=>d.querySelector('#today-schedule [data-open-job="DEMO-12"]'));
  await dom.window.startJob('DEMO-12');const steps=d.querySelectorAll('[data-complete-step]').length;assert.ok(steps>0);
  assert.equal(d.getElementById('reassign-job').disabled,false);
  await d.getElementById('reassign-job').onclick();assert.ok(d.getElementById('assignment-dialog').open);
  d.getElementById('assignment-new-owner').value='FC2 Rivera';d.getElementById('assignment-reason').value='Leave coverage';
  await d.getElementById('assignment-form').onsubmit({preventDefault(){}});
  assert.equal(writes.length,1);assert.equal(writes[0].owner,'FC2 Rivera');assert.equal(writes[0].reason,'Leave coverage');
  assert.equal(d.getElementById('draft-owner').value,'FC2 Rivera');assert.equal(d.getElementById('procedure-job').value,'DEMO-12');
  assert.equal(d.querySelectorAll('[data-complete-step]').length,steps);
  assert.ok([...d.getElementById('watch-sailor').options].some(o=>o.value==='FC2 Rivera'));
  assert.equal(d.getElementById('assignment-dialog').open,false);
  assert.match(d.getElementById('assignment-status').textContent,/Progress and notes preserved/);
  assert.equal(d.getElementById('workspace-sailor').disabled,false);
  d.getElementById('workspace-sailor').value='FC3 Kluzak';await d.getElementById('workspace-sailor').onchange();
  assert.equal(writes.length,1,'Browsing another sailor must not reassign work');
  assert.equal(row.draft.owner,'FC2 Rivera');
  d.getElementById('equipment-selector').value='';await d.getElementById('equipment-selector').onchange();
  assert.ok([...d.getElementById('procedure-job').options].some(o=>o.value==='CM-4'));
  dom.window.renderEquipmentOptions('');
  const tellerLabel=d.querySelector('[data-select-equipment="DDG-76::water-cooler"] .equipment-workload').textContent;
  assert.match(tellerLabel,/0 open/);assert.match(tellerLabel,/1 completed/);assert.match(tellerLabel,/Work orders: FC3 Kluzak/);
  d.getElementById('workspace-sailor').value='';await d.getElementById('workspace-sailor').onchange();
  assert.ok([...d.getElementById('procedure-job').options].some(o=>o.value==='DEMO-12'));
  console.log('Assignment dialog transfers ownership, retains checklist and updates sailor selectors.');
 }finally{await new Promise(resolve=>setTimeout(resolve,500));dom.window.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
