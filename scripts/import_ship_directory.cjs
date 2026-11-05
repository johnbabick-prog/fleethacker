// Usage: curl -L -A 'Mozilla/5.0' URL -o /tmp/ships.html
// node scripts/import_ship_directory.cjs /tmp/ships.html
const fs=require('node:fs'),{JSDOM}=require('jsdom');
const url='https://en.wikipedia.org/wiki/List_of_current_ships_of_the_United_States_Navy';
const d=new JSDOM(fs.readFileSync(process.argv[2],'utf8')).window.document;
const groups=['Commissioned','Non-commissioned','Support','Ready Reserve Force','Reserve fleet'];
const tables=[...d.querySelectorAll('table.wikitable')].filter(t=>t.rows[0]?.textContent.includes('Ship name'));
const clean=cell=>{let n=cell.cloneNode(true);n.querySelectorAll('sup,.sortkey,.sorttext,[style*="display:none"],[style*="display: none"]').forEach(x=>x.remove());return n.textContent.replace(/\s+/g,' ').trim()};
let ships=[];
for(let i=0;i<5;i++){
 let spans=[];
 for(const row of [...tables[i].rows].slice(1)){
  let cols=[],column=0;
  for(const cell of row.cells){while(spans[column]?.remaining){cols[column]=spans[column].text;spans[column].remaining--;column++;}let value=clean(cell);cols[column]=value;if(cell.rowSpan>1)spans[column]={text:value,remaining:cell.rowSpan-1};column++;}
  while(spans[column]?.remaining){cols[column]=spans[column].text;spans[column].remaining--;column++;}
  let [name,hull,cls]=cols;hull=hull.replace(/ex-.*$/,'').trim();name=name.replace(/^Unnamedex-/,'Unnamed (ex-');if(name.startsWith('Unnamed (ex-'))name+=')';if(!name||!hull||!cls)throw Error('Missing identity field');
  ships.push({id:hull==='—'?'name-'+name.toLowerCase().replace(/[^a-z0-9]+/g,'-'):hull,name,hull_number:hull==='—'?'No hull number':hull,class_name:cls,status:groups[i],source:url});
 }
}
const existing=JSON.parse(fs.readFileSync('config/ship_classes.json')).groups;
const names=Object.values(existing).flat();
const aliases={'2nd Lt. John P. Bobo':'Bobo'};
for(const ship of ships){const raw=aliases[ship.class_name]||ship.class_name;const match=names.find(n=>n.split(' (')[0].toLowerCase()===raw.toLowerCase());ship.ship_class=match||ship.class_name;}
ships.sort((a,b)=>a.name.replace(/^(USS|USNS|MV|SS|GTS|TS) /,'').localeCompare(b.name.replace(/^(USS|USNS|MV|SS|GTS|TS) /,''))||a.id.localeCompare(b.id));
const ids=new Set();for(const ship of ships){if(ids.has(ship.id))throw Error('Duplicate hull '+ship.id);ids.add(ship.id);}
fs.writeFileSync('config/ships.json',JSON.stringify({source:url,retrieved:new Date().toISOString(),scope:'Current-ships tables: commissioned, non-commissioned, support, Ready Reserve Force and reserve fleet. Excludes future and historical ships outside those tables. Public-source snapshot, not an authoritative operational status feed.',ships},null,2)+'\n');
console.log(`${ships.length} ships; ${new Set(ships.map(s=>s.ship_class)).size} classes`);
