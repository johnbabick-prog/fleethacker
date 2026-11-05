// Unit test of the navigation handler; no browser or network required.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('static/app.js','utf8');
const handler=source.slice(source.indexOf('let openingJob=false;'));
function setup(fail=false){
 const elements=new Map();const get=id=>{if(!elements.has(id))elements.set(id,{value:'',textContent:'',scrollIntoView(){}});return elements.get(id)};
 const views=[{id:'work',hidden:false},{id:'procedure',hidden:true}];let loaded=0,error='';
 const ctx={document:{querySelectorAll:s=>s==='.view'?views:[]},$:get,state:{jobs:[{id:'DEMO-11',title:'Demo job'}]},flushDraft:async()=>{},procedureDirty:false,confirm:()=>true,updateProcedureJobs:()=>{},loadProcedureSession:async()=>{loaded++;if(fail)throw Error('Service unavailable')},notice:s=>error=s};
 vm.createContext(ctx);vm.runInContext(handler,ctx);return {ctx,get,views,loaded:()=>loaded,error:()=>error};
}
(async()=>{
 let t=setup(),button={textContent:'Start job',disabled:false};await t.ctx.startJob('DEMO-11',button);
 assert.equal(t.get('procedure-job').value,'DEMO-11');assert.equal(t.views[1].hidden,false);assert.equal(t.loaded(),1);assert.equal(t.get('job-open-status').textContent,'');assert.equal(button.disabled,false);
 t=setup(true);await t.ctx.startJob('DEMO-11',button);assert.match(t.get('job-open-status').textContent,/Service unavailable/);assert.match(t.error(),/Unable to open/);assert.equal(button.disabled,false);
 console.log('Start job: navigation, loading completion, failure feedback and button recovery passed.');
})().catch(e=>{console.error(e);process.exit(1)});
