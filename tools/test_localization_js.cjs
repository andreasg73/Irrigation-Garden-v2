const fs=require('fs'),assert=require('assert');
const root=require('path').resolve(__dirname,'..');
const before=JSON.parse(fs.readFileSync(root+'/dist/en/irrigation_dashboard.json'));
const after=JSON.parse(fs.readFileSync(root+'/dist/pl/irrigation_dashboard.json'));
const pairs=[];let syntax=0;
function walk(a,b,path=''){
 if(Array.isArray(a))a.forEach((v,i)=>walk(v,b[i],path+'/'+i));
 else if(a&&typeof a==='object')for(const[k,v]of Object.entries(a))walk(v,b[k],path+'/'+k);
 else if(typeof a==='string'){
  if(a.includes('${')===false)assert(!b.includes('${'),'Introduced config-template marker '+path);
  if(b.trim().startsWith('[[[')){new Function('states','entity','hass','user','variables',b.trim().slice(3,-3));syntax++;}
  if(b.trim().startsWith('${')){new Function('states','ZONE_NAME','CYCLE_NAME','USER1_NAME','USER2_NAME','return ('+b.trim().slice(2,-1)+');');syntax++;}
  if(a!==b&&(a.trim().startsWith('[[[')||a.trim().startsWith('${')))pairs.push({path,a,b});
 }
}
walk(before,after);
syntax=0;
function syntaxAll(x){
 if(Array.isArray(x))x.forEach(syntaxAll);
 else if(x&&typeof x==='object')Object.values(x).forEach(syntaxAll);
 else if(typeof x==='string'){
  if(x.trim().startsWith('[[[')){new Function('states','entity','hass','user','variables',x.trim().slice(3,-3));syntax++;}
  if(x.trim().startsWith('${')){new Function('states','ZONE_NAME','CYCLE_NAME','USER1_NAME','USER2_NAME','return ('+x.trim().slice(2,-1)+');');syntax++;}
 }
}
syntaxAll(after);
const rows=[];function check(id,run){run();rows.push({id,passed:true});}
const stock={};
function state(id,value,attributes={}){stock[id]={entity_id:id,state:value,attributes};}
for(let c=1;c<=3;c++)state(`input_boolean.irrigation_cycle${c}_running`,'off');
for(let z=1;z<=16;z++){state(`timer.irrigation_zone${z}_timer`,'idle');state(`input_text.irrigation_zone${z}_name`,'Zone'+z);}
state('input_text.irrigation_cycle1_name','Cycle1');state('input_text.irrigation_cycle2_name','Cycle2');state('input_text.irrigation_cycle3_name','Manual Cycle');
state('input_text.irrigation_current_status','SYSTEM IDLE');state('sensor.irrigation_next_run','SYSTEM IS OFF');
const states=new Proxy(stock,{get:(o,k)=>o[k]||{entity_id:k,state:'off',attributes:{}}});
function run(code,entity={state:'off',attributes:{}},args={}){
 if(code.trim().startsWith('${'))return new Function('states','ZONE_NAME','CYCLE_NAME','USER1_NAME','USER2_NAME','return ('+code.trim().slice(2,-1)+')')(states,args.zone??'Zone1',args.cycle??'Manual Cycle',args.user??'Alicja','Jan');
 return new Function('states','entity','hass','user','variables',code.trim().slice(3,-3)).call({},states,entity,{}, {name:'User'},{});
}
const manual=pairs.find(p=>p.path.endsWith('/name')&&p.a.includes("return 'Run This Zone Now'"));assert(manual);
check('manual.start.label',()=>{assert.equal(run(manual.a),'Run This Zone Now');assert.equal(run(manual.b),'Uruchom tę strefę');});
check('manual.stop.label',()=>{state('timer.irrigation_zone1_timer','active');assert.equal(run(manual.a,{state:'on'}),'Stop This Zone');assert.equal(run(manual.b,{state:'on'}),'Zatrzymaj tę strefę');state('timer.irrigation_zone1_timer','idle');});
const cycle=pairs.find(p=>p.path.endsWith('/name')&&p.a.includes("return states['input_text.irrigation_cycle3_name'].state.toUpperCase()"));assert(cycle);
check('default.cycle.label',()=>assert.equal(run(cycle.b),'CYKL RĘCZNY'));
check('custom.name.preserved',()=>{const value="GENERAL SCHEDULE 'A' — Żółć";state('input_text.irrigation_cycle3_name',value);assert.equal(run(cycle.b),value.toUpperCase());state('input_text.irrigation_cycle3_name','Manual Cycle');});
const zone=pairs.find(p=>p.a.trim()==='${ ZONE_NAME }');assert(zone);
check('default.zone.expression',()=>assert.equal(run(zone.b),'Strefa 1'));
check('custom.zone.expression',()=>{const value='SCHEDULE sad "A"';state('input_text.irrigation_zone1_name',value);assert.equal(run(zone.b,{}, {zone:value}),value);state('input_text.irrigation_zone1_name','Zone1');});
const header=pairs.find(p=>p.a.includes("return states['sensor.irrigation_next_run'].state"));assert(header);
check('runtime.status.output.only',()=>{assert.equal(run(header.b),'SYSTEM WYŁĄCZONY');assert.equal(stock['sensor.irrigation_next_run'].state,'SYSTEM IS OFF');});
check('default.state.display.localized',()=>{
 const nodes=[];function collect(x){if(Array.isArray(x))x.forEach(collect);else if(x&&typeof x==='object'){if(x.type==='custom:button-card'&&x.entity==='input_text.irrigation_current_status'&&x.show_state&&x.state_display)nodes.push(x);Object.values(x).forEach(collect);}}collect(after);assert(nodes.length);assert.equal(run(nodes[0].state_display,{state:'SYSTEM IDLE'}),'SYSTEM GOTOWY');
});
check('cancelled.default.name.localized',()=>{const p=pairs.find(p=>p.path.endsWith('/label')&&p.a.includes("return states['input_text.irrigation_previous_run_cycle_name'].state"));assert(p);state('input_text.irrigation_previous_run_cycle_name','Manual Cycle (Cancelled)');assert.equal(run(p.b),'Cykl ręczny (Przerwano)');assert.equal(stock['input_text.irrigation_previous_run_cycle_name'].state,'Manual Cycle (Cancelled)');});
check('numeric.invalid.handling.preserved',()=>{
 const p=pairs.find(p=>p.a.includes('var total_seconds = Number(raw)'));assert(p);
 assert.equal(run(p.b,{state:'unknown',attributes:{}}),run(p.a,{state:'unknown',attributes:{}}));
});
check('technical.ids.not.translated',()=>{assert(!fs.readFileSync(root+'/dist/pl/irrigation_dashboard.json','utf8').includes('input_boolean.cykl'));});
const report={syntax_cases:syntax,wrapped_presentation_expressions:pairs.length,rows};
fs.writeFileSync(root+'/tests/javascript-results.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
