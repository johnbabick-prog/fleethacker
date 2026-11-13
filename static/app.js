// Keep the standalone app usable at / and when hosted under /fleethacker/.
const HATCH_BASE=(()=>{try{return new URL('.',document.baseURI).pathname.replace(/\/$/,'')}catch{return ''}})();
function hatchURL(path){return typeof path==='string'&&path.startsWith('/api/')?HATCH_BASE+path:path;}
function hatchFetch(path,options){return globalThis.fetch(hatchURL(path),options);}
let watchShipId='',workspaceEquipmentFilter='',shipSailorRequest=0,shipPreferenceLoaded=false;
const $=id=>document.getElementById(id);let state,selected;
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function renderMarkdown(text){return esc(text).replace(/^### (.+)$/gm,'<strong>$1</strong>').replace(/^## (.+)$/gm,'<strong style="font-size:15px">$1</strong>').replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/\*(.+?)\*/g,'<em>$1</em>').replace(/`([^`]+)`/g,'<code style="background:#1a2936;padding:2px 5px;border-radius:3px">$1</code>').replace(/\[(\d+)\]/g,'<span style="color:#83e0c2;font-weight:bold">[$1]</span>').replace(/^\s*[-•]\s+(.+)$/gm,'<span style="display:block;padding-left:16px">• $1</span>').replace(/\n/g,'<br>')}
async function api(path,body){const r=await hatchFetch('/api/'+path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const d=await r.json();if(!r.ok)throw Error(typeof d.detail==='string'?d.detail:JSON.stringify(d.detail));return d}
let noticeTimer=null;
function notice(s,duration=0){clearTimeout(noticeTimer);$('notice').textContent=s;if(s)$('notice').scrollIntoView({block:'nearest'});if(s&&duration)noticeTimer=setTimeout(()=>{$('notice').textContent=''},duration)}
async function refresh(){state=await api('state');if(state.shared_demo){$('sharing-banner').hidden=false;}$('metrics').innerHTML=[[state.jobs.filter(j=>j.status==='Open').length,'Open work orders','metric-open'],[state.parts.length,'Demo catalog items',''],[state.chunks.toLocaleString(),'Local reference chunks','metric-refs'],[state.events.filter(e=>!e.shore).length,'Awaiting shore receipt','metric-pending']].map(([n,l,cls])=>`<div class="metric ${cls}"><strong>${n}</strong><span>${l}</span></div>`).join('');$('parts').innerHTML=state.parts.map(p=>`<tr><td>${esc(p.name)}<br><small>${esc(p.nsn)}</small></td><td>${p.on_hand}</td><td>${p.reserved}</td><td>${esc(p.location)}</td></tr>`).join('');$('snapshot').textContent='AS OF '+state.snapshot;$('events').innerHTML=state.events.length?state.events.map(e=>`<p>${esc(e.id.slice(0,8))} · Device ✓ · Ship ${e.ship?'✓':'pending'} · Shore ${e.shore?'✓':'pending'}</p>`).join(''):'<p>No queued transactions. Complete a work order to begin.</p>';updateProcedureJobs();await loadWatch();bindHandoffs();document.querySelectorAll('[data-job]').forEach(b=>b.onclick=()=>{selected=state.jobs.find(j=>j.id===b.dataset.job);$('completion').reset();$('complete-job-context').textContent=selected.id+' · '+selected.title;$('complete').showModal()})}
function showView(view){
 if(!['work','procedure','assistant'].includes(view))view='work';
 const pane=document.querySelector('.chat-pane'),scroll=$('chat-body').scrollTop,expanded=view==='assistant';
 document.querySelectorAll('.view').forEach(v=>v.hidden=v.id!==view);
 document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('selected',b.dataset.view===view));
 document.body.classList.toggle('chat-expanded',expanded);try{localStorage.setItem('fleet-chat-view',view)}catch{};
 if(expanded)$('expanded-chat-mount').append(pane);else if(pane.parentElement!==document.body)document.body.append(pane);
 $('toggle-chat-view').textContent=expanded?'Back to job workspace ↙':'Open full chat ↗';
 $('chat-body').scrollTop=scroll;
 if(expanded){$('assistant').scrollIntoView({block:'start'});$('chat-input').focus({preventScroll:true})}
}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>showView(b.dataset.view));
$('toggle-chat-view').onclick=()=>document.querySelector('[data-view="'+(document.body.classList.contains('chat-expanded')?'procedure':'assistant')+'"]').click();
function resizeChatInput(){const input=$('chat-input');input.style.height='44px';input.style.height=Math.min(160,Math.max(44,input.scrollHeight))+'px';}
$('chat-input').addEventListener('input',resizeChatInput);
$('chat-input').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();const button=$('side-chat').querySelector('button[type="submit"],button.primary');if(!button.disabled&&$('chat-input').value.trim())$('side-chat').requestSubmit(button)}});
$('cancel').onclick=()=>$('complete').close();
$('completion').onsubmit=async e=>{e.preventDefault();const b=e.submitter;b.disabled=true;try{let photo=null,f=$('photo').files[0];if(f){if(f.size>2000000)throw Error('Photo must be under 2 MB');photo=await new Promise((resolve,reject)=>{let r=new FileReader();r.onload=()=>resolve(r.result);r.onerror=reject;r.readAsDataURL(f)})}await api('jobs/'+selected.id+'/complete',{version:selected.version,meter:$('meter').value.trim()===''?null:Number($('meter').value),note:$('notes').value,photo});$('complete').close();notice('Completion saved as an encrypted local record. Transaction queued.');await refresh()}catch(err){notice(err.message)}finally{b.disabled=false}};

for(const target of ['ship','shore'])$(target).onclick=async()=>{try{const mode=$('network').value;if(mode==='device'||(target==='shore'&&mode!=='shore'))throw Error('Select the corresponding matching connectivity state first');const d=await api('sync',{target});notice(`${d.acknowledged} new ${target} acknowledgments (simulation).`);$(target).classList.add('sync-success');setTimeout(()=>$(target).classList.remove('sync-success'),700);await refresh()}catch(err){notice(err.message)}};
$('export').onclick=()=>{if(!$('verified').checked)return notice('Review the fixture value before export.');const n=Number($('reading').value);if(!Number.isFinite(n)||n<0)return notice('Enter a valid nonnegative meter reading.');const blob=new Blob([JSON.stringify({fixture:true,asset:'DEMO 701',meter:n,reviewed:true,confidence_source:'illustrative only'},null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='reviewed-demo-record.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
refresh().then(restoreLastConversation).catch(e=>notice(e.message));
let procedureData=null,procedureSession=null,sectionIndex=0,reviewed=new Set(),procedureDirty=false;
function updateProcedureJobs(preferredId=$('procedure-job').value,sailor=$('workspace-sailor').value){
 if(!state)return;
 syncConversationEquipment();
 const jobs=state.jobs.filter(j=>{const row=watchRows.find(r=>r.job.id===j.id);const owner=j.id===draftJob?$('draft-owner').value:row?ownerOf(row):'';const ship=row?.draft.ship_id||'';const equipment=row?.draft.equipment_id||'';return !!watchShipId&&(!sailor||owner===sailor)&&ship===watchShipId&&(!workspaceEquipmentFilter||equipment===workspaceEquipmentFilter)});
 $('procedure-job').innerHTML=jobs.length?jobs.map(j=>`<option value="${esc(j.id)}">[${esc(j.status)}] ${esc(j.id)} · ${esc(j.title)} · ${esc(ownerOf(watchRows.find(r=>r.job.id===j.id))||'Unassigned')}</option>`).join(''):'<option value="">No work orders match this sailor and equipment</option>';
 $('procedure-job').disabled=!jobs.length;
 if(jobs.some(j=>j.id===preferredId))$('procedure-job').value=preferredId;else if(jobs.length){$('procedure-job').insertBefore(new Option('Select a work order',''),$('procedure-job').firstChild);$('procedure-job').value='';}
 document.querySelectorAll('[data-follow]').forEach(b=>b.onclick=()=>startJob(b.dataset.follow,b));
}

async function showLogs(logs){$('log-list').innerHTML=logs.map(l=>`<p><a href="${HATCH_BASE}/api/logs/${encodeURIComponent(l.id)}">${esc(l.name)}</a><br><small>${esc(l.status)} · ${esc(l.created)}</small></p>`).join('')||'<p>No handwritten logs uploaded yet.</p>'}
async function loadProcedureSession(){if(!$('procedure-job').value)return;await loadJobDraft();const id=$('procedure-job').value;const d=await api('jobs/'+id+'/procedure');procedureSession=d.session;procedureDirty=false;await showLogs(d.logs);procedureData=null;stepCoachVersion++;stepCoachKey='';$('step-coach')?.remove();$('procedure-content').hidden=true;$('procedure-empty').hidden=true;$('procedure-checklist').replaceChildren();const source=d.session?.source||watchRows.find(r=>r.job.id===id)?.schedule?.procedure_source;if(source){const p=await api('procedure?source='+encodeURIComponent(source));await openProcedure(p,d.session)}else{$('procedure-complete').disabled=false;updateChatContext()}}

$('procedure-job').onchange=async()=>{try{await flushDraft();await loadProcedureSession()}catch(e){$('procedure-job').value=draftJob;notice(e.message)}};
async function openProcedure(p,s){$('procedure-complete').disabled=false;$('procedure-empty').hidden=true;procedureData=p;sectionIndex=0;reviewed=new Set(s?.revision_hash===p.revision_hash?s.checked:[]);if(p.structured_steps){const next=p.sections.findIndex((_,i)=>!reviewed.has(i));sectionIndex=next<0?p.sections.length-1:next;}$('procedure-notes').value=s?.note||'';procedureDirty=false;$('procedure-content').hidden=false;$('procedure-title').textContent=p.title;document.querySelector('.procedure-scope').textContent=p.structured_steps?'Demo checklist · Synthetic steps for testing; use approved equipment instructions for actual maintenance.':'Source reading view · Checkmarks record review, not certified maintenance completion.';$('procedure-source').textContent=p.source+' · SHA-256 '+p.revision_hash.slice(0,12);if(s&&s.revision_hash!==p.revision_hash)notice('Source revision changed. Reading acknowledgments have been cleared.');renderSection();loadLessons().catch(e=>{$('lesson-list').textContent='Lessons unavailable: '+e.message})}
function renderSection(){renderChecklist();updateChatContext();scheduleStepCoach();$('procedure-step').textContent=`${procedureData.structured_steps?'STEP':'SECTION'} ${sectionIndex+1} OF ${procedureData.sections.length}\n\n`+procedureData.sections[sectionIndex];$('section-read').checked=reviewed.has(sectionIndex);$('previous-section').disabled=sectionIndex===0;$('next-section').disabled=sectionIndex===procedureData.sections.length-1}
$('previous-section').onclick=()=>{sectionIndex--;renderSection()};$('next-section').onclick=()=>{sectionIndex++;renderSection()};$('section-read').onchange=()=>{if($('section-read').checked)reviewed.add(sectionIndex);else reviewed.delete(sectionIndex);procedureDirty=true};$('procedure-notes').oninput=()=>procedureDirty=true;
$('clear-checks').onclick=async()=>{
 const button=$('clear-checks');button.disabled=true;
 try{
  endCurrentChat();
  if(procedureData){reviewed.clear();sectionIndex=0;procedureDirty=true;renderSection();}
  for(const id of ['draft-symptom-report','draft-symptom','draft-actions_taken','draft-outcome','problem-photo'])$(id).value='';
  $('resolution-status').value='not_verified';$('problem-photo-preview').hidden=true;$('problem-photo-img').removeAttribute('src');
  $('problem-report-status').textContent='';$('troubleshooting-status').textContent='';scheduleTroubleshooting();
  document.querySelectorAll('#procedure details,.chat-pane details').forEach(details=>details.open=false);closeEquipmentOptions();
  if(jobDraft){draftDirty=true;draftGeneration++;await flushDraft();}
  notice(procedureData?'Checks and current troubleshooting draft cleared; sections collapsed. Open Maintenance steps and save progress to persist cleared checks.':'Current troubleshooting draft cleared; sections collapsed.',5000);
  $('procedure').scrollIntoView({block:'start'});
 }catch(e){notice('Troubleshooting reset could not be saved: '+e.message);}finally{button.disabled=false}
};

// Corrective maintenance: problem report
function isCorrectiveJob(){const id=$('procedure-job').value;const row=watchRows.find(r=>r.job.id===id);return !!(row?.schedule?.corrective||row?.job?.corrective)}
function showProblemReport(){$('problem-report').hidden=false;$('problem-report').open=isCorrectiveJob();$('draft-symptom-report').value=$('draft-symptom')?.value||'';$('draft-symptom-report').disabled=!draftJob;$('problem-ask-ai').disabled=!draftJob;$('problem-photo').disabled=!draftJob;$('problem-photo').value='';$('problem-photo-preview').hidden=true;$('problem-report-status').textContent='';loadProblemPhotos();}
$('draft-symptom-report').oninput=()=>{$('draft-symptom').value=$('draft-symptom-report').value;draftDirty=true;draftGeneration++;clearTimeout(draftTimer);draftTimer=setTimeout(()=>flushDraft().catch(()=>{}),800);scheduleTroubleshooting()};
$('problem-photo').onchange=()=>{const f=$('problem-photo').files[0];if(!f)return;if(f.size>5*1024*1024){notice('Photo must be under 5 MB');$('problem-photo').value='';return}const reader=new FileReader();reader.onload=()=>{$('problem-photo-img').src=reader.result;$('problem-photo-preview').hidden=false};reader.readAsDataURL(f)};
$('problem-photo-clear').onclick=()=>{$('problem-photo').value='';$('problem-photo-preview').hidden=true};
async function loadProblemPhotos(){const id=draftJob;$('problem-saved-photos').replaceChildren();if(!id)return;try{const rows=await api('jobs/'+id+'/problem-photos');if(draftJob!==id)return;$('problem-saved-photos').innerHTML=rows.map(p=>`<a href="${esc(hatchURL(p.url))}" target="_blank" rel="noopener">Saved problem photo · ${esc(new Date(p.recorded).toLocaleString())}</a>`).join('<br>')}catch(e){$('problem-report-status').textContent='Unable to load saved photos: '+e.message}}
$('problem-ask-ai').onclick=async()=>{
 const symptom=$('draft-symptom-report').value.trim(),id=draftJob,button=$('problem-ask-ai');
 if(!id||!symptom){notice('Select a job and describe the problem first.');return;}
 if($('side-chat').querySelector('button').disabled){notice('Wait for the current response or cancel it before starting a new problem discussion.');return;}
 button.disabled=true;$('problem-report-status').textContent='Saving problem and searching local class history…';
 try{
  $('draft-symptom').value=symptom;draftDirty=true;draftGeneration++;await flushDraft();
  const file=$('problem-photo').files[0];
  if(file){const response=await hatchFetch('/api/jobs/'+encodeURIComponent(id)+'/problem-photos',{method:'POST',body:file});const result=await response.json();if(!response.ok)throw Error(result.detail||'Photo could not be saved');if(draftJob!==id)return;$('problem-photo').value='';await loadProblemPhotos();}
  if(draftJob!==id)return;
  await loadTroubleshooting();
  const conversation=await api('conversations',{job_id:id,problem:symptom});
  if(draftJob!==id)return;
  displayConversation(conversation);showView('assistant');
  $('problem-report-status').textContent='Problem saved in a new discussion. HATCH is preparing symptom-specific checks and manual page references.';
  $('chat-input').value=symptom;
  $('side-chat').requestSubmit($('side-chat').querySelector('button'));
 }catch(e){$('problem-report-status').textContent='Unable to finish: '+e.message}finally{button.disabled=!draftJob}
};
$('save-progress').onclick=async()=>{try{procedureSession=await api('jobs/'+$('procedure-job').value+'/procedure',{source:procedureData.source,revision_hash:procedureData.revision_hash,checked:[...reviewed],note:$('procedure-notes').value,version:procedureSession?.version||0});procedureDirty=false;notice('Procedure progress saved and queued.');await refresh()}catch(e){notice(e.message)}};
async function loadLessons(){const lessons=await api('lessons?source='+encodeURIComponent(procedureData.source));$('lesson-brief').textContent='';$('lesson-list').innerHTML=lessons.map(l=>`<article><p>${esc(l.text)}</p><small>${esc(l.id)} · ${esc(l.job_id)}<br>${esc(l.recorded)} · ${esc(l.status)}</small></article>`).join('')||'<p>No past observations recorded for this module.</p>'}
$('save-lesson').onclick=async()=>{try{const text=$('lesson-text').value.trim();if(!text)throw Error('Enter an observation first.');await flushDraft();await api('jobs/'+$('procedure-job').value+'/lessons',{source:procedureData.source,text,step:sectionIndex,kind:$('lesson-kind').value});scheduleStepCoach(true);$('lesson-text').value='';await loadLessons();await refresh();notice('Observation saved as an unverified technician report.')}catch(e){notice(e.message)}};
$('brief-lessons').onclick=async()=>{const b=$('brief-lessons');b.disabled=true;$('lesson-brief').textContent='Preparing local briefing…';try{const d=await api('lessons/brief',{source:procedureData.source,text:'brief'});$('lesson-brief').textContent=d.mode+'\n'+d.answer}catch(e){$('lesson-brief').textContent=e.message}finally{b.disabled=false}};
$('upload-log').onclick=async()=>{const b=$('upload-log');b.disabled=true;try{const f=$('handwritten-log').files[0];if(!f)throw Error('Select a handwritten log first.');if(f.size>10*1024*1024)throw Error('Maximum file size is 10 MB.');const r=await hatchFetch('/api/jobs/'+$('procedure-job').value+'/logs',{method:'POST',headers:{'X-Filename':encodeURIComponent(f.name)},body:f});const d=await r.json();if(!r.ok)throw Error(d.detail);$('log-status').textContent='Original stored encrypted. OCR pending; no handwriting has been parsed.';$('handwritten-log').value='';const saved=await api('jobs/'+$('procedure-job').value+'/procedure');await showLogs(saved.logs);await refresh()}catch(e){$('log-status').textContent=e.message}finally{b.disabled=false}};
$('procedure-complete').onclick=()=>{selected=state.jobs.find(j=>j.id===$('procedure-job').value);if(selected.status!=='Open')return notice('This work order is already completed. Logs can still be attached.');$('completion').reset();$('complete-job-context').textContent=selected.id+' · '+selected.title;$('complete').showModal()};
document.querySelector('[data-view="procedure"]').addEventListener('click',()=>{if(!procedureData)loadProcedureSession().catch(e=>notice('Unable to load job: '+e.message))});

let chatHistory=[],currentConversation=null,conversationLoadVersion=0,conversationPoll=null,chatRun=0,activeChatController=null;
function closedChatJobs(){try{return new Set(JSON.parse(localStorage.getItem('fleet-closed-chat-jobs')||'[]'))}catch{return new Set()}}
function markChatClosed(job,closed){const jobs=closedChatJobs();if(closed)jobs.add(job||'general');else jobs.delete(job||'general');try{localStorage.setItem('fleet-closed-chat-jobs',JSON.stringify([...jobs]))}catch{}}
function endCurrentChat(){resetFindingsReview();chatRun++;activeChatController?.abort();activeChatController=null;conversationLoadVersion++;clearTimeout(conversationPoll);markChatClosed(draftJob,true);currentConversation=null;chatHistory=[];try{localStorage.removeItem('fleet-last-conversation')}catch{};$('chat-thread-title').textContent='';$('chat-messages').innerHTML='<p class="muted">Conversation closed. Start a new conversation, or open Saved conversations to resume a previous discussion.</p>';$('chat-input').value='';resizeChatInput();delete $('side-chat').dataset.stepHelp;$('chat-save-status').textContent='Previous conversations remain saved on this host.';$('chat-status').textContent='No active conversation';$('side-chat').querySelector('button').disabled=false;$('clear-chat').disabled=false;}
function updateChatContext(){if($('chat-context'))$('chat-context').textContent=procedureData?procedureData.title+' · step '+(sectionIndex+1):'Local corpus + work-order records';if($('chat-job-context'))$('chat-job-context').textContent=draftJob?[$('draft-ship_name').value,$('draft-owner').value,draftJob].filter(Boolean).join(' · '):'Select a work order on My Watch for equipment-specific help.';}
function readableQuestion(text){
 if(text.startsWith('The sailor reports: ')&&text.includes('Propose numbered troubleshooting checks'))return text.slice('The sailor reports: '.length).split('Propose numbered troubleshooting checks')[0].trim();
 return text;
}
function chatMessage(role,text){const box=document.createElement('article');box.className='chat-message '+role;const label=document.createElement('strong');label.textContent=role==='user'?'You':'HATCH';const body=document.createElement('p');body.textContent=role==='user'?readableQuestion(text):text;box.append(label,body);$('chat-messages').append(box);$('chat-body').scrollTop=$('chat-body').scrollHeight;return box}
$('clear-chat').onclick=async()=>{try{const c=await api('conversations',{job_id:draftJob});displayConversation(c);$('chat-status').textContent='New conversation — previous chats remain saved'}catch(e){$('chat-save-status').textContent='Unable to start conversation: '+e.message}};
$('side-chat').onsubmit=async e=>{
 e.preventDefault();const input=$('chat-input'),question=input.value.trim();if(!question)return;
 const quick=$('side-chat').dataset.stepHelp==='true';delete $('side-chat').dataset.stepHelp;const controller=new AbortController(),run=++chatRun;activeChatController=controller;const button=e.submitter;button.disabled=true;$('clear-chat').disabled=true;input.value='';resizeChatInput();chatMessage('user',question);
 const box=chatMessage('assistant',''),answer=box.querySelector('p'),activity=document.createElement('details'),summary=document.createElement('summary'),steps=document.createElement('div');
 activity.className='chat-activity';activity.hidden=true;activity.open=false;summary.textContent='Working…';activity.append(summary,steps);box.insertBefore(activity,answer);
 const busy=document.createElement('div');busy.className='ai-busy';busy.setAttribute('role','status');busy.setAttribute('aria-live','polite');const spinner=document.createElement('span');spinner.className='ai-spinner';spinner.setAttribute('aria-hidden','true');const progress=document.createElement('span');progress.textContent='Preparing your question…';const cancel=document.createElement('button');cancel.type='button';cancel.textContent='Cancel';cancel.onclick=()=>controller.abort();busy.append(spinner,progress,cancel);box.insertBefore(busy,activity);box.setAttribute('aria-busy','true');
 const requestJob=draftJob;let requestConversation=null;
 const started=Date.now();let answerRefs=[],rawAnswer='';let completed=false,failed=false,phase='Preparing your question',mode='Local AI';
 const timer=setInterval(()=>{if(run!==chatRun)return;const seconds=Math.floor((Date.now()-started)/1000);progress.textContent=phase+' · '+seconds+'s'+(seconds>=15?' — still waiting for the local model':'');$('chat-status').textContent='Working · '+seconds+'s';},1000);
 function process(event){
  if(run!==chatRun)return;
  if(event.type==='activity'){phase=event.text.includes('Connected')?'Thinking…':event.text.includes('Preparing final')?'Writing answer…':event.text.includes('Contacting')?'Waiting for local model…':event.text;progress.textContent=phase;const line=document.createElement('p');line.textContent=event.text;steps.append(line);summary.textContent=event.text;}
  if(event.type==='token'){rawAnswer+=event.text;renderChatAnswer(answer,rawAnswer,answerRefs);}
  if(event.type==='references'){answerRefs=event.references;for(const ref of event.references)savedReference(box,ref);}
  if(event.type==='done'){completed=true;mode=event.mode||'Local AI';activity.open=false;summary.textContent=`${event.mode||"Local AI"} · completed in ${Math.floor((Date.now()-started)/1000)}s`;}
  if(event.type==='error'){failed=true;const error=document.createElement('p');error.className='warning';error.textContent=event.text;box.append(error);summary.textContent='Request failed · expand for activity';activity.open=false;}
 }
 try{
  await flushDraft();
  if(run!==chatRun)return;
  if(!currentConversation||currentConversation.job_id!==requestJob){const created=await api('conversations',{job_id:requestJob});if(run!==chatRun)return;currentConversation=created;rememberConversation(currentConversation.id);}
  requestConversation=currentConversation.id;$('chat-save-status').textContent='Saving conversation on host…';
  const response=await hatchFetch('/api/chat/stream',{method:'POST',headers:{'Content-Type':'application/json'},signal:controller.signal,body:JSON.stringify({text:question,step_help:quick,conversation_id:requestConversation,job_id:requestJob,history:chatHistory.slice(-6),source:procedureData?.source||null,section:sectionIndex})});
  if(!response.ok)throw Error('Chat request failed: HTTP '+response.status);
  $('chat-save-status').textContent='Question saved encrypted on host; answer will save when complete.';
  const reader=response.body.getReader(),decoder=new TextDecoder();let buffer='';
  while(true){const {value,done}=await reader.read();buffer+=decoder.decode(value,{stream:!done});let index;while((index=buffer.indexOf('\n'))>=0){const line=buffer.slice(0,index);buffer=buffer.slice(index+1);if(line.trim())process(JSON.parse(line))}if(done)break;}
  if(buffer.trim())process(JSON.parse(buffer));
  if(!completed&&!failed)throw Error('Connection ended before the answer completed.');
  if(completed&&run===chatRun){const raw=rawAnswer;renderChatAnswer(answer,raw,answerRefs);if(currentConversation?.id===requestConversation)chatHistory.push({role:'user',content:question},{role:'assistant',content:raw});}
 }catch(err){if(run!==chatRun)return;if(!requestConversation)$('chat-save-status').textContent='Conversation not saved: '+err.message;process({type:'error',text:err.name==='AbortError'?'Request canceled.':err.message})}
 finally{clearInterval(timer);busy.remove();box.removeAttribute('aria-busy');if(run!==chatRun)return;activeChatController=null;if(requestConversation)refreshConversationSaveStatus(requestConversation);$('chat-status').textContent=completed?mode+' · complete':controller.signal.aborted?'Canceled':'Request failed';button.disabled=false;$('clear-chat').disabled=false;input.focus();if(completed&&requestJob&&currentConversation?.id===requestConversation&&reportsResolution(question))draftFindingsFromChat();}
};

$('equipment-document-panel').addEventListener('toggle',()=>{if($('equipment-document-panel').open)loadEquipmentDocuments()});

function downloadText(name,text,type='text/plain'){const url=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function bindHandoffs(){document.querySelectorAll('[data-handoff]').forEach(b=>b.onclick=async()=>{try{const result=await api('jobs/'+b.dataset.handoff+'/handoff');downloadText(b.dataset.handoff+'-handoff-draft.txt',result.text);notice('Handoff draft downloaded. Review before sharing.')}catch(e){notice(e.message)}})}
let trialStart=null,trialElapsed=null,trialMethod=null,trialTimer=null;const trials=[];
$('trial-start').onclick=()=>{trialMethod=$('trial-method').value;trialStart=performance.now();trialElapsed=null;$('trial-start').disabled=true;$('trial-method').disabled=true;$('trial-stop').disabled=false;$('trial-save').disabled=true;$('trial-quality').value='pending';trialTimer=setInterval(()=>{$('trial-clock').textContent=trialMethod+' trial · '+((performance.now()-trialStart)/1000).toFixed(1)+' seconds'},100)};
$('trial-stop').onclick=()=>{trialElapsed=(performance.now()-trialStart)/1000;clearInterval(trialTimer);$('trial-clock').textContent=trialMethod+' trial stopped · '+trialElapsed.toFixed(1)+' seconds';$('trial-stop').disabled=true;$('trial-save').disabled=false};
$('trial-save').onclick=()=>{trials.push({method:trialMethod,seconds:trialElapsed,quality:$('trial-quality').value,recorded:new Date().toISOString()});$('trial-save').disabled=true;$('trial-start').disabled=false;$('trial-method').disabled=false;renderImpact()};
function renderImpact(){const accepted=method=>trials.filter(t=>t.method===method&&t.quality==='pass').map(t=>t.seconds);const median=a=>{a.sort((x,y)=>x-y);return a.length%2?a[Math.floor(a.length/2)]:(a[a.length/2-1]+a[a.length/2])/2};const baseline=accepted('manual'),assisted=accepted('hatch');let comparison='Complete at least one reviewed passing trial for each method to compare.';if(baseline.length&&assisted.length){const b=median(baseline),h=median(assisted);comparison=`Observed median elapsed-time difference: ${(b-h).toFixed(1)} seconds per trial (${b>0?((b-h)/b*100).toFixed(1):'0'}%). Positive means HATCH was faster. Baseline n=${baseline.length}; HATCH n=${assisted.length}. Small demo samples do not establish fleetwide savings.`}$('impact-results').innerHTML='<p>'+esc(comparison)+'</p>'+trials.map(t=>`<p>${esc(t.method)} · ${t.seconds.toFixed(1)}s · ${esc(t.quality)}</p>`).join('')}
$('trial-export').onclick=()=>downloadText('hatch-deckplate-trials.json',JSON.stringify({scope:'Elapsed administrative task time; not labor-hours',trials},null,2),'application/json');
renderImpact();
async function loadFeedback(){try{const d=await api('feedback');$('feedback-count').textContent=d.total+' submitted';$('feedback-list').innerHTML=d.items.map(f=>`<article class="panel"><div class="eyebrow">${esc(f.kind)} · ${esc(f.area)}</div><p class="feedback-message">${esc(f.text)}</p><small class="muted">${esc(f.author||'Anonymous reviewer')} · ${esc(new Date(f.created).toLocaleString())}</small></article>`).join('')||'<div class="panel"><p>No feedback yet. Share the first observation.</p></div>'}catch(e){$('feedback-status').textContent='Unable to load feedback: '+e.message}}
document.querySelector('[data-view="feedback"]').addEventListener('click',loadFeedback);
$('feedback-form').onsubmit=async e=>{e.preventDefault();const b=e.submitter;b.disabled=true;try{await api('feedback',{author:$('feedback-author').value.trim(),area:$('feedback-area').value,kind:$('feedback-kind').value,text:$('feedback-text').value.trim()});$('feedback-text').value='';$('feedback-status').textContent='Thank you. Your feedback is saved for the team.';await loadFeedback()}catch(err){$('feedback-status').textContent=err.message}finally{b.disabled=false}};
let shipCatalog=null,schematicRequest=0;
function selectedShipClass(){return $('ship-class').value==='__custom'?'Custom: '+$('custom-class').value.trim():$('ship-class').value}
function renderShipClasses(){const old=$('ship-class').value,q=$('ship-class-search').value.trim().toLowerCase();let options='<option value="">Select a ship class</option>';for(const [group,names] of Object.entries({...shipCatalog.groups,'Saved custom classes':shipCatalog.custom})){const filtered=names.filter(n=>(group+' '+n).toLowerCase().includes(q));if(filtered.length)options+=`<optgroup label="${esc(group)}">${filtered.map(n=>`<option value="${esc(n)}">${esc(n)}</option>`).join('')}</optgroup>`}options+='<option value="__custom">Custom class…</option>';$('ship-class').innerHTML=options;if([...$('ship-class').options].some(o=>o.value===old))$('ship-class').value=old;$('custom-class-label').hidden=$('ship-class').value!=='__custom';loadSchematics()}
async function initShipClasses(){try{shipCatalog=await api('ship-classes');renderShipClasses()}catch(e){$('schematic-status').textContent='Unable to load ship classes: '+e.message}}
async function loadSchematics(){const request=++schematicRequest,c=selectedShipClass();$('schematic-list').replaceChildren();$('schematic-count').textContent='';if(!c||c==='Custom: ')return;try{const files=await api('schematics?ship_class='+encodeURIComponent(c));if(request!==schematicRequest)return;$('schematic-count').textContent=files.length+' files';$('schematic-list').innerHTML=files.map(f=>`<article class="schematic-row"><a href="${HATCH_BASE}/api/schematics/${encodeURIComponent(f.id)}/download">${esc(f.name)}</a><p class="muted">${esc(f.ship_class)} · ${(f.size/1024).toFixed(1)} KB · ${esc(new Date(f.created).toLocaleString())}</p></article>`).join('')||'<p>No schematics saved for this class yet.</p>'}catch(e){if(request===schematicRequest)$('schematic-status').textContent=e.message}}
$('ship-class-search').oninput=()=>{if(shipCatalog)renderShipClasses()};$('ship-class').onchange=()=>{$('custom-class-label').hidden=$('ship-class').value!=='__custom';$('schematic-status').textContent='';loadSchematics()};$('custom-class').onchange=loadSchematics;
$('schematic-upload').onsubmit=async e=>{e.preventDefault();const shipClass=selectedShipClass(),files=[...$('schematic-files').files];if(!shipClass||shipClass==='Custom: ')return $('schematic-status').textContent='Select or enter a ship class first.';const button=e.submitter;button.disabled=true;$('ship-class').disabled=true;$('custom-class').disabled=true;$('ship-class-search').disabled=true;let saved=0;try{for(const file of files){if(file.size>20*1024*1024)throw Error(file.name+': exceeds 20 MB');$('schematic-status').textContent=`Uploading ${file.name} for ${shipClass}…`;const response=await hatchFetch('/api/schematics?ship_class='+encodeURIComponent(shipClass),{method:'POST',headers:{'X-Filename':encodeURIComponent(file.name)},body:file});const result=await response.json();if(!response.ok)throw Error(typeof result.detail==='string'?result.detail:JSON.stringify(result.detail));saved++;}$('schematic-files').value='';$('schematic-status').textContent=`${saved} schematic(s) saved for ${shipClass}.`;if(shipClass.startsWith('Custom: ')&&!shipCatalog.custom.includes(shipClass))shipCatalog.custom.push(shipClass);}catch(err){$('schematic-status').textContent=`${saved} saved. ${err.message}`}finally{button.disabled=false;$('ship-class').disabled=false;$('custom-class').disabled=false;$('ship-class-search').disabled=false;await loadSchematics();await loadJobSchematics()}};
initShipClasses();
let watchOptions=null;
let watchRows=[],draftJob=null,jobDraft=null,draftTimer=null,draftDirty=false,draftSaving=null,draftGeneration=0;
const draftFields=['equipment_id','ship_id','ship_name','hull_number','equipment','symptom','actions_taken','outcome','owner','location','ship_class','notes','blockers','next_watch'];
async function loadWatch(){try{watchOptions=await api('watch-options');watchRows=await api('watch');await ensureShipDirectory();if($('ship-type-filter').options.length===1)$('ship-type-filter').innerHTML='<option value="">All ship types</option>'+directoryClasses().map(c=>`<option value="${esc(c)}">${esc(c)}</option>`).join('');restoreWatchShip();await loadShipSailors();renderWatch();updateProcedureJobs()}catch(e){notice('Unable to load watch context: '+e.message)}}
function ownerOf(row){return row.draft.owner||row.schedule?.assignee||''}
function inWeek(day){return day&&day>=watchOptions.week_start&&day<=watchOptions.week_end}
function watchMatch(row,filter){const j=row.job,s=row.schedule;return filter==='all'||filter==='open'&&j.status==='Open'||filter==='completed'&&j.status!=='Open'||filter==='blocked'&&row.draft.blockers.trim()||filter==='due-week'&&j.status==='Open'&&inWeek(s?.due_date)||filter==='completed-week'&&j.status!=='Open'&&inWeek(j.completed?.slice(0,10))||filter==='overdue'&&j.status==='Open'&&s?.due_date<watchOptions.today}
function submissionTimestamp(value){const date=new Date(value);return Number.isNaN(date.getTime())?'Not recorded':date.toLocaleString([], {year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',second:'2-digit',timeZoneName:'short'});}
function workOrderDue(row){const day=row.schedule?.due_date;if(!day)return 'Due date not set';const date=new Date(day+'T12:00:00Z');const label=Number.isNaN(date.getTime())?day:date.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'});return 'Due '+label+(row.job.status==='Open'?(day<watchOptions.today?' · Overdue':day===watchOptions.today?' · Today':''):'');}
function recentlyCompleted(row,now=Date.now()){const completed=Date.parse(row.job.completed);return row.job.status!=='Open'&&Number.isFinite(completed)&&completed<=now&&completed>now-7*24*60*60*1000;}
function renderWatch(){if(!watchOptions)return;$('repeat-job').hidden=!draftJob||state.jobs.find(j=>j.id===draftJob)?.status==='Open';for(const id of ['watch-center','watch-search','watch-filter'])$(id).disabled=!watchShipId;if(!watchShipId){$('watch-period').textContent='Select your ship to view maintenance.';$('watch-summary').replaceChildren();$('today-schedule').innerHTML='<p>Select a ship above to see today’s maintenance and overdue work.</p>';$('jobs').innerHTML='<p class="work-order-empty">Select a ship above to browse its work orders.</p>';$('work-order-count').textContent='';$('recent-completed').innerHTML='<p>Select a ship above to see completed maintenance.</p>';$('recent-completed-count').textContent='';return;}const q=$('watch-search').value.toLowerCase(),filter=$('watch-filter').value,center=$('watch-center').value,sailor=$('watch-sailor').value;const scoped=watchRows.filter(r=>(!watchShipId||r.draft.ship_id===watchShipId)&&(!center||r.schedule?.work_center===center)&&(!sailor||ownerOf(r)===sailor));$('watch-period').textContent=`Host date: ${watchOptions.today} · Week: ${watchOptions.week_start} through ${watchOptions.week_end}`;$('watch-summary').innerHTML=[['due-week','Due this week'],['completed-week','Completed this week'],['overdue','Overdue']].map(([key,label])=>`<button class="metric" data-watch-summary="${key}"><strong>${scoped.filter(r=>watchMatch(r,key)).length}</strong><span>${label}</span></button>`).join('');document.querySelectorAll('[data-watch-summary]').forEach(b=>b.onclick=()=>{if(b.dataset.watchSummary==='overdue'||b.dataset.watchSummary==='due-week'){$('today-schedule-menu').open=true;$('today-schedule-menu').scrollIntoView({block:'start'});return;}$('watch-filter').value=b.dataset.watchSummary;$('work-order-menu').open=true;renderWatch()});const today=scoped.filter(r=>r.job.status==='Open'&&r.schedule?.due_date&&r.schedule.due_date<=watchOptions.today).sort((a,b)=>a.schedule.due_date.localeCompare(b.schedule.due_date)||(a.schedule.time||'').localeCompare(b.schedule.time||'')||a.job.id.localeCompare(b.job.id));$('today-schedule').innerHTML=today.length?today.map(r=>`<article class="schedule-row ${r.job.status==='Open'&&r.schedule.due_date<watchOptions.today?'schedule-overdue':''}"><strong>${esc(r.schedule.time||'Time not set')}${r.schedule.duration_minutes?' · '+esc(r.schedule.duration_minutes)+' min':''}</strong><button data-open-job="${esc(r.job.id)}">${esc(r.job.title)} →</button><p><span class="schedule-due">${esc(workOrderDue(r))}</span>${esc(r.schedule.work_center)} · ${esc(ownerOf(r)||'Unassigned')} · ${esc(r.job.status)}</p></article>`).join(''):'<p>No maintenance due today or overdue for this selection.</p>';const recent=scoped.filter(r=>recentlyCompleted(r)).sort((a,b)=>Date.parse(b.job.completed)-Date.parse(a.job.completed));$('recent-completed-count').textContent=' · '+recent.length;$('recent-completed').innerHTML=recent.map(r=>`<article class="schedule-row"><strong>Completed</strong><button data-open-job="${esc(r.job.id)}">${esc(r.job.title)} →</button><p>${esc(new Date(r.job.completed).toLocaleString())} · ${esc(ownerOf(r)||'Unassigned')} · ${esc(r.draft.equipment||r.job.asset)}</p></article>`).join('')||'<p>No maintenance completed in the last seven days for this selection.</p>';const terms=q.trim().split(/\s+/).filter(Boolean);const rows=scoped.filter(r=>{if(r.job.status==='Open'&&r.schedule?.due_date&&r.schedule.due_date<=watchOptions.today)return false;const haystack=[r.job.id,r.job.title,r.job.asset,r.draft.equipment,ownerOf(r),r.draft.location].join(' ').toLowerCase();return terms.every(term=>haystack.includes(term))&&watchMatch(r,filter)}).sort((a,b)=>{const priority={Urgent:0,High:1,Routine:2};return Number(a.job.status!=='Open')-Number(b.job.status!=='Open')||(priority[a.job.priority]??3)-(priority[b.job.priority]??3)||(a.schedule?.due_date||'9999').localeCompare(b.schedule?.due_date||'9999')||a.job.id.localeCompare(b.job.id)});
$('work-order-count').textContent='· '+rows.length+' matches';
const futureOpen=$('future-work-menu')?.open??true,completedOpen=$('completed-work-menu')?.open??false;
const renderWorkRows=items=>items.map(r=>`<button type="button" class="work-order-row" data-open-job="${esc(r.job.id)}"><span class="work-order-heading"><strong>${esc(r.job.id)} · ${esc(r.job.title)}</strong><span aria-hidden="true">→</span></span><span class="work-order-equipment">${esc(r.draft.equipment||r.job.asset)}</span><span class="work-order-meta">${esc(ownerOf(r)||'Unassigned')} · ${esc(r.job.priority)} · ${esc(r.job.status)}</span><span class="work-order-due ${r.job.status==='Open'&&r.schedule?.due_date<watchOptions.today?'is-overdue':''}">${esc(r.job.status==='Open'?workOrderDue(r):'Completed '+submissionTimestamp(r.job.completed))}</span></button>`).join('')||'<p class="work-order-empty">No matching work orders.</p>';
const future=rows.filter(r=>r.job.status==='Open'),completed=rows.filter(r=>r.job.status!=='Open').sort((a,b)=>(Date.parse(b.job.completed)||0)-(Date.parse(a.job.completed)||0));
$('jobs').innerHTML=`<details id="future-work-menu" class="work-order-submenu" ${futureOpen||terms.length||filter==='open'?'open':''}><summary>Future maintenance · ${future.length}</summary><div class="work-order-sublist">${renderWorkRows(future)}</div></details><details id="completed-work-menu" class="work-order-submenu" ${completedOpen||terms.length||filter.startsWith('completed')?'open':''}><summary>Completed maintenance · ${completed.length}</summary><div class="work-order-sublist">${renderWorkRows(completed)}</div></details>`;
$('jobs').scrollTop=0;bindHandoffs();bindStartJobs();bindAssignments()}
$('watch-search').oninput=()=>{$('work-order-menu').open=true;renderWatch()};$('watch-filter').onchange=()=>{$('work-order-menu').open=true;renderWatch()};$('watch-center').onchange=renderWatch;$('watch-sailor').onchange=async()=>{try{await flushWorkspaceContext();clearWorkspaceSelection();renderWatch();updateProcedureJobs();loadEquipment()}catch(e){notice(e.message)}};
async function loadJobDraft(){await flushDraft();const id=$('procedure-job').value;if(!id)return;const d=await api('jobs/'+id+'/draft');if(draftJob!==id){resetFindingsReview();$('resolution-status').value='not_verified';}draftJob=id;jobDraft=d;$('reassign-job').disabled=false;$('draft-owner').disabled=true;$('assignment-status').textContent='';workspaceEquipmentFilter=d.equipment_id||'';draftDirty=false;$('draft-owner').options[0].textContent='Unassigned';await ensureShipDirectory();if(d.ship_id&&!watchShipId){watchShipId=d.ship_id;$('ship-search').value=d.ship_name;$('ship-type-filter').value=shipHullType({hull_number:d.hull_number});await loadShipSailors();renderWatch();}$('job-draft-panel').hidden=false;$('troubleshooting-panel').hidden=false;$('upload-log').disabled=false;if(d.owner&&![...$('draft-owner').options].some(o=>o.value===d.owner))$('draft-owner').add(new Option(d.owner,d.owner));draftFields.forEach(f=>$('draft-'+f).value=d[f]||'');if(!d.owner)$('draft-owner').value=watchRows.find(r=>r.job.id===id)?.schedule?.assignee||'';setWorkspaceSailor($('draft-owner').value);updateProcedureJobs(id);$('draft-save-status').textContent=d.updated?'Saved on host · '+new Date(d.updated).toLocaleTimeString():'Ready for notes';const j=state.jobs.find(j=>j.id===id);$('repeat-job').hidden=j.status==='Open';$('workspace-heading').textContent=id+' · '+j.title;showProblemReport();$('job-parts').innerHTML=state.parts.map(p=>`<p>${esc(p.name)} · ${p.on_hand} on hand / ${p.reserved} reserved · ${esc(p.location)}</p>`).join('');$('workspace-ship-context').textContent=d.ship_id?d.ship_name+' · '+d.hull_number:'This work order has no ship recorded.';renderExperience();await greetSailor();loadJobSchematics();loadTroubleshooting();await loadEquipment()}
async function loadJobSchematics(){const c=$('draft-ship_class').value;$('job-schematics').textContent=c?'Loading class drawings…':'Select a ship class above to find saved schematics.';if(!c)return;try{const files=await api('schematics?ship_class='+encodeURIComponent(c));if(c!==$('draft-ship_class').value)return;$('job-schematics').innerHTML=files.map(f=>`<p><a href="${HATCH_BASE}/api/schematics/${encodeURIComponent(f.id)}/download">${esc(f.name)}</a> · ${esc(f.ship_class)}</p>`).join('')||'<p>No drawings saved for this class. Use Upload & browse ship-class schematics below.</p>'}catch(e){$('job-schematics').textContent=e.message}}
async function flushDraft(){clearTimeout(draftTimer);if(draftSaving)await draftSaving;if(!draftDirty||!jobDraft)return;const generation=draftGeneration,id=draftJob,body={version:jobDraft.version};draftFields.forEach(f=>body[f]=$('draft-'+f).value);$('draft-save-status').textContent='Saving…';draftSaving=api('jobs/'+id+'/draft',body).then(d=>{jobDraft=d;const row=watchRows.find(r=>r.job.id===id);if(row)row.draft=d;if(generation===draftGeneration)draftDirty=false;$('draft-save-status').textContent=draftDirty?'More changes pending':'Saved on host · '+new Date(d.updated).toLocaleTimeString();}).catch(e=>{$('draft-save-status').textContent='Not saved · '+e.message;throw e}).finally(()=>{draftSaving=null});await draftSaving;if(draftDirty)await flushDraft();}
for(const f of draftFields)$('draft-'+f).addEventListener('input',()=>{if(!jobDraft){if(f==='owner')updateProcedureJobs();return;}draftDirty=true;draftGeneration++;$('draft-save-status').textContent='Unsaved changes';clearTimeout(draftTimer);draftTimer=setTimeout(()=>flushDraft().catch(()=>{}),800);if(f==='ship_class'){clearSelectedShip();renderShipOptions('');loadJobSchematics();loadTroubleshooting();}if(f==='symptom'){$('draft-symptom-report').value=$('draft-symptom').value;scheduleTroubleshooting();}if(f==='owner'){updateProcedureJobs(draftJob);renderExperience();flushDraft().then(()=>greetSailor()).catch(()=>{})}});
$('draft-save').onclick=async()=>{try{await flushDraft();await refresh()}catch(e){notice(e.message)}};
$('job-handoff').onclick=async()=>{try{await flushDraft();const d=await api('jobs/'+draftJob+'/handoff');downloadText(draftJob+'-handoff-draft.txt',d.text)}catch(e){notice(e.message)}};
window.addEventListener('beforeunload',e=>{if(draftDirty||draftSaving){e.preventDefault();e.returnValue=''}});
document.querySelector('[data-view="work"]').addEventListener('click',async()=>{try{await flushDraft();await refresh()}catch(e){notice(e.message)}});

function renderExperience(){$('assigned-sailor-name').textContent=jobDraft?.owner||'Unassigned';const sailor=$('draft-owner').value,p=watchOptions?.experience_profiles?.[sailor];$('experience-profile').innerHTML=p?`<div class="eyebrow">DEMO EXPERIENCE PROFILE</div><h3>${esc(sailor)} · ${esc(p.level)}</h3><p>${esc(p.repetitions)}</p><p>${esc(p.guidance)}</p><small class="muted">Explanation depth changes; required warnings and verification do not. This profile is not qualification evidence.</small>`:'<p>Experience not specified. The assistant will use standard explanations.</p>';}

async function greetSailor(){
 const id=draftJob;if(!id)return;
 if(currentConversation?.job_id===id)return;
 if(closedChatJobs().has(id)){endCurrentChat();return;}
 const version=++conversationLoadVersion;clearTimeout(conversationPoll);currentConversation=null;$('chat-thread-title').textContent='';chatHistory=[];$('chat-messages').replaceChildren();
 try{
  const conversations=await api('conversations?job_id='+encodeURIComponent(id));
  if(version!==conversationLoadVersion||id!==draftJob)return;
  if(conversations.length){const c=await api('conversations/'+conversations[0].id);if(version===conversationLoadVersion&&id===draftJob)displayConversation(c);return;}
  const d=await api('jobs/'+id+'/greeting');if(version!==conversationLoadVersion||id!==draftJob)return;
  currentConversation=null;$('chat-thread-title').textContent='';chatHistory=[];$('chat-messages').replaceChildren();
  const box=chatMessage('assistant',d.text);box.classList.add('chat-welcome');box.hidden=!!$('step-coach');const label=document.createElement('small');label.textContent=d.mode;box.insertBefore(label,box.querySelector('p'));chatHistory.push({role:'assistant',content:d.text});$('chat-status').textContent='Ready to help with this job';$('chat-save-status').textContent='Messages will save encrypted on this host.';
 }catch(e){$('chat-status').textContent='Conversation unavailable: '+e.message;}
}

let openingJob=false;
function bindStartJobs(){document.querySelectorAll('[data-open-job]').forEach(button=>{button.onclick=()=>startJob(button.dataset.openJob,button)})}
async function startJob(id,button){
 if(openingJob)return;openingJob=true;const original=button?.textContent;if(button){button.disabled=true;button.textContent='Opening…';}
 try{
  await flushDraft();
  if(procedureDirty&&!confirm('Discard unsaved procedure reading progress?'))return;
  const job=state.jobs.find(j=>j.id===id);if(!job)throw Error('Work order no longer available. Refresh the dashboard.');
  const targetRow=watchRows.find(r=>r.job.id===id);workspaceEquipmentFilter=targetRow?.draft.equipment_id||'';updateProcedureJobs(id,targetRow?ownerOf(targetRow):'');$('procedure-job').value=id;
  if($('procedure-job').value!==id)throw Error('Could not select the work order. Refresh and try again.');
  showView('procedure');
  $('workspace-heading').textContent=id+' · '+job.title;$('job-open-status').textContent='Opening work order…';$('procedure').scrollIntoView({block:'start'});
  await loadProcedureSession();$('job-open-status').textContent='';$('procedure').scrollIntoView({block:'start'});
 }catch(e){$('job-open-status').textContent='Unable to open work order: '+e.message;notice('Unable to open work order: '+e.message)}
 finally{openingJob=false;if(button){button.disabled=false;button.textContent=original;}}
}

let savingStep=false;
function renderChecklist(){const p=procedureData,structured=!!p.structured_steps;$('procedure-checklist').hidden=!structured;const pct=structured?Math.round(reviewed.size/p.sections.length*100):0;$('step-progress').innerHTML=structured?`${reviewed.size} of ${p.sections.length} steps checked · Checklist<div class="procedure-progress"><div class="procedure-progress-fill" style="width:${pct}%"></div></div>`:'';$('section-read').parentElement.hidden=structured;if(!structured){$('procedure-checklist').replaceChildren();return;}$('procedure-checklist').innerHTML=p.sections.map((step,i)=>`<div class="checklist-row ${i===sectionIndex?'active-step':''}"><input type="checkbox" aria-label="Complete step ${i+1}" data-complete-step="${i}" ${reviewed.has(i)?'checked':''} ${savingStep?'disabled':''}><button type="button" data-focus-step="${i}"><strong>Step ${i+1}</strong><span>${esc(step)}</span></button></div>`).join('');document.querySelectorAll('[data-focus-step]').forEach(b=>b.onclick=()=>{sectionIndex=Number(b.dataset.focusStep);renderSection()});document.querySelectorAll('[data-complete-step]').forEach(box=>box.onchange=()=>saveCheckedStep(Number(box.dataset.completeStep),box.checked));}
async function saveCheckedStep(index,checked){if(savingStep)return;savingStep=true;sectionIndex=index;const before=new Set(reviewed);if(checked)reviewed.add(index);else reviewed.delete(index);procedureDirty=true;renderSection();$('step-progress').textContent='Saving step progress…';try{procedureSession=await api('jobs/'+$('procedure-job').value+'/procedure',{source:procedureData.source,revision_hash:procedureData.revision_hash,checked:[...reviewed],note:$('procedure-notes').value,version:procedureSession?.version||0});procedureDirty=false;if(checked){const next=procedureData.sections.findIndex((_,i)=>!reviewed.has(i));if(next>=0)sectionIndex=next;}}catch(e){reviewed=before;notice('Step was not saved: '+e.message)}finally{savingStep=false;renderSection()}}
function bindAssignments(){document.querySelectorAll('[data-assign-job]').forEach(select=>select.onchange=async()=>{const id=select.dataset.assignJob,owner=select.value;if(!owner)return;select.disabled=true;try{await flushDraft();const current=await api('jobs/'+id+'/draft');await api('jobs/'+id+'/draft',{...current,owner});if(draftJob===id){jobDraft=await api('jobs/'+id+'/draft');$('draft-owner').value=owner;renderExperience();await greetSailor();}await loadWatch();}catch(e){notice('Assignment not saved: '+e.message);await loadWatch()}finally{select.disabled=false}})}

let troubleshootingRequest=0;
async function loadTroubleshooting(){const request=++troubleshootingRequest,cls=$('draft-ship_class').value;if(!draftJob||!$('draft-symptom-report').value.trim()){$('troubleshooting-results').textContent='Describe the problem above to find relevant past fixes.';return;}if(!cls){$('troubleshooting-results').textContent='Select a named ship class above.';return;}try{const rows=await api('troubleshooting?ship_class='+encodeURIComponent(cls)+'&similar=true&equipment_id='+encodeURIComponent($('draft-equipment_id').value)+'&q='+encodeURIComponent($('draft-symptom-report').value));if(request!==troubleshootingRequest)return;$('troubleshooting-results').innerHTML=rows.length?`<p class="solution-count">${rows.length} matching solution record${rows.length===1?'':'s'} · expand to view details</p>`+rows.map(r=>`<details class="solution-record"><summary><span class="solution-title">${esc(r.actions_taken.length>105?r.actions_taken.slice(0,102)+'…':r.actions_taken)}</span><span class="solution-meta">${esc(r.resolution_status==='resolved'?'Reported resolved':r.resolution_status==='unresolved'?'Unresolved':'Not verified')} · ${esc(r.technician||'Unknown technician')} · Submitted ${esc(submissionTimestamp(r.recorded))}</span></summary><div class="solution-body"><p class="muted">${esc(r.ship_name)} · ${esc(r.hull_number)} · ${esc(r.equipment)} · ${esc(r.job_id)}</p><p><strong>Problem:</strong> ${esc(r.symptom)}</p><p><strong>Actions:</strong> ${esc(r.actions_taken)}</p><p><strong>Outcome:</strong> ${esc(r.outcome)}</p>${r.match_reason?`<p class="muted">${esc(r.match_reason)}</p>`:''}<div class="solution-links">${(r.conversation_links||[]).map(c=>`<button type="button" data-case-conversation="${esc(c.id)}">Open discussion: ${esc(c.title)}</button>`).join('')}${(r.problem_photos||[]).map(p=>`<a href="${esc(hatchURL(p.url))}" target="_blank" rel="noopener">View photo</a>`).join('')}</div><small>Submitted ${esc(submissionTimestamp(r.recorded))} · ${esc(r.status)}<br>Record ${esc(r.id)}</small></div></details>`).join(''):'<p>No relevant past fixes found for this reported symptom in the local history.</p>';document.querySelectorAll('[data-case-conversation]').forEach(b=>b.onclick=()=>openSavedConversation(b.dataset.caseConversation).catch(e=>notice(e.message)))}catch(e){$('troubleshooting-results').textContent='Unable to load history: '+e.message}}
let troubleshootingTimer=null;
function scheduleTroubleshooting(){clearTimeout(troubleshootingTimer);troubleshootingRequest++;$('troubleshooting-results').textContent=$('draft-symptom-report').value.trim()?'Finding relevant past fixes…':'Describe the problem above to find relevant past fixes.';troubleshootingTimer=setTimeout(loadTroubleshooting,400);}

$('save-troubleshooting').onclick=async()=>{const button=$('save-troubleshooting');if(!$('findings-review-check').hidden&&!$('findings-reviewed').checked)return notice('Review the draft findings before submitting.');button.disabled=true;try{await flushDraft();if(procedureData&&procedureDirty)throw Error('Save the procedure progress before recording troubleshooting.');const r=await api('jobs/'+draftJob+'/troubleshooting',{draft_version:jobDraft.version,resolution_status:$('resolution-status').value});resetFindingsReview();$('troubleshooting-status').textContent='Submitted '+submissionTimestamp(r.recorded)+' · Report '+r.id+' with '+(r.conversation_links||[]).length+' conversation(s) for future troubleshooting · queued for synchronization.';await loadTroubleshooting()}catch(e){$('troubleshooting-status').textContent=e.message}finally{button.disabled=false}};

let shipDirectory=null;
async function ensureShipDirectory(){if(!shipDirectory)shipDirectory=await api('ships');return shipDirectory}
function shipHullType(ship){const code=(ship?.hull_number||'').match(/^((?:T-)?[A-Z]+)-[0-9]/)?.[1];return code==='T-ESB'?'ESB':code||'OTHER'}
function directoryClasses(){return [...new Set(shipDirectory.ships.map(shipHullType))].sort((a,b)=>a.localeCompare(b))}
function clearSelectedShip(){return selectDirectoryShip('')}
function renderShipOptions(query=$('ship-search').value){if(!shipDirectory)return;const cls=$('ship-type-filter').value,q=query.toLowerCase().trim();const matches=shipDirectory.ships.filter(s=>(!cls||shipHullType(s)===cls)&&(!q||(s.name+' '+s.hull_number).toLowerCase().includes(q)));$('ship-options').innerHTML=matches.map(s=>`<button type="button" role="option" data-select-ship="${esc(s.id)}">${esc(s.name)} <small>${esc(s.hull_number)} · ${esc(s.ship_class)} · ${esc(s.status)}</small></button>`).join('')||'<p>No matching ships in this class.</p>';$('ship-options').hidden=false;$('ship-search').setAttribute('aria-expanded','true');document.querySelectorAll('[data-select-ship]').forEach(b=>b.onclick=()=>selectDirectoryShip(b.dataset.selectShip))}
async function flushWorkspaceContext(){await flushDraft();if(procedureDirty&&procedureData&&draftJob){procedureSession=await api('jobs/'+draftJob+'/procedure',{source:procedureData.source,revision_hash:procedureData.revision_hash,checked:[...reviewed],note:$('procedure-notes').value,version:procedureSession?.version||0});procedureDirty=false;}}
function rememberWatchShip(){try{if(watchShipId)localStorage.setItem('fleet-current-ship',watchShipId);else localStorage.removeItem('fleet-current-ship')}catch{}}
function restoreWatchShip(){
 if(shipPreferenceLoaded)return;shipPreferenceLoaded=true;
 let saved='';try{saved=localStorage.getItem('fleet-current-ship')||''}catch{}
 const ship=shipDirectory.ships.find(s=>s.id===saved);if(!ship){rememberWatchShip();return;}
 watchShipId=ship.id;$('ship-search').value=ship.name;$('ship-type-filter').value=shipHullType(ship);clearWorkspaceSelection();loadEquipment();
}
async function selectDirectoryShip(id){
 try{await flushWorkspaceContext();const ship=shipDirectory.ships.find(s=>s.id===id);watchShipId=ship?.id||'';rememberWatchShip();workspaceEquipmentFilter='';renderWatch();$('ship-search').value=ship?.name||'';if(ship)$('ship-type-filter').value=shipHullType(ship);$('ship-options').hidden=true;$('ship-search').setAttribute('aria-expanded','false');await loadShipSailors();clearWorkspaceSelection();renderWatch();updateProcedureJobs();await loadEquipment();}catch(e){notice(e.message)}
}
async function loadShipSailors(){
 const request=++shipSailorRequest,old=$('watch-sailor').value;
 const result=watchShipId?await api('ships/'+encodeURIComponent(watchShipId)+'/maintenance-sailors'):null;if(request!==shipSailorRequest)return;
 const names=result?result.sailors.map(s=>s.name):[];
 $('watch-sailor').innerHTML='<option value="">All sailors</option>'+names.map(n=>`<option value="${esc(n)}">${esc(n)}</option>`).join('');if(names.includes(old))$('watch-sailor').value=old;
 const currentOwner=$('draft-owner').value,ownerNames=[...new Set([...(watchOptions?.sailors||[]),...names,currentOwner].filter(Boolean))].sort();
 $('draft-owner').innerHTML='<option value="">'+(draftJob?'Unassigned':'All sailors')+'</option>'+ownerNames.map(n=>`<option value="${esc(n)}">${esc(n)}</option>`).join('');$('draft-owner').value=currentOwner;
 const filter=$('workspace-sailor'),selected=filter.value;filter.innerHTML='<option value="">All sailors</option>'+names.map(n=>`<option value="${esc(n)}">${esc(n)}</option>`).join('');setWorkspaceSailor(selected);filter.disabled=!watchShipId;
 $('watch-sailor').disabled=!watchShipId||!names.length;
 filterWorkspaceSailors();if($('new-event-menu').open)loadNewEventOptions();
 $('watch-ship-status').textContent=watchShipId?(names.length?names.length+' sailors found in this ship’s saved maintenance records and logs.':'No maintenance records or logs linked to this ship yet.'):'Select a ship to view its sailors and maintenance. Your selection will be remembered in this browser.';
}
function workspaceAssignmentRows(){return watchRows.filter(r=>r.draft.ship_id===watchShipId);}
function filterWorkspaceSailors(){
 const select=$('workspace-sailor'),old=select.value,rows=workspaceAssignmentRows(),names=[...new Set([...rows.map(ownerOf),...(watchOptions?.sailors||[])].filter(Boolean))].sort();
 select.innerHTML='<option value="">All sailors</option>'+names.map(n=>`<option value="${esc(n)}">${esc(n)}</option>`).join('');select.value=names.includes(old)?old:'';select.disabled=!watchShipId;
}
function setWorkspaceSailor(name){const select=$('workspace-sailor');if(name&&![...select.options].some(o=>o.value===name))select.add(new Option(name,name));select.value=name||'';}
$('workspace-sailor').onchange=async()=>{const sailor=$('workspace-sailor').value;try{await flushWorkspaceContext();clearWorkspaceSelection(sailor);updateProcedureJobs();await loadEquipment();}catch(e){setWorkspaceSailor(jobDraft?.owner||'');notice(e.message)}};
function clearWorkspaceSelection(sailor=$('watch-sailor').value){
 resetFindingsReview();draftJob=null;jobDraft=null;syncConversationEquipment();$('assigned-sailor-name').textContent='Select a work order';$('repeat-job').hidden=true;$('resolution-status').value='not_verified';$('reassign-job').disabled=true;$('draft-owner').disabled=false;$('assignment-status').textContent='';draftDirty=false;procedureData=null;procedureSession=null;reviewed=new Set();procedureDirty=false;stepCoachKey='';stepCoachVersion++;$('step-coach')?.remove();currentConversation=null;$('chat-thread-title').textContent='';conversationLoadVersion++;clearTimeout(conversationPoll);chatHistory=[];$('chat-messages').replaceChildren();updateChatContext();
 $('procedure-content').hidden=true;$('procedure-empty').hidden=true;$('procedure-checklist').replaceChildren();showProblemReport();$('workspace-heading').textContent='Your job workspace';$('draft-owner').options[0].textContent='All sailors';$('draft-owner').value=sailor;setWorkspaceSailor(sailor);
 const ship=shipDirectory?.ships.find(s=>s.id===watchShipId);for(const key of ['ship_id','ship_name','ship_class','hull_number'])$('draft-'+key).value=({ship_id:ship?.id,ship_name:ship?.name,ship_class:ship?.ship_class,hull_number:ship?.hull_number})[key]||'';
 $('workspace-ship-context').textContent=ship?ship.name+' · '+ship.hull_number:'Select a ship on My Watch.';
 $('draft-equipment_id').value=workspaceEquipmentFilter;$('draft-equipment').value=equipmentItems.find(x=>x.equipment_id===workspaceEquipmentFilter)?.name||'';
 $('procedure-job').value='';$('job-draft-panel').hidden=true;$('troubleshooting-panel').hidden=true;$('upload-log').disabled=true;$('procedure-complete').disabled=true;$('log-list').replaceChildren();$('job-open-status').textContent='Select a work order to begin.';
}
$('clear-watch-ship').onclick=()=>{$('ship-type-filter').value='';selectDirectoryShip('')};
$('ship-search').onfocus=async()=>{try{await ensureShipDirectory();renderShipOptions('')}catch(e){notice(e.message)}};
$('ship-search').oninput=()=>renderShipOptions();
$('ship-search').onkeydown=e=>{if(e.key==='Escape'){ $('ship-options').hidden=true;$('ship-search').setAttribute('aria-expanded','false');$('ship-search').value=shipDirectory?.ships.find(s=>s.id===watchShipId)?.name||'';}if(e.key==='ArrowDown'){e.preventDefault();$('ship-options').querySelector('button')?.focus();}};
$('ship-options').onkeydown=e=>{const buttons=[...$('ship-options').querySelectorAll('button')],i=buttons.indexOf(document.activeElement);if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();buttons[Math.max(0,Math.min(buttons.length-1,i+(e.key==='ArrowDown'?1:-1)))]?.focus();}if(e.key==='Escape'){$('ship-search').focus();$('ship-options').hidden=true;$('ship-search').setAttribute('aria-expanded','false');}};
document.addEventListener('click',e=>{if(!e.target.closest('.ship-picker')){$('ship-options').hidden=true;$('ship-search').setAttribute('aria-expanded','false');$('ship-search').value=shipDirectory?.ships.find(s=>s.id===watchShipId)?.name||'';}});

$('ship-type-filter').onchange=async()=>{await clearSelectedShip();renderShipOptions('')};

let equipmentItems=[],equipmentRequest=0;
function clearEquipment(){closeEquipmentOptions();$('equipment-search').value='';$('equipment-search').placeholder='Select a ship first';equipmentRequest++;equipmentItems=[];$('draft-equipment').value='';$('draft-equipment_id').value='';$('equipment-selector').innerHTML='<option value="">Select a ship first</option>';$('equipment-detail').hidden=true;resetEquipmentDocuments();}
async function loadEquipment(){closeEquipmentOptions();$('equipment-search').value=$('draft-equipment').value;const request=++equipmentRequest,ship=$('draft-ship_id').value;$('equipment-detail').hidden=true;if(!ship){equipmentItems=[];resetEquipmentDocuments();$('equipment-search').value='';$('equipment-selector').innerHTML='<option value="">Select a ship first</option>';return;}try{const data=await api('ships/'+encodeURIComponent(ship)+'/equipment');if(request!==equipmentRequest)return;equipmentItems=data.items;filterWorkspaceSailors();$('equipment-search').placeholder=data.items.length?'Type or click to select equipment':'No equipment register for this class';const selected=workspaceEquipmentFilter||$('draft-equipment_id').value;$('equipment-selector').innerHTML='<option value="">'+(data.items.length?'Select demo equipment':'No demo register for this class')+'</option>'+data.items.map(x=>`<option value="${esc(x.equipment_id)}">${esc(x.name)} · ${esc(x.work_center)} · ${equipmentWorkload(x).total} open</option>`).join('');if(selected){$('equipment-selector').value=selected;$('equipment-search').value=data.items.find(x=>x.equipment_id===selected)?.name||'';}else if($('draft-equipment').value){$('equipment-selector').add(new Option('Existing record: '+$('draft-equipment').value,'__legacy'));$('equipment-selector').value='__legacy';}renderEquipment()}catch(e){$('equipment-selector').innerHTML='<option value="">Equipment unavailable</option>';notice(e.message)}}
function renderEquipment(){loadEquipmentDocuments();const item=equipmentItems.find(x=>x.equipment_id===$('equipment-selector').value);$('equipment-detail').hidden=!item;if(!item)return;const stock=item.inventory,n=v=>v===null?'Unknown':v;$('equipment-detail').innerHTML=`<div class="eyebrow">DEMO EQUIPMENT REGISTER · ${esc(stock.assessment.toUpperCase())}</div><h3>${esc(item.name)}</h3><p>${esc(item.demo_location)} · ${esc(item.work_center)}</p><p class="muted">${esc(item.applicability)}</p>${item.source?`<a href="${esc(item.source)}" target="_blank" rel="noopener noreferrer">Public equipment reference ↗</a>`:'<p class="muted">Upload the equipment manual to establish model-specific references.</p>'}<table><thead><tr><th>Part</th><th>Required</th><th>On hand</th><th>Reserved</th><th>Available</th></tr></thead><tbody><tr><td>${esc(stock.part_id)}<br>${esc(stock.name)}</td><td>${stock.required}</td><td>${n(stock.on_hand)}</td><td>${n(stock.reserved)}</td><td>${n(stock.available)}</td></tr></tbody></table><p>${esc(stock.assessment)}${stock.shortage?' · Short by '+stock.shortage:''} · Snapshot: ${esc(stock.snapshot||'Not available')}</p><p class="muted">${esc(stock.basis)}</p>`;}
$('equipment-selector').onchange=async()=>{
 const selected=$('equipment-selector').value;if(selected==='__legacy')return;
 try{await flushWorkspaceContext();workspaceEquipmentFilter=selected;filterWorkspaceSailors();closeEquipmentOptions();updateProcedureJobs();
 if(draftJob&&$('procedure-job').value!==draftJob)clearWorkspaceSelection($('workspace-sailor').value);
 if(!jobDraft){$('draft-equipment_id').value=selected;$('draft-equipment').value=equipmentItems.find(x=>x.equipment_id===selected)?.name||'';}
 $('equipment-selector').value=selected;$('equipment-search').value=equipmentItems.find(x=>x.equipment_id===selected)?.name||'';updateProcedureJobs();renderEquipment();
 }catch(e){notice(e.message)}
};
$('clear-equipment-filter').onclick=()=>{$('equipment-selector').value='';$('equipment-selector').dispatchEvent(new Event('change',{bubbles:true}))};

function closeEquipmentOptions(){$('equipment-options').hidden=true;$('equipment-search').setAttribute('aria-expanded','false')}
function equipmentWorkload(item){const ship=watchShipId||$('draft-ship_id').value,sailor=$('workspace-sailor').value;const rows=watchRows.filter(r=>r.draft.ship_id===ship&&r.draft.equipment_id===item.equipment_id),open=rows.filter(r=>r.job.status==='Open');return {total:open.length,completed:rows.length-open.length,owners:[...new Set(rows.map(ownerOf).map(n=>n||'Unassigned'))],assigned:sailor?open.filter(r=>ownerOf(r)===sailor).length:null,sailor};}
function equipmentWorkloadLabel(item){const count=equipmentWorkload(item);return count.total+' open'+(count.assigned===null?'':' · '+count.assigned+' assigned to '+count.sailor)+(count.completed?' · '+count.completed+' completed':'')+(count.owners.length?' · Work orders: '+count.owners.join(', '):'');}
function renderEquipmentOptions(query=$('equipment-search').value){const words=query.toLowerCase().trim().split(/\s+/).filter(Boolean);const matches=equipmentItems.filter(x=>words.every(word=>[x.name,x.equipment_id,x.work_center,x.demo_location].join(' ').toLowerCase().includes(word))).sort((a,b)=>a.name.localeCompare(b.name));$('equipment-options').innerHTML=matches.slice(0,100).map(x=>`<button type="button" role="option" aria-selected="${x.equipment_id===$('draft-equipment_id').value}" data-select-equipment="${esc(x.equipment_id)}">${esc(x.name)}<span class="equipment-workload">${esc(equipmentWorkloadLabel(x))}</span><small>${esc(x.work_center)} · ${esc(x.demo_location)} · ${esc(x.equipment_id)}</small></button>`).join('')+(matches.length>100?`<p>${matches.length} matches. Showing the first 100; type to narrow the list.</p>`:'')||'<p>'+(equipmentItems.length?'No matching equipment. Try another name, ID or work center.':'Select a ship with an equipment register first.')+'</p>';$('equipment-options').hidden=false;$('equipment-search').setAttribute('aria-expanded','true');document.querySelectorAll('[data-select-equipment]').forEach(b=>b.onclick=()=>{$('equipment-selector').value=b.dataset.selectEquipment;$('equipment-selector').dispatchEvent(new Event('change',{bubbles:true}));});}
$('equipment-search').onfocus=()=>renderEquipmentOptions('');
$('equipment-search').oninput=()=>renderEquipmentOptions();
$('equipment-search').onkeydown=e=>{if(e.key==='ArrowDown'){e.preventDefault();if($('equipment-options').hidden)renderEquipmentOptions();$('equipment-options').querySelector('button')?.focus();}if(e.key==='Escape'){closeEquipmentOptions();$('equipment-search').value=$('draft-equipment').value;}};
$('equipment-options').onkeydown=e=>{const buttons=[...$('equipment-options').querySelectorAll('button')],i=buttons.indexOf(document.activeElement);if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();buttons[Math.max(0,Math.min(buttons.length-1,i+(e.key==='ArrowDown'?1:-1)))]?.focus();}if(e.key==='Escape'){$('equipment-search').focus();closeEquipmentOptions();$('equipment-search').value=$('draft-equipment').value;}};
document.addEventListener('click',e=>{if(!e.target.closest('.equipment-picker')){closeEquipmentOptions();$('equipment-search').value=$('draft-equipment').value;}});

let equipmentDocumentRequest=0;
function filterEquipmentDocuments(){const query=$('equipment-document-search').value.trim().toLowerCase();const cards=[...$('equipment-document-list').querySelectorAll(':scope > article')];for(const card of cards)card.hidden=!!query&&!card.textContent.toLowerCase().includes(query);$('equipment-document-search-status').textContent=query&&cards.length&&!cards.some(card=>!card.hidden)?'No submitted manuals match your search.':'';}
$('equipment-document-search').oninput=filterEquipmentDocuments;

function resetEquipmentDocuments(){updateDocumentEquipment();equipmentDocumentRequest++;$('equipment-document-search').value='';$('equipment-document-search-status').textContent='';$('equipment-document-list').replaceChildren();$('equipment-document-count').textContent='';$('equipment-document-context').textContent='Select equipment to attach its PDFs.';}
async function loadEquipmentDocuments(){updateDocumentEquipment();const ship=$('draft-ship_id').value,equipment=$('equipment-selector').value;if(!ship||!equipment||equipment==='__legacy'){resetEquipmentDocuments();return;}const request=++equipmentDocumentRequest;const item=equipmentItems.find(x=>x.equipment_id===equipment);$('equipment-document-context').textContent=($('draft-ship_name').value||ship)+' · '+(item?.name||equipment);try{const docs=await api('equipment-documents?ship_id='+encodeURIComponent(ship)+'&equipment_id='+encodeURIComponent(equipment));if(request!==equipmentDocumentRequest)return;$('equipment-document-count').textContent=' · '+docs.length+' documents';$('equipment-document-list').innerHTML=docs.map(d=>`<article class="panel manual-card"><a href="${hatchURL('/api/equipment-documents/'+encodeURIComponent(d.id)+'/file')}">${esc(d.name)}</a><p>Revision: ${esc(d.revision)} · ${d.page_count} pages · ${esc(d.pages_without_text.length?'Some pages need OCR':'Text searchable')}</p><small>${esc(d.scope==='class'?'Class + equipment model':'This ship + equipment')} · ${d.indexed_pages} pages searchable</small>${d.pages_without_text.length?`<p>${d.pages_without_text.length} page(s) have no extractable text. Open the page viewer to distinguish graphics, scans and likely blank pages.</p>`:''}<div class="manual-analysis" data-analysis-document="${esc(d.id)}"><p class="analysis-status" role="status">Checking local AI analysis…</p><button type="button" data-analyze-manual="${esc(d.id)}">Analyze manual locally</button><details><summary>System knowledge &amp; page references</summary><div class="analysis-notes"></div></details></div><details class="pdf-viewer" data-document="${esc(d.id)}"><summary>View pages &amp; graphics</summary><div class="pdf-viewer-body"></div></details></article>`).join('')||'<p>No manuals for this equipment yet. Open Upload manuals or schematics below to add a PDF.</p>';filterEquipmentDocuments();refreshManualAnalysis()}catch(e){$('equipment-document-status').textContent='Unable to load documents: '+e.message}}
$('equipment-document-upload').onsubmit=async e=>{e.preventDefault();const ship=$('draft-ship_id').value,equipment=$('equipment-document-equipment').value;if(!ship||!equipment){$('equipment-document-status').textContent='Select a ship and equipment first.';return;}const button=e.submitter;button.disabled=true;let saved=0;const revision=$('equipment-document-revision').value.trim()||'Not specified',scope=$('equipment-document-scope').value,files=[...$('equipment-document-files').files];try{await flushDraft();for(const file of files){if(file.size>20*1024*1024)throw Error(file.name+' exceeds 20 MB');$('equipment-document-status').textContent='Uploading and extracting text: '+file.name;const response=await hatchFetch('/api/equipment-documents?'+new URLSearchParams({ship_id:ship,equipment_id:equipment,scope,revision}),{method:'POST',headers:{'X-Filename':encodeURIComponent(file.name)},body:file});const d=await response.json();if(!response.ok)throw Error(typeof d.detail==='string'?d.detail:JSON.stringify(d.detail));saved++;}$('equipment-document-files').value='';$('equipment-document-status').textContent=saved+' PDF(s) saved and queued for synchronization with the selected scope. Check indexing status below.';}catch(err){$('equipment-document-status').textContent=saved+' saved. '+err.message}finally{button.disabled=false;await loadEquipmentDocuments()}};

function updateDocumentEquipment(){const selected=$('equipment-selector').value;$('equipment-document-equipment').innerHTML='<option value="">Select equipment</option>'+equipmentItems.map(x=>`<option value="${esc(x.equipment_id)}">${esc(x.name)} · ${esc(x.work_center)} · ${equipmentWorkload(x).total} open</option>`).join('');$('equipment-document-equipment').value=selected;renderUploadDestination();}
function renderUploadDestination(){const item=equipmentItems.find(x=>x.equipment_id===$('equipment-document-equipment').value);if(!item){$('equipment-upload-destination').textContent='Choose equipment before uploading.';return;}const cls=$('equipment-document-scope').value==='class';$('equipment-upload-destination').textContent=cls?`Class distribution: ${item.name} on ${item.ship_class}. Queued for shore synchronization and retrieval by matching ships. Queued for shore transport.`:`Ship only: ${$('draft-ship_name').value} (${$('draft-hull_number').value}) · ${item.name}. Not distributed to other ships.`;}
$('equipment-document-equipment').onchange=()=>{$('equipment-selector').value=$('equipment-document-equipment').value;$('equipment-selector').dispatchEvent(new Event('change',{bubbles:true}));};
$('equipment-document-scope').onchange=renderUploadDestination;

// Render locally from the encrypted original, including graphics on text-bearing pages.
async function loadPdfViewer(viewer){
 if(!viewer.matches('.pdf-viewer')||!viewer.open||viewer.dataset.loaded||viewer.dataset.loading)return;
 viewer.dataset.loading='true';
 const body=viewer.querySelector('.pdf-viewer-body');body.textContent='Inspecting PDF pages locally…';
 try{
  const data=await api('equipment-documents/'+encodeURIComponent(viewer.dataset.document)+'/pages');
  body.innerHTML='<div class="pdf-selectors"><label>Show<select class="pdf-page-filter"><option value="graphics">Graphics</option><option value="content">All nonblank pages</option></select></label><label>Page<select class="pdf-page-select"></select></label></div><form class="pdf-find"><label>Find a page with local AI<input required maxlength="2000" placeholder="Diagram, component or question"></label><button>Find pages</button></form><div class="pdf-find-results" aria-live="polite"></div><div class="pdf-navigation"><button type="button" class="pdf-prev">← Previous</button><button type="button" class="pdf-next">Next →</button><button type="button" class="pdf-print" disabled>Print page</button><a class="pdf-image-link" target="_blank" rel="noopener">Open / save PNG ↗</a><span class="pdf-image-status" role="status"></span></div><div class="pdf-image-scroll"><img class="pdf-page-image" alt="" loading="lazy"></div>';
  const select=body.querySelector('.pdf-page-select'),filter=body.querySelector('.pdf-page-filter'),img=body.querySelector('img'),prev=body.querySelector('.pdf-prev'),next=body.querySelector('.pdf-next'),status=body.querySelector('.pdf-image-status'),link=body.querySelector('.pdf-image-link');
  const printButton=body.querySelector('.pdf-print');printButton.onclick=()=>printManualPage(img);
  let pages=[];
  function show(){printButton.disabled=true;const p=pages[select.selectedIndex];img.hidden=!p;link.hidden=!p;prev.disabled=!p||select.selectedIndex===0;next.disabled=!p||select.selectedIndex===pages.length-1;if(!p){img.removeAttribute('src');status.textContent='No pages match this filter.';return;}status.textContent='Loading page '+p.page+'…';if(viewer.closest('#cited-pdf-dialog'))$('cited-pdf-title').textContent=$('cited-pdf-dialog').dataset.source+' · PDF page '+p.page;img.alt='Document page '+p.page+' — '+p.kind;img.src=hatchURL(p.image_url);link.href=hatchURL(p.image_url);}
  function applyFilter(){const old=select.value;pages=data.pages.filter(p=>p.kind!=='No detected content'&&(filter.value!=='graphics'||p.has_graphics));select.replaceChildren();pages.forEach(p=>select.add(new Option('Page '+p.page+' · '+p.kind,p.page)));if(pages.some(p=>String(p.page)===old))select.value=old;select.disabled=!pages.length;show();}
  filter.onchange=()=>{body.querySelector('.pdf-find-results').replaceChildren();applyFilter()};
  img.onload=()=>{printButton.disabled=!pages.length;if(pages.length)status.textContent='';if(viewer.closest('#cited-pdf-dialog'))fitCitedPage()};img.onerror=()=>{if(pages.length)status.textContent='Unable to render this page. Download the original PDF to inspect it.'};
  select.onchange=show;prev.onclick=()=>{select.selectedIndex--;show()};next.onclick=()=>{select.selectedIndex++;show()};applyFilter();viewer.dataset.loaded='true';
  if(viewer.dataset.requestedPage){filter.value='content';applyFilter();const requested=viewer.dataset.requestedPage;if(pages.some(p=>String(p.page)===requested)){select.value=requested;show()}else{status.textContent='The cited page is unavailable in this document.';img.hidden=true;link.hidden=true;}}
  let findRequest=0;
  body.querySelector('.pdf-find').onsubmit=async e=>{e.preventDefault();const button=e.submitter,results=body.querySelector('.pdf-find-results'),request=++findRequest,mode=filter.value;button.disabled=true;results.textContent='Searching this manual with local AI…';try{const result=await api('ask',{text:e.target.querySelector('input').value,document_id:viewer.dataset.document,graphics_only:mode==='graphics'});if(request!==findRequest||mode!==filter.value)return;results.replaceChildren();const answer=document.createElement('p');answer.textContent=result.mode+' · '+result.answer;results.append(answer);const seen=new Set();for(const ref of result.references){if(seen.has(ref.page))continue;seen.add(ref.page);const open=document.createElement('button');open.type='button';open.textContent='Open page '+ref.page;open.onclick=()=>{select.value=String(ref.page);show()};results.append(open);}if(!seen.size){const empty=document.createElement('p');empty.textContent='No matching text found in the selected pages. Try a component name or browse the graphics manually.';results.append(empty);}}catch(e){results.textContent=e.message}finally{button.disabled=false}};

 }catch(e){body.textContent='Unable to inspect pages: '+e.message;}finally{delete viewer.dataset.loading}
}
document.addEventListener('toggle',event=>loadPdfViewer(event.target),true);

// Desktop pane dividers; widths are preferences for this browser only.
(()=>{
 const root=document.documentElement,defaults={left:245,right:360};let widths={...defaults};
 try{const saved=JSON.parse(localStorage.getItem('fleet-panel-widths')||'null');for(const side of ['left','right'])if(Number.isFinite(saved?.[side]))widths[side]=saved[side];}catch{}
 const handles={};
 function limits(side){return side==='left'?[180,Math.min(400,innerWidth-widths.right-400)]:[280,Math.min(650,innerWidth-widths.left-400)];}
 function apply(){if(innerWidth<=1100)return; widths.left=Math.max(180,Math.min(400,widths.left));widths.right=Math.max(280,Math.min(650,widths.right,innerWidth-widths.left-400));widths.left=Math.min(widths.left,innerWidth-widths.right-400);for(const side of ['left','right']){root.style.setProperty('--'+side+'-pane-width',widths[side]+'px');const [min,max]=limits(side);handles[side].setAttribute('aria-valuemin',min);handles[side].setAttribute('aria-valuemax',max);handles[side].setAttribute('aria-valuenow',Math.round(widths[side]));}}
 function save(){try{localStorage.setItem('fleet-panel-widths',JSON.stringify(widths));}catch{}}
 function resize(side,value){const [min,max]=limits(side);widths[side]=Math.max(min,Math.min(max,value));apply();}
 for(const side of ['left','right']){
  const h=document.createElement('div');handles[side]=h;h.className='pane-divider pane-divider-'+side;h.tabIndex=0;h.setAttribute('role','separator');h.setAttribute('aria-orientation','vertical');h.setAttribute('aria-label','Resize '+(side==='left'?'navigation':'assistant')+' panel');h.title='Drag to resize · arrow keys to adjust · double-click to reset';document.body.append(h);
  let drag=null;
  h.onpointerdown=e=>{if(e.button!==0)return;e.preventDefault();drag={x:e.clientX,width:widths[side],id:e.pointerId};h.setPointerCapture(e.pointerId);document.body.classList.add('resizing-panes');};
  h.onpointermove=e=>{if(drag&&e.pointerId===drag.id)resize(side,drag.width+(e.clientX-drag.x)*(side==='left'?1:-1));};
  function end(){if(!drag)return;drag=null;document.body.classList.remove('resizing-panes');save();}
  h.onpointerup=end;h.onpointercancel=end;h.onlostpointercapture=end;
  h.ondblclick=()=>{resize(side,defaults[side]);save()};
  h.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const [min,max]=limits(side);resize(side,e.key==='Home'?min:e.key==='End'?max:widths[side]+(e.key==='ArrowRight'?1:-1)*(side==='left'?1:-1)*(e.shiftKey?40:10));save();};
 }
 window.addEventListener('resize',apply);apply();
})();

// Show the active step immediately; reminder lookup never waits for model inference or draft saves.
let stepCoachVersion=0,stepCoachKey='';
async function scheduleStepCoach(force=false){
 if(!procedureData)return;
 const source=procedureData.source,step=sectionIndex,job=$('procedure-job').value,sailor=$('draft-owner').value;
 const key=[job,source,procedureData.revision_hash,step,sailor,[...reviewed].sort().join(',')].join('|');if(!force&&key===stepCoachKey)return;stepCoachKey=key;
 const version=++stepCoachVersion;
 let box=$('step-coach');if(!box){box=document.createElement('section');box.id='step-coach';box.setAttribute('aria-label','Current step guidance');box.setAttribute('aria-live','polite');$('chat-body').prepend(box);}
 document.querySelectorAll('.chat-welcome').forEach(w=>w.hidden=true);
 box.replaceChildren();const heading=document.createElement('strong'),details=document.createElement('div');heading.textContent='Step '+(step+1)+' of '+procedureData.sections.length+' · '+(sailor||'Unassigned')+(reviewed.has(step)?' · Checked':' · Current');details.textContent='Loading local lessons…';box.append(heading,details);
 try{
  const result=await api('step-coaching?'+new URLSearchParams({source,step,sailor}));if(version!==stepCoachVersion)return;
  details.replaceChildren();const profile=document.createElement('p');profile.className='coach-profile';profile.textContent='TRAINING HISTORY ·'+result.demo_history.completed_exercises+' completed exercises · '+result.profile.level;details.append(profile);
  for(const record of [...result.corrections,...result.lessons]){const p=document.createElement('p');p.className=record.kind==='correction'?'warning':'';p.textContent=(record.kind==='correction'?'Your prior correction: ':'Lesson: ')+record.text;details.append(p);const reference=document.createElement('details'),label=document.createElement('summary'),citation=document.createElement('p');reference.className='coach-reference';label.textContent='Source details';citation.textContent=record.id+' · '+(record.recorded||'Date unavailable');reference.append(label,citation);details.append(reference);}
  if(!result.corrections.length){const p=document.createElement('small');p.className='coach-history-note';p.textContent='No prior correction recorded for this step.';details.append(p);}
  const ask=document.createElement('button');ask.type='button';ask.className='coach-ask';ask.textContent='Ask AI about this step';ask.onclick=()=>{const input=$('chat-input');input.value='Explain my current step and the relevant recorded lessons or recorded lessons and corrections.';$('side-chat').dataset.stepHelp='true';$('side-chat').requestSubmit($('side-chat').querySelector('button'));};details.append(ask);
 }catch(e){if(version===stepCoachVersion)details.textContent='Local reminders unavailable: '+e.message;}
}
$('draft-owner').addEventListener('change',()=>scheduleStepCoach(true));

// Keyboard shortcuts: digits 1-7 switch views during demo
document.addEventListener('keydown',e=>{
 if(e.target.matches('input,textarea,select')||e.metaKey||e.ctrlKey||e.altKey)return;
 const views=['work','procedure','assistant'];
 const n=Number(e.key);
 if(n>=1&&n<=views.length){e.preventDefault();document.querySelector(`[data-view="${views[n-1]}"]`).click();}
});

// Connectivity indicator class
$('network').addEventListener('change',()=>{
 document.body.className=document.body.className.replace(/connectivity-\w+/g,'').trim();
 document.body.classList.add('connectivity-'+$('network').value);
});
document.body.classList.add('connectivity-'+$('network').value);

$('watch-search').addEventListener('focus',()=>{$('work-order-menu').open=true});
$('watch-search').addEventListener('keydown',e=>{if(e.key==='ArrowDown'){e.preventDefault();$('work-order-menu').open=true;$('jobs').querySelector('details[open] button')?.focus()}if(e.key==='Escape'){$('work-order-menu').open=false}});
$('jobs').addEventListener('keydown',e=>{const rows=[...$('jobs').querySelectorAll('details[open] [data-open-job]')],index=rows.indexOf(e.target);if(index<0)return;if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();rows[Math.max(0,Math.min(rows.length-1,index+(e.key==='ArrowDown'?1:-1)))].focus()}if(e.key==='Escape'){e.preventDefault();$('watch-search').focus();$('work-order-menu').open=false}});

let assignmentJob=null;
$('reassign-job').onclick=async()=>{
 if(!draftJob)return;
 try{await flushWorkspaceContext();assignmentJob=draftJob;$('assignment-form').reset();$('assignment-error').textContent='';
 const job=state.jobs.find(j=>j.id===assignmentJob),owner=jobDraft.owner||ownerOf(watchRows.find(r=>r.job.id===assignmentJob));
 $('assignment-job-context').textContent=job.id+' · '+job.title;$('assignment-current-owner').textContent='Current owner: '+(owner||'Unassigned');
 const names=[...new Set([...(watchOptions?.sailors||[]),...watchRows.filter(r=>r.draft.ship_id===watchShipId).map(ownerOf)].filter(Boolean))].sort();
 $('assignment-owner').innerHTML='<option value="">Select a sailor</option>'+names.map(n=>`<option value="${esc(n)}">${esc(n)}</option>`).join('');
 $('assignment-dialog').showModal();$('assignment-history').textContent='Loading assignment history…';
 const history=await api('jobs/'+assignmentJob+'/assignments');
 $('assignment-history').innerHTML=history.map(h=>`<p><strong>${esc(h.from_owner||'Unassigned')} → ${esc(h.to_owner)}</strong><br>${esc(h.reason||'No reason recorded')}<br><small>${esc(new Date(h.time).toLocaleString())}</small></p>`).join('')||'<p>No transfers recorded yet.</p>';
 }catch(e){notice(e.message)}
};
$('assignment-cancel').onclick=()=>$('assignment-dialog').close();
$('assignment-new-owner').oninput=()=>{if($('assignment-new-owner').value.trim())$('assignment-owner').value=''};
$('assignment-owner').onchange=()=>{if($('assignment-owner').value)$('assignment-new-owner').value=''};
$('assignment-form').onsubmit=async e=>{
 e.preventDefault();const owner=($('assignment-new-owner').value.trim()||$('assignment-owner').value),id=assignmentJob;
 if(!owner){$('assignment-error').textContent='Choose a sailor or enter a new sailor’s name.';return;}
 if(id!==draftJob){$('assignment-error').textContent='The selected work order changed. Reopen assignment.';return;}
 $('assignment-submit').disabled=true;$('assignment-error').textContent='Saving assignment…';
 try{await flushWorkspaceContext();const previous=jobDraft.owner;
 const saved=await api('jobs/'+id+'/assignment',{version:jobDraft.version,owner,reason:$('assignment-reason').value.trim()});
 jobDraft=saved;const row=watchRows.find(r=>r.job.id===id);if(row)row.draft=saved;
 if(![...$('draft-owner').options].some(o=>o.value===saved.owner))$('draft-owner').add(new Option(saved.owner,saved.owner));$('draft-owner').value=saved.owner;
 await loadWatch();if($('watch-sailor').value===previous){$('watch-sailor').value=saved.owner;renderWatch();}
 setWorkspaceSailor(saved.owner);updateProcedureJobs(id,saved.owner);renderExperience();updateChatContext();await greetSailor();scheduleStepCoach(true);await loadEquipment();
 $('assignment-dialog').close();$('assignment-status').textContent='Assigned to '+saved.owner+'. Progress and notes preserved.';
 }catch(error){$('assignment-error').textContent=error.message}finally{$('assignment-submit').disabled=false}
};

let manualAnalysisTimer=null;
async function refreshManualAnalysis(){
 clearTimeout(manualAnalysisTimer);let pending=false;
 await Promise.all([...document.querySelectorAll('[data-analysis-document]')].map(async panel=>{
  const id=panel.dataset.analysisDocument,status=panel.querySelector('.analysis-status'),button=panel.querySelector('button');
  button.onclick=async()=>{button.disabled=true;status.textContent='Queueing full-manual text analysis…';try{await api('equipment-documents/'+id+'/analysis',{});await refreshManualAnalysis()}catch(e){status.textContent=e.message;button.disabled=false}};
  try{const result=await api('equipment-documents/'+id+'/analysis');if(!panel.isConnected)return;
   const running=['running','queued'].includes(result.status);pending=pending||running;button.disabled=running||result.status==='complete';button.hidden=running||result.status==='complete';
   button.textContent=result.status==='complete'?'Manual text analyzed':running?'Analyzing locally…':result.completed_batches?'Resume manual analysis':'Analyze entire manual locally';
   status.textContent=(result.status==='complete'?'Local AI ready':running?'Local AI analyzing':result.status==='failed'?'Analysis needs attention':'Local AI: '+result.status)+' · '+(result.pages_analyzed||0)+' / '+result.total_pages+' pages analyzed · Text only'+(result.error?' · '+result.error:'')+(result.pages_without_text?.length?' · '+result.pages_without_text.length+' pages need OCR':'');
   status.title=result.completed_batches+' / '+result.total_batches+' batches complete. Diagram symbols and wiring are not interpreted.';
   panel.querySelector('.analysis-notes').innerHTML=(result.sections||[]).map(s=>`<article><p>${esc(s.overview)}</p><ul>${s.facts.map(f=>`<li>${esc(f.text)} ${f.pages.map(page=>`<a href="${HATCH_BASE}/api/equipment-documents/${encodeURIComponent(id)}/pages/${page}/image" target="_blank" rel="noopener">p. ${page}</a>`).join(', ')}</li>`).join('')}</ul></article>`).join('')||'<p>No saved system notes yet. Analysis reads every page with extractable text in batches and saves its progress on this host.</p>';
  }catch(e){status.textContent='Manual analysis unavailable: '+e.message;button.disabled=false;button.hidden=false}
 }));
 if(pending)manualAnalysisTimer=setTimeout(refreshManualAnalysis,4000);
}
$('suggest-manual-steps').onclick=()=>{
 if(!draftJob)return notice('Select a work order first.');
 $('chat-input').value='Using the analyzed equipment manuals and original cited pages, propose basic maintenance or troubleshooting steps for this job. Tailor them to the reported problem. Explain which checks depend on the exact symptom and identify any missing manual evidence. Do not invent settings or treat the synthetic demo checklist as a manufacturer procedure.';
 $('side-chat').requestSubmit($('side-chat').querySelector('button'));
};

function rememberConversation(id){markChatClosed(currentConversation?.job_id||draftJob,false);try{localStorage.setItem('fleet-last-conversation',id)}catch{}}
function referencePage(ref){
 const path=ref.image_url?.match(/^\/api\/equipment-documents\/([^/]+)\/pages\/(\d+)\/image$/);
 const documentId=ref.document_id||(path?decodeURIComponent(path[1]):'');
 const page=Number(ref.page||(path?path[2]:0));
 return /^[a-zA-Z0-9_-]+$/.test(documentId)&&Number.isInteger(page)&&page>0?{documentId,page}:null;
}
async function openCitedPage(ref){
 const target=referencePage(ref);if(!target)return notice('This reference does not identify an available PDF page.');
 const dialog=$('cited-pdf-dialog');dialog.dataset.source=(ref.source||'Manual reference').split(' · ')[0];$('cited-pdf-title').textContent=dialog.dataset.source+' · PDF page '+target.page;
 const viewer=document.createElement('div');viewer.className='pdf-viewer';viewer.dataset.document=target.documentId;viewer.dataset.requestedPage=String(target.page);
 const body=document.createElement('div');body.className='pdf-viewer-body';viewer.append(body);viewer.open=true;
 $('cited-pdf-content').replaceChildren(viewer);if(!dialog.open){dialog.show();dialog.style.left='16px';dialog.style.top='16px';}await loadPdfViewer(viewer);
}
async function printManualPage(image){
 if(!image?.getAttribute('src')||image.hidden)return;
 const page=document.createElement('div');page.id='manual-print-page';
 const copy=document.createElement('img');copy.alt=image.alt;copy.src=image.src;page.append(copy);
 document.getElementById('manual-print-page')?.remove();document.body.append(page);
 const cleanup=()=>page.remove();
 try{
  await copy.decode();
  window.addEventListener('afterprint',cleanup,{once:true});
  window.print();
 }catch(e){window.removeEventListener('afterprint',cleanup);cleanup();notice('Unable to prepare this page for printing. Try opening the page image.');}
}
function clampCitedPage(){
 const dialog=$('cited-pdf-dialog'),rect=dialog.getBoundingClientRect();
 dialog.style.left=Math.max(0,Math.min(rect.left,innerWidth-rect.width))+'px';
 dialog.style.top=Math.max(0,Math.min(rect.top,innerHeight-rect.height))+'px';
}
function fitCitedPage(){
 const dialog=$('cited-pdf-dialog'),img=dialog.querySelector('.pdf-page-image');
 if(!dialog.open||!img?.naturalWidth)return;
 // Measure controls after wrapping; size the window around the fitted page itself.
 for(let i=0;i<3;i++){
  const space=dialog.querySelector('.pdf-image-scroll').getBoundingClientRect();
  const width=Math.min(innerWidth-16,Math.max(Math.min(340,innerWidth-16),space.height*img.naturalWidth/img.naturalHeight+24));
  dialog.style.width=width+'px';
 }
 clampCitedPage();
}
(()=>{
 const dialog=$('cited-pdf-dialog'),handle=dialog.querySelector('.cited-pdf-header');let drag=null;
 handle.tabIndex=0;handle.title='Drag to move · Arrow keys to move';handle.setAttribute('aria-label','Move manual viewer');
 handle.addEventListener('pointerdown',e=>{if(e.button!==0||e.target.closest('button'))return;const r=dialog.getBoundingClientRect();drag={x:e.clientX-r.left,y:e.clientY-r.top};handle.setPointerCapture(e.pointerId);e.preventDefault()});
 handle.addEventListener('pointermove',e=>{if(!drag)return;dialog.style.left=(e.clientX-drag.x)+'px';dialog.style.top=(e.clientY-drag.y)+'px';clampCitedPage()});
 handle.addEventListener('pointerup',()=>{drag=null});handle.addEventListener('lostpointercapture',()=>{drag=null});
 handle.addEventListener('keydown',e=>{if(e.target!==handle||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();const r=dialog.getBoundingClientRect();dialog.style.left=(r.left+(e.key==='ArrowRight'?20:e.key==='ArrowLeft'?-20:0))+'px';dialog.style.top=(r.top+(e.key==='ArrowDown'?20:e.key==='ArrowUp'?-20:0))+'px';clampCitedPage()});
 dialog.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();dialog.close()}});
 window.addEventListener('resize',()=>{if(dialog.open){fitCitedPage();clampCitedPage()}});
})();
$('close-cited-pdf').onclick=()=>$('cited-pdf-dialog').close();
function renderChatAnswer(body,text,refs){
 // Keep readable page citations, but don't expose storage keys or model control text.
 text=text.replace(/\[(?:PDF-|CHAT-)[^\]]*$/g,'');
 text=text.replace(/\[PDF-[^\]]+\]/g,token=>refs.some(r=>'['+r.citation+']'===token)?token:('PDF page '+(token.match(/(?:-p|,\s*p)(\d+)/g)||[]).map(p=>p.match(/\d+/)[0]).join(', ')));
 text=text.replace(/<think>[\s\S]*?(<\/think>|$)/gi,'');
 text=text.replace(/\[(?:CHAT-|Report\s+|SYN-LESSON-|selected-section)[^\]]*\]/gi,'');
 text=text.split(/(\[PDF-[^\]]*\])/g).map(part=>part.startsWith('[PDF-')?part:part.replace(/\b(?:Report\s+)?[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b/gi,'prior maintenance report')).join('');
 body.innerHTML=renderMarkdown(text);
 const available=refs.filter(r=>referencePage(r));if(!available.length)return;
 const walker=document.createTreeWalker(body,NodeFilter.SHOW_TEXT),nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);
 for(const node of nodes){let remaining=node.textContent,changed=false;const fragment=document.createDocumentFragment();
  while(remaining){let chosen=null,index=Infinity;for(const ref of available){const at=remaining.indexOf('['+ref.citation+']');if(at>=0&&at<index){index=at;chosen=ref}}
   if(!chosen){fragment.append(document.createTextNode(remaining));break;}
   changed=true;fragment.append(document.createTextNode(remaining.slice(0,index)));const button=document.createElement('button');button.type='button';button.className='inline-page-link';button.textContent='PDF page '+referencePage(chosen).page;button.title=chosen.source;button.onclick=()=>openCitedPage(chosen);fragment.append(button);remaining=remaining.slice(index+chosen.citation.length+2);
  }
  if(changed)node.replaceWith(fragment);
 }
}
function savedReference(box,ref){
 const detail=document.createElement('details'),label=document.createElement('summary'),text=document.createElement('p');label.textContent=referencePage(ref)?'Manual excerpt · PDF page '+referencePage(ref).page:ref.conversation_id?'Related maintenance discussion':ref.citation==='selected-section'?'Current maintenance procedure':'Supporting maintenance record';text.textContent=ref.source+'\n\n'+ref.excerpt;detail.append(label,text);
 const target=referencePage(ref);
 if(target){
  let links=box.querySelector('.chat-page-links');if(!links){links=document.createElement('div');links.className='chat-page-links';const caption=document.createElement('small');caption.textContent='Manual reference pages';links.append(caption);box.append(links)}
  const key=target.documentId+':'+target.page;box.pageKeys=box.pageKeys||new Set();
  if(!box.pageKeys.has(key)){box.pageKeys.add(key);const open=document.createElement('button');open.type='button';open.textContent='PDF p. '+target.page+' · '+(ref.source||'Manual').split(' · ')[0];open.title=ref.source;open.onclick=()=>openCitedPage(ref);links.append(open)}
 }
 if(ref.image_url?.startsWith('/api/')){const a=document.createElement('a');a.href=ref.image_url;a.target='_blank';a.rel='noopener';a.textContent='Open page image '+ref.page;detail.append(a)}
 if(ref.conversation_id){const open=document.createElement('button');open.type='button';open.textContent='Open prior conversation';open.onclick=()=>openSavedConversation(ref.conversation_id).catch(e=>notice(e.message));detail.append(open)}box.append(detail);
}
function conversationOptionLabel(c){return (c.job_id||'General')+' · '+c.title+' · '+new Date(c.updated).toLocaleString([], {year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',second:'2-digit'});}
function conversationEquipmentScope(){return workspaceEquipmentFilter||(draftJob?jobDraft?.equipment_id:'')||'';}
function conversationMatchesEquipment(c){const equipment=conversationEquipmentScope();return !!equipment&&c.context?.equipment_id===equipment;}
function syncConversationEquipment(){
 const select=$('saved-chat-select'),scope=conversationEquipmentScope();
 if(select.dataset.equipment===scope)return;
 select.dataset.equipment=scope;select.replaceChildren(new Option(scope?'Open history to load equipment conversations':'Select equipment to view conversations',''));
 if($('saved-chats').open)loadEquipmentConversations();
}
async function loadEquipmentConversations(){
 const scope=conversationEquipmentScope(),select=$('saved-chat-select');select.dataset.equipment=scope;
 select.replaceChildren(new Option(scope?'Loading equipment conversations…':'Select equipment to view conversations',''));
 if(!scope)return;
 try{
  const items=await api('conversations?equipment_id='+encodeURIComponent(scope));
  if(scope!==conversationEquipmentScope())return;
  select.replaceChildren(...items.filter(conversationMatchesEquipment).map(c=>new Option(conversationOptionLabel(c),c.id)));
  if(currentConversation&&conversationMatchesEquipment(currentConversation))selectConversationOption(currentConversation);
  if(!select.options.length)select.add(new Option('No conversations saved for this equipment',''));
 }catch(e){if(scope===conversationEquipmentScope()){select.replaceChildren(new Option('Unable to load conversations',''));$('chat-save-status').textContent=e.message}}
}
function selectConversationOption(c){
 syncConversationEquipment();if(!conversationMatchesEquipment(c))return;
 const select=$('saved-chat-select');for(const option of [...select.options])if(!option.value)option.remove();
 let option=[...select.options].find(o=>o.value===c.id);if(!option){option=new Option('',c.id);select.prepend(option);}option.textContent=conversationOptionLabel(c);select.value=c.id;
}
function displayConversation(c){
 clearTimeout(conversationPoll);conversationLoadVersion++;currentConversation=c;selectConversationOption(c);$('chat-thread-title').textContent=c.title;rememberConversation(c.id);chatHistory=[];$('chat-messages').replaceChildren();
 for(const m of c.messages){const text=m.status==='pending'?'Response in progress on the local host…':m.content;const box=chatMessage(m.role,text);if(m.role==='assistant'&&m.status==='complete')renderChatAnswer(box.querySelector('p'),text,m.references||[]);const stamp=document.createElement('small');stamp.textContent=new Date(m.time).toLocaleString()+' · '+m.status+(m.context?.owner?' · '+m.context.owner:'');box.insertBefore(stamp,box.querySelector('p'));for(const ref of m.references||[])savedReference(box,ref);if(m.status==='complete'&&m.content)chatHistory.push({role:m.role,content:m.content});}
 const pending=c.messages.some(m=>m.status==='pending');$('side-chat').querySelector('button').disabled=pending;$('clear-chat').disabled=pending;
 $('chat-save-status').textContent='Saved encrypted on host · '+new Date(c.updated).toLocaleString();$('chat-status').textContent=pending?'Waiting for saved response…':'Conversation restored';
 if(pending)conversationPoll=setTimeout(async()=>{try{const latest=await api('conversations/'+c.id);if(currentConversation?.id===c.id)displayConversation(latest)}catch(e){$('chat-save-status').textContent='Unable to refresh conversation: '+e.message}},2000);
}
async function refreshConversationSaveStatus(id){try{const c=await api('conversations/'+id);if(currentConversation?.id!==id)return;currentConversation=c;selectConversationOption(c);$('chat-thread-title').textContent=c.title;$('chat-save-status').textContent='Saved encrypted on host · '+new Date(c.updated).toLocaleTimeString()}catch(e){$('chat-save-status').textContent='Could not confirm saved conversation: '+e.message}}
async function openSavedConversation(id,view='assistant'){
 if(!id)return;
 const c=await api('conversations/'+encodeURIComponent(id));
 if(c.job_id&&c.job_id!==draftJob){if(c.context?.ship_id&&c.context.ship_id!==watchShipId)await selectDirectoryShip(c.context.ship_id);await startJob(c.job_id);}
 else if(!c.job_id&&draftJob)clearWorkspaceSelection();
 if(c.job_id!==draftJob&&c.job_id)throw Error('Open the work order before continuing this conversation.');
 displayConversation(c);updateChatContext();showView(view);
}
async function restoreLastConversation(){let id='',view='assistant';try{id=localStorage.getItem('fleet-last-conversation')||'';view=localStorage.getItem('fleet-chat-view')||'assistant'}catch{};if(id)try{await openSavedConversation(id,document.getElementById(view)?.classList.contains('view')?view:'assistant')}catch(e){$('chat-save-status').textContent='Could not restore previous conversation: '+e.message}}
$('saved-chats').addEventListener('toggle',()=>{if($('saved-chats').open)loadEquipmentConversations()});
$('open-saved-chat').onclick=async()=>{try{await openSavedConversation($('saved-chat-select').value)}catch(e){$('chat-save-status').textContent=e.message}};
$('download-chat').onclick=async()=>{const id=$('saved-chat-select').value||currentConversation?.id;if(!id)return notice('Choose a saved conversation first.');try{const c=await api('conversations/'+id);const text=['HATCH conversation: '+c.title,'Work order: '+(c.job_id||'General'),...c.messages.map(m=>[m.role.toUpperCase()+' · '+m.time+' · '+m.status,[m.context?.ship_name,m.context?.equipment,m.context?.owner].filter(Boolean).join(' · '),m.content,...(m.references||[]).map(r=>'['+r.citation+'] '+r.source+'\n'+r.excerpt)].join('\n'))].join('\n\n');downloadText('HATCH-'+(c.job_id||'general')+'-'+c.id.slice(0,8)+'.txt',text)}catch(e){$('chat-save-status').textContent=e.message}};

function reportsResolution(text){
 const normalized=text.toLowerCase().replace(/[’‘]/g,"'").replace(/\bit'?s\b/g,'it is').replace(/\bthat'?s\b/g,'that is');
 if(/[?]|\b(if|should|could|would|might|maybe|hopefully)\b/.test(normalized))return false;
 if(/\b(not|never|hasn'?t|haven'?t|didn'?t|doesn'?t|isn'?t|wasn'?t|weren'?t|can'?t|cannot|still)\b.*\b(fixed|resolved|working|work|solved|repaired|operational)\b/.test(normalized))return false;
 return /\b((?:it|that|everything|the system|the machine|the door|the unit|problem|issue) (?:is |was |has been )?(?:now |finally )?(?:fixed|resolved|solved|repaired|working|operational)|now (?:it |the system )?(?:works|working)|it works|(?:fixed|resolved|solved|repaired) it|(?:solved|fixed|resolved) the (?:problem|issue)|working now|system restored|back (?:up|to normal)|that did it|all good now)\b/.test(normalized);
}
let findingsRequest=0;
async function draftFindingsFromChat(){
 if(!draftJob||!currentConversation)return notice('Open a work-order conversation first.');
 const id=draftJob,cid=currentConversation.id,request=++findingsRequest,fields=['symptom','actions_taken','outcome'],before=fields.map(f=>$('draft-'+f).value);
 const panel=$('troubleshooting-panel'),banner=$('findings-review-banner');showView('procedure');panel.open=true;panel.classList.add('needs-review');banner.hidden=false;banner.textContent='Preparing findings from this conversation with local AI…';panel.scrollIntoView({block:'start'});
 try{const proposal=await api('conversations/'+encodeURIComponent(cid)+'/findings-draft',{});
  if(request!==findingsRequest||draftJob!==id||currentConversation?.id!==cid)return;
  if(fields.some((f,i)=>$('draft-'+f).value!==before[i])){banner.textContent='Your findings changed while the draft was being prepared. Kept your edits. Click Record troubleshooting outcome to try again.';return;}
  if(proposal.job_id!==id)throw Error('Draft belongs to another work order');
  fields.forEach(f=>$('draft-'+f).value=proposal.fields[f]);$('draft-symptom-report').value=proposal.fields.symptom;$('resolution-status').value='not_verified';
  $('findings-review-check').hidden=false;$('findings-reviewed').checked=false;$('save-troubleshooting').disabled=true;
  banner.textContent=proposal.mode+' — review the problem, actions and outcome below, choose the resolution status, then check the review box to submit. This report has not been submitted.';
  const evidence=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Technician statements used';evidence.append(summary);for(const item of proposal.evidence||[]){const p=document.createElement('p');p.textContent=item.text;evidence.append(p)}banner.append(evidence);
  draftDirty=true;draftGeneration++;await flushDraft();panel.scrollIntoView({block:'start'});$('draft-actions_taken').focus({preventScroll:true});
 }catch(e){if(request===findingsRequest&&draftJob===id)banner.textContent='Could not prepare findings: '+e.message+'. You can enter them manually.';}
}
$('findings-reviewed').onchange=()=>{$('save-troubleshooting').disabled=!$('findings-reviewed').checked;};
$('record-chat-outcome').onclick=draftFindingsFromChat;

let newEventOptionsVersion=0;
async function loadNewEventOptions(){
 const version=++newEventOptionsVersion,ship=watchShipId;const fieldset=$('new-event-fields');fieldset.disabled=true;
 $('new-event-ship').textContent=shipDirectory?.ships.find(s=>s.id===ship)?.name||'Select a ship above before creating an event.';
 if(!ship)return;
 try{const data=await api('ships/'+encodeURIComponent(ship)+'/equipment');if(version!==newEventOptionsVersion||ship!==watchShipId)return;
 const equipment=$('new-event-equipment'),old=equipment.value;equipment.innerHTML='<option value="">Select equipment</option>'+data.items.map(x=>`<option value="${esc(x.equipment_id)}" data-center="${esc(x.work_center)}">${esc(x.name)}</option>`).join('');if(data.items.some(x=>x.equipment_id===old))equipment.value=old;
 const owner=$('new-event-owner'),previous=owner.value||$('watch-sailor').value,names=[...new Set([...watchRows.filter(r=>r.draft.ship_id===ship).map(ownerOf),...(watchOptions?.sailors||[])].filter(Boolean))].sort();owner.innerHTML='<option value="">Select sailor</option>'+names.map(n=>`<option>${esc(n)}</option>`).join('');owner.value=names.includes(previous)?previous:'';
 if(!$('new-event-date').value)$('new-event-date').value=watchOptions.today;fieldset.disabled=false;
 }catch(e){$('new-event-status').textContent='Could not load equipment: '+e.message;}
}
$('new-event-menu').addEventListener('toggle',()=>{if($('new-event-menu').open)loadNewEventOptions()});
$('new-event-equipment').onchange=()=>{const center=$('new-event-equipment').selectedOptions[0]?.dataset.center;if(center)$('new-event-center').value=center;};
$('new-event-form').onsubmit=async e=>{
 e.preventDefault();const ship=watchShipId,button=$('new-event-submit');if(!ship)return;button.disabled=true;$('new-event-status').textContent='Creating maintenance event…';
 try{const result=await api('work-events',{ship_id:ship,equipment_id:$('new-event-equipment').value,owner:$('new-event-owner').value,title:$('new-event-title').value,work_center:$('new-event-center').value,due_date:$('new-event-date').value,time:$('new-event-time').value,priority:$('new-event-priority').value,corrective:$('new-event-type').value==='corrective',description:$('new-event-description').value});
 $('new-event-form').reset();if(ship===watchShipId){$('watch-search').value='';$('watch-filter').value='all';$('watch-center').value='';$('watch-sailor').value='';}await refresh();
 $('new-event-status').replaceChildren(document.createTextNode(result.job.id+' created · '+result.draft.owner+' · due '+result.schedule.due_date+' '));const open=document.createElement('button');open.type='button';open.textContent='Open work order';open.onclick=()=>startJob(result.job.id);$('new-event-status').append(open);$('work-order-menu').open=true;
 }catch(e){$('new-event-status').textContent='Unable to create event: '+e.message;}finally{button.disabled=false}
};

let repeatJobId=null;
$('repeat-job').onclick=()=>{repeatJobId=draftJob;const row=watchRows.find(r=>r.job.id===repeatJobId);if(!row)return;$('repeat-job-context').textContent=row.job.id+' · '+row.job.title;$('repeat-job-date').value=watchOptions.today;$('repeat-job-time').value=row.schedule?.time||'09:00';$('repeat-job-error').textContent='';$('repeat-job-dialog').showModal();};
$('repeat-job-cancel').onclick=()=>$('repeat-job-dialog').close();
$('repeat-job-form').onsubmit=async e=>{e.preventDefault();const button=$('repeat-job-submit');button.disabled=true;try{await flushWorkspaceContext();const result=await api('jobs/'+encodeURIComponent(repeatJobId)+'/repeat',{due_date:$('repeat-job-date').value,time:$('repeat-job-time').value});$('repeat-job-dialog').close();await refresh();await startJob(result.job.id);notice(result.job.id+' created from '+repeatJobId+'. Original completion record preserved.');}catch(e){$('repeat-job-error').textContent=e.message;}finally{button.disabled=false}};

// Searchable sailor controls retain the underlying select as the form's canonical value.
function enhanceSailorSelect(id){
 const select=$(id),required=select.required,wrapper=document.createElement('div');wrapper.className='sailor-picker';
 select.before(wrapper);wrapper.append(select);select.hidden=true;select.required=false;select.tabIndex=-1;
 const input=document.createElement('input');input.id=id+'-search';input.type='text';input.autocomplete='off';input.placeholder='Type a sailor’s name';input.required=required;input.setAttribute('role','combobox');input.setAttribute('aria-autocomplete','list');input.setAttribute('aria-expanded','false');
 const toggle=document.createElement('button');toggle.type='button';toggle.className='sailor-picker-toggle';toggle.textContent='▾';toggle.setAttribute('aria-label','Show sailor choices');
 const list=document.createElement('div');list.id=id+'-choices';list.className='sailor-choices';list.setAttribute('role','listbox');list.hidden=true;input.setAttribute('aria-controls',list.id);
 wrapper.append(input,toggle,list);const label=wrapper.closest('label');if(label)label.htmlFor=input.id;
 let active=-1;
 function close(){list.hidden=true;input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');active=-1;}
 function sync(){input.disabled=toggle.disabled=select.disabled;if(document.activeElement!==input||list.hidden){input.value=select.value?(select.selectedOptions[0]?.textContent||select.value):'';input.placeholder=select.options[0]?.textContent||'Type a sailor’s name';input.setCustomValidity('');}if(select.disabled)close();}
 function choose(value){select.value=value;close();sync();select.dispatchEvent(new Event('change',{bubbles:true}));input.focus();close();sync();}
 function show(query=''){
  if(select.disabled)return;const words=query.toLowerCase().trim().split(/\s+/).filter(Boolean);list.replaceChildren();active=-1;
  [...select.options].filter(o=>!o.disabled&&words.every(w=>o.textContent.toLowerCase().includes(w))).forEach((o,i)=>{const button=document.createElement('button');button.type='button';button.tabIndex=-1;button.id=id+'-choice-'+i;button.setAttribute('role','option');button.setAttribute('aria-selected',String(o.value===select.value));button.textContent=o.textContent;button.onclick=()=>choose(o.value);list.append(button)});
  if(!list.children.length){const empty=document.createElement('p');empty.textContent='No matching sailors';list.append(empty)}list.hidden=false;input.setAttribute('aria-expanded','true');
 }
 input.onfocus=()=>show('');input.oninput=()=>{show(input.value);input.setCustomValidity('Select a sailor from the matching choices.');};toggle.onclick=()=>{if(list.hidden){input.focus();show('')}else{close();sync()}};
 input.onkeydown=e=>{if(e.key==='Escape'){close();sync();return}if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();if(list.hidden)show('');const choices=[...list.querySelectorAll('[role="option"]')];if(!choices.length)return;active=Math.max(0,Math.min(choices.length-1,active+(e.key==='ArrowDown'?1:-1)));choices.forEach((b,i)=>b.classList.toggle('active',i===active));input.setAttribute('aria-activedescendant',choices[active].id);choices[active].scrollIntoView({block:'nearest'});}if(e.key==='Enter'&&!list.hidden){e.preventDefault();const choices=list.querySelectorAll('[role="option"]');if(active>=0)choices[active].click();else if(choices.length===1)choices[0].click();}};
 wrapper.addEventListener('focusout',e=>{if(!wrapper.contains(e.relatedTarget)){close();sync()}});
 document.addEventListener('click',e=>{if(!wrapper.contains(e.target)){close();sync()}});
 const valueProperty=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value');Object.defineProperty(select,'value',{get(){return valueProperty.get.call(this)},set(value){valueProperty.set.call(this,value);sync()}});
 new MutationObserver(sync).observe(select,{childList:true,subtree:true,attributes:true,attributeFilter:['disabled','selected']});select.addEventListener('change',sync);select.form?.addEventListener('reset',()=>setTimeout(sync,0));sync();
}
['watch-sailor','workspace-sailor','assignment-owner','new-event-owner'].forEach(enhanceSailorSelect);

function resetFindingsReview(){findingsRequest++;$('findings-review-banner').hidden=true;$('findings-review-check').hidden=true;$('findings-reviewed').checked=false;$('save-troubleshooting').disabled=false;$('troubleshooting-panel').classList.remove('needs-review');}
