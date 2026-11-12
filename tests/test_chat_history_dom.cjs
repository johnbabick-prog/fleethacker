const {JSDOM}=require('jsdom');const assert=require('node:assert/strict');
const base=process.env.FLEET_TEST_URL||'http://localhost:8765/';
(async()=>{
 const html=await(await fetch(base)).text(),script=await(await fetch(new URL('/app.js',base))).text();
 const rows=await(await fetch(new URL('/api/watch',base))).json(),row=rows.find(r=>r.job.id==='DEMO-12');
 Object.assign(row.draft,{ship_id:'DDG-76',ship_name:'USS Higgins',hull_number:'DDG-76',ship_class:'Arleigh Burke (DDG)',equipment_id:'DDG-76::lm2500',owner:'FC1 Ochoa'});
 const chats=new Map(),sent=[],symptomQueries=[];const json=d=>Promise.resolve({ok:true,json:async()=>structuredClone(d)});
 const make=(last='')=>new JSDOM(html,{url:base,runScripts:'outside-only',beforeParse(w){
  w.localStorage.setItem('fleet-current-ship','DDG-76');if(last){w.localStorage.setItem('fleet-last-conversation',last);w.localStorage.setItem('fleet-chat-view','assistant')}
  w.HTMLElement.prototype.scrollIntoView=function(){};w.HTMLDialogElement.prototype.showModal=function(){this.open=true};w.HTMLDialogElement.prototype.show=function(){this.open=true};w.HTMLDialogElement.prototype.close=function(){this.open=false};
  w.fetch=(u,o)=>{const url=new URL(u,base),path=url.pathname;
   if(path==='/api/watch')return json(rows);
   if(path==='/api/troubleshooting'){symptomQueries.push(url.searchParams.get('q'));return json([]);}
   if(path.endsWith('/maintenance-sailors'))return json({sailors:[{name:'FC1 Ochoa'}]});
   if(path==='/api/jobs/DEMO-12/draft'){if(o?.method==='POST')Object.assign(row.draft,JSON.parse(o.body),{version:row.draft.version+1});return json(row.draft);}
   if(path==='/api/equipment-documents/test/pages')return json({blank_candidates:[3],pages:[{page:1,kind:'Text + graphics',has_graphics:true,image_url:'/api/equipment-documents/test/pages/1/image'},{page:2,kind:'Text',has_graphics:false,image_url:'/api/equipment-documents/test/pages/2/image'},{page:3,kind:'No detected content',has_graphics:false,image_url:'/api/equipment-documents/test/pages/3/image'}]});
   if(path==='/api/conversations'){
    if(o?.method==='POST'){const body=JSON.parse(o.body),empty=[...chats.values()].find(c=>c.job_id===body.job_id&&!c.problem&&!c.messages.length);if(empty&&!body.problem)return json(empty);const c={id:'chat-'+(chats.size+1),job_id:JSON.parse(o.body).job_id,context:{ship_id:'DDG-76',equipment_id:'DDG-76::lm2500'},title:JSON.parse(o.body).problem||'New conversation',problem:JSON.parse(o.body).problem||'',created:new Date().toISOString(),updated:new Date().toISOString(),messages:[]};chats.set(c.id,c);return json(c)}
    return json([...chats.values()].filter(c=>!url.searchParams.has('job_id')||c.job_id===url.searchParams.get('job_id')).reverse());
   }
   if(path.endsWith('/findings-draft'))return json({job_id:'DEMO-12',fields:{symptom:'Door jammed',actions_taken:'Released the latch',outcome:'Technician reports it works'},mode:'Local AI draft',evidence:[]});
   if(path.startsWith('/api/conversations/'))return json(chats.get(path.split('/').pop()));
   if(path==='/api/chat/stream'){
    const q=JSON.parse(o.body);sent.push(q);const c=chats.get(q.conversation_id),ref={citation:'PDF-test-p2',title:'Manual',source:'Manual · PDF page 2',excerpt:'Check the indicated condition.',page:2,image_url:'/api/equipment-documents/test/pages/2/image'};
    c.title=q.text;c.messages.push({role:'user',content:q.text,status:'complete',time:new Date().toISOString(),context:{owner:'FC1 Ochoa'}},{role:'assistant',content:'Saved answer about the equipment. [PDF-test-p2]',status:'complete',time:new Date().toISOString(),references:[ref]});
    return Promise.resolve(new Response([{type:'references',references:[ref]},{type:'token',text:'Saved answer about the equipment. [PDF-test-p2]'},{type:'done',mode:'Local AI'}].map(e=>JSON.stringify(e)+'\n').join('')));
   }
   if(o?.method==='POST')throw Error('Unexpected write '+path);
   return fetch(url,o);
  };
 }});
 async function until(fn){for(let i=0;i<150;i++){if(fn())return;await new Promise(r=>setTimeout(r,30));}throw Error('Timed out');}
 let dom=make(),d=dom.window.document;
 try{
  dom.window.eval(script);
  assert.equal(dom.window.readableQuestion('The sailor reports: The door is jammed\n\nPropose numbered troubleshooting checks for this symptom.'),'The door is jammed');
  assert.equal(dom.window.readableQuestion('What is the night lock?'),'What is the night lock?');
  dom.window.HTMLImageElement.prototype.decode=async function(){};
  const printable=d.createElement('img');printable.src='/api/equipment-documents/test/pages/2/image';printable.alt='Document page 2';
  let printed=false;dom.window.print=()=>{printed=true;assert.equal(d.querySelector('#manual-print-page img').src,printable.src);assert.equal(d.querySelector('#manual-print-page').children.length,1)};
  await dom.window.printManualPage(printable);assert.ok(printed);dom.window.dispatchEvent(new dom.window.Event('afterprint'));assert.equal(d.querySelector('#manual-print-page'),null);
  const clean=d.createElement('div');dom.window.renderChatAnswer(clean,'Check the switch [CHAT-secret]. Report 39cbd4cb-8984-4518-829c-2b9239f8bf3b. See [PDF-test-p19].',[]);
  assert.ok(!/CHAT-|PDF-test|39cbd4cb/.test(clean.textContent));assert.match(clean.textContent,/PDF page 19/);
  await until(()=>d.querySelector('#today-schedule [data-open-job="DEMO-12"]'));
  await dom.window.startJob('DEMO-12');d.querySelector('[data-view="assistant"]').click();
  d.getElementById('chat-input').value='What did we check?';d.getElementById('side-chat').requestSubmit(d.querySelector('#side-chat button'));
  await until(()=>d.getElementById('chat-save-status').textContent.includes('Saved encrypted'));
  const id=dom.window.localStorage.getItem('fleet-last-conversation');assert.equal(id,'chat-1');
  await new Promise(r=>setTimeout(r,300));dom.window.close();dom=make(id);d=dom.window.document;dom.window.eval(script);
  await until(()=>d.querySelector('#assistant .chat-pane')&&d.getElementById('chat-messages').textContent.includes('Saved answer'));
  assert.equal(d.getElementById('procedure-job').value,'DEMO-12');assert.match(d.getElementById('chat-messages').textContent,/What did we check/);assert.ok(d.querySelector('#chat-messages a[href$="/pages/2/image"]'));
  d.getElementById('chat-input').value='What comes next?';d.getElementById('side-chat').requestSubmit(d.querySelector('#side-chat button'));
  await until(()=>sent.length===2&&!d.querySelector('.ai-busy'));
  assert.ok(sent[1].history.some(m=>m.content==='What did we check?'));assert.equal(sent[1].conversation_id,id);
  await d.getElementById('clear-chat').onclick();await d.getElementById('clear-chat').onclick();assert.equal(chats.size,2);assert.equal(d.getElementById('saved-chat-select').value,dom.window.localStorage.getItem('fleet-last-conversation'));assert.match(d.getElementById('saved-chat-select').selectedOptions[0].textContent,/New conversation/);assert.equal(chats.get(id).messages.length,4);
  chats.set('unrelated',{id:'unrelated',job_id:'DEMO-32',context:{equipment_id:'DDG-76::sonar'},title:'Unrelated sonar',updated:new Date().toISOString(),messages:[]});
  d.getElementById('saved-chats').open=true;await until(()=>d.getElementById('saved-chat-select').options.length===2);assert.match(d.getElementById('saved-chat-select').textContent,/\d+:\d{2}/);assert.ok(!d.getElementById('saved-chat-select').textContent.includes('Unrelated sonar'));chats.delete('unrelated');
  d.getElementById('saved-chat-select').value=id;await d.getElementById('open-saved-chat').onclick();assert.match(d.getElementById('chat-messages').textContent,/What comes next/);
  await d.getElementById('record-chat-outcome').onclick();
  assert.equal(d.getElementById('procedure').hidden,false);assert.equal(d.getElementById('troubleshooting-panel').open,true);
  assert.equal(d.getElementById('resolution-status').value,'not_verified');
  assert.equal(dom.window.localStorage.getItem('fleet-last-conversation'),id);
  const refBox=d.createElement('article');dom.window.savedReference(refBox,{citation:'CHAT-example',title:'Prior discussion',source:'CM-4',excerpt:'Reported symptom, not verified',conversation_id:id});
  assert.equal(refBox.querySelector('button').textContent,'Open prior conversation');
  assert.equal(d.getElementById('troubleshooting-query'),null);assert.equal(d.getElementById('find-troubleshooting'),null);
  d.getElementById('draft-symptom-report').value='The system wont turn on';d.getElementById('draft-symptom-report').dispatchEvent(new dom.window.Event('input'));
  assert.match(d.getElementById('troubleshooting-results').textContent,/Finding relevant/);
  await until(()=>symptomQueries.includes('The system wont turn on'));
  assert.match(d.getElementById('troubleshooting-results').textContent,/No relevant past fixes/);
  assert.equal(sent.length,2,'Typing a symptom must not start an AI request');
  await d.getElementById('problem-ask-ai').onclick();
  await until(()=>sent.length===3&&!d.querySelector('.ai-busy'));
  const newId=sent[2].conversation_id;assert.notEqual(newId,id);assert.equal(chats.get(newId).problem,'The system wont turn on');
  assert.equal(sent[2].history.length,0);assert.equal(chats.get(id).messages.length,4);
  assert.ok(d.querySelector('#assistant .chat-pane'));assert.match(d.getElementById('chat-thread-title').textContent,/system wont turn on/);
  const inline=d.querySelector('#chat-messages .inline-page-link');assert.ok(inline);assert.equal(inline.textContent,'PDF page 2');
  inline.click();await until(()=>d.querySelector('#cited-pdf-dialog .pdf-page-select')?.value==='2');
  assert.equal(d.getElementById('cited-pdf-dialog').open,true);
  assert.equal(d.querySelector('#cited-pdf-dialog .pdf-page-filter').value,'content');
  assert.match(d.querySelector('#cited-pdf-dialog img').src,/pages\/2\/image$/);
  assert.equal(dom.window.localStorage.getItem('fleet-last-conversation'),newId);
  d.getElementById('close-cited-pdf').click();assert.equal(d.getElementById('cited-pdf-dialog').open,false);
  assert.ok(d.querySelector('#chat-messages .chat-page-links button'));

  const savedCount=chats.get(newId).messages.length;
  await d.getElementById('clear-checks').onclick();
  assert.equal(dom.window.localStorage.getItem('fleet-last-conversation'),null);
  assert.match(d.getElementById('chat-messages').textContent,/Conversation closed/);
  assert.equal(chats.get(newId).messages.length,savedCount);
  await dom.window.greetSailor();assert.match(d.getElementById('chat-messages').textContent,/Conversation closed/);
  await d.getElementById('clear-chat').onclick();
  assert.notEqual(dom.window.localStorage.getItem('fleet-last-conversation'),newId);
  assert.equal(d.getElementById('saved-chat-select').value,dom.window.localStorage.getItem('fleet-last-conversation'));assert.match(d.getElementById('saved-chat-select').selectedOptions[0].textContent,/New conversation/);
  await dom.window.openSavedConversation(newId);
  assert.match(d.getElementById('chat-messages').textContent,/Saved answer/);
  d.getElementById('chat-input').value='Continue this discussion';d.getElementById('side-chat').requestSubmit(d.querySelector('#side-chat button'));
  await until(()=>sent.length===4&&!d.querySelector('.ai-busy'));
  assert.equal(sent[3].conversation_id,newId);assert.ok(sent[3].history.length>0);
  for(const text of ['okay its fixed',"It's fixed",'It’s fixed','it is fixed now','that did it','the system is working','problem solved'])assert.equal(dom.window.reportsResolution(text),true,text);
  for(const text of ['It is not fixed',"it's not fixed",'it isnt fixed','it still doesnt work','hopefully its fixed','what if its fixed'])assert.equal(dom.window.reportsResolution(text),false,text);
  assert.equal(dom.window.reportsResolution('Should I check whether it works?'),false);
  d.getElementById('chat-input').value='okay its fixed';d.getElementById('side-chat').requestSubmit(d.querySelector('#side-chat button'));
  await until(()=>sent.length===5&&!d.getElementById('findings-review-check').hidden&&d.getElementById('draft-actions_taken').value==='Released the latch');
  assert.equal(d.getElementById('procedure').hidden,false);assert.ok(d.getElementById('troubleshooting-panel').classList.contains('needs-review'));
  assert.equal(d.getElementById('save-troubleshooting').disabled,true);
  d.getElementById('findings-reviewed').checked=true;d.getElementById('findings-reviewed').onchange();assert.equal(d.getElementById('save-troubleshooting').disabled,false);
  console.log('Saved chat survives reload, restores job and sources, supports follow-up and retains old conversations.');
 }finally{await new Promise(r=>setTimeout(r,300));dom.window.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
