/* Isolated programmatic DOM contracts, not real-browser input or geometry. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const crypto=require('node:crypto');
const ROOT=path.resolve(__dirname,'..');
const source=fs.readFileSync(process.env.IG_UI_SOURCE||path.join(ROOT,'custom_components/irrigation_garden/frontend/irrigation-garden-ui.js'),'utf8');
(async()=>{
 const {Window}=await import(pathToFileURL(require.resolve('happy-dom')).href);
 const w=new Window({url:'https://weather-fixture.invalid',settings:{enableJavaScriptEvaluation:true,disableJavaScriptFileLoading:true,disableCSSFileLoading:true}});
 const errors=[],requests=[],results=[];let escapeAttempts=0;
 w.addEventListener('error',e=>errors.push(e.message));
 for(const name of ['fetch','WebSocket','XMLHttpRequest','EventSource','Worker','SharedWorker'])w[name]=()=>{escapeAttempts++;throw Error('Blocked transport');};
 w.navigator.sendBeacon=()=>{escapeAttempts++;throw Error('Blocked beacon');};
 w.eval(source);
 const helper='input_text.irrigation_external_sensor_current_temp',rain='input_text.irrigation_external_sensor_forecast_rain',now='input_text.irrigation_external_sensor_raining_now';
 const old='2026-10-20T08:00:00Z',recent='2026-10-25T08:00:00Z';
 const entity=(id,value,unit)=>({entity_id:id,state:value,attributes:{unit_of_measurement:unit},last_updated:old});
 let states={[helper]:entity(helper,'sensor.fixture_temperature'),[rain]:entity(rain,'sensor.fixture_forecast'),[now]:entity(now,'binary_sensor.fixture_rain'),
 'sensor.fixture_temperature':entity('sensor.fixture_temperature','15','°C'),
 'sensor.fixture_forecast':entity('sensor.fixture_forecast','0','mm'),
 'binary_sensor.fixture_rain':entity('binary_sensor.fixture_rain','off')};
 let fault='normal',release;
 const connection={};
 const callApi=async(method,route,data)=>{
   requests.push({method,route,data});assert.equal(method,'POST');assert.equal(route,'template');assert.deepEqual(Object.keys(data),['template']);
   const rows=Object.keys(states).filter(id=>id.startsWith('input_text.')).map(id=>({helper:id,source:states[id].state,last_reported:recent,last_updated:old}));
   if(fault==='reject')throw Error('Injected read error');
   if(fault==='delay')await new Promise(r=>release=r);
   if(fault==='malformed')return '{}';
   return JSON.stringify(rows);
 };
 const hass=()=>({states:{...states},connection,callApi,locale:{language:'en'},config:{time_zone:'UTC'},callService:()=>{throw Error('No writes allowed in diagnostic tests');}});
 const mount=(id,kind,domains,units)=>{const e=w.document.createElement('irrigation-garden-entity-picker');e.setConfig({entity:id,diagnostic_kind:kind,domains,units});e.hass=hass();w.document.body.append(e);return e;};
 const temp=mount(helper,'measurement',['sensor'],['°C']),forecast=mount(rain,'forecast',['sensor'],['mm']),binary=mount(now,'measurement',['binary_sensor']);
 const legacy=w.document.createElement('irrigation-garden-entity-picker');legacy.setConfig({entity:helper,domains:['sensor'],units:['°C'],ui_labels:{save:'Zapisz'}});legacy.hass=hass();w.document.body.append(legacy);
 const all=[temp,forecast,binary],q=(e,s)=>e.shadowRoot.querySelector(s),tick=async()=>{await Promise.resolve();await new Promise(r=>setImmediate(r));};
 const update=()=>all.forEach(e=>e.hass=hass());
 const check=(id,fn)=>{fn();results.push({id,status:'passed',input_method:'programmatic DOM'});};
 const state=(id,value,unit)=>{states={...states,[id]:entity(id,value,unit)};update();};
 const health=(e,text)=>assert.ok(q(e,'.health').textContent.includes(text),q(e,'.health').textContent);
 try{
  await tick();
  check('REPORT.coalesced-read',()=>assert.equal(requests.length,1));
  check('LEGACY.polish-dashboard-without-rebuild',()=>{assert.equal(q(legacy,'.kind').textContent,'Pomiar');assert.ok(q(legacy,'.health').textContent.includes('poprawna'));});
  check('REPORT.unchanged-value-is-healthy',()=>{health(temp,'Available');assert.ok(q(temp,'.reported').textContent.includes('10/25/26'));assert.ok(q(temp,'.updated').textContent.includes('10/20/26'));});
  check('KIND.measurement-versus-forecast',()=>{assert.equal(q(temp,'.kind').textContent,'Measurement');assert.equal(q(forecast,'.kind').textContent,'Forecast');});
  for(const [value,expected]of [['','Not configured'],['unknown','Not configured'],['Not set','Not configured'],['sensor.fixture_missing','does not exist']]){state(helper,value);check('MAPPING.'+(value||'empty'),()=>health(temp,expected));}
  state(helper,'sensor.fixture_temperature');
  for(const [value,unit,expected]of [['unavailable','°C','Unavailable'],['unknown','°C','known value'],['10','°F','Wrong unit'],['NaN','°C','Invalid value'],['Infinity','°C','Invalid value'],[' ','°C','Invalid value'],['0x10','°C','Invalid value'],['-12.5','°C','Available']]){state('sensor.fixture_temperature',value,unit);check('VALUE.'+JSON.stringify([value,unit]),()=>health(temp,expected));}
  state(helper,'binary_sensor.fixture_rain');check('DOMAIN.invalid',()=>health(temp,'Wrong entity type'));
  state(helper,'sensor.fixture_temperature');state('sensor.fixture_temperature','15','°C');
  state('sensor.fixture_temperature','8.10000038146973','°C');check('VALUE.readable-number',()=>assert.equal(q(temp,'.reading').textContent,'Value: 8.1 °C'));state('sensor.fixture_temperature','15','°C');
  state('sensor.fixture_forecast','-1','mm');check('RAIN.negative-invalid',()=>health(forecast,'Invalid value'));
  state('sensor.fixture_forecast','0','mm');check('RAIN.zero-valid',()=>health(forecast,'Available'));
  state('sensor.fixture_forecast','10','mm/h');check('RAIN.rate-rejected',()=>health(forecast,'Wrong unit'));
  state('binary_sensor.fixture_rain','open');check('BINARY.invalid-state',()=>health(binary,'Invalid value'));
  state('binary_sensor.fixture_rain','off');check('BINARY.dry-valid',()=>{health(binary,'Available');assert.ok(q(binary,'.polarity').textContent.includes('on = raining'));});
  state('sensor.fixture_temperature','<img src=x onerror=alert(1)>','°C');check('TEXT.hostile-value-is-inert',()=>{assert.equal(q(temp,'.diagnostics').querySelector('img'),null);health(temp,'Invalid value');});
  state('sensor.fixture_temperature','15','°C');
  q(temp,'.open').click();const search=q(temp,'.search');search.value='fixture';search.dispatchEvent(new w.Event('input'));search.focus();search.setSelectionRange(3,3);
  fault='delay';q(temp,'.refresh').click();await tick();const count=requests.length;q(forecast,'.refresh').click();await tick();
  check('RACE.refresh-is-coalesced',()=>assert.equal(requests.length,count));
  states={...states,'sensor.fixture_new':entity('sensor.fixture_new','20','°C')};state(helper,'sensor.fixture_new');release();await tick();
  check('RACE.old-source-time-not-reused',()=>{assert.ok(q(temp,'.reported').textContent.includes('No report timestamp'));assert.ok(q(temp,'.value').textContent.includes('fixture_new'));});
  check('RACE.read-preserves-editor',()=>{assert.equal(q(temp,'.search'),search);assert.equal(search.value,'fixture');assert.equal(search.selectionStart,3);assert.equal(temp.shadowRoot.activeElement,search);});
  fault='reject';q(temp,'.refresh').click();await tick();check('FAULT.read-failure-visible',()=>assert.ok(q(temp,'.reported').textContent.includes('unavailable')));
  fault='malformed';q(temp,'.refresh').click();await tick();check('FAULT.malformed-read-visible',()=>assert.ok(q(temp,'.reported').textContent.includes('unavailable')));
  fault='normal';q(temp,'.refresh').click();await tick();check('FAULT.refresh-recovers',()=>assert.ok(q(temp,'.reported').textContent.includes('10/25/26')));
  states={...states,'sensor.fixture_new':{...states['sensor.fixture_new'],last_updated:recent}};update();check('RACE.new-state-rejects-old-timestamp',()=>assert.ok(q(temp,'.reported').textContent.includes('No report timestamp')));
  state(helper,'unavailable');check('MAPPING.helper-unavailable',()=>health(temp,'Mapping helper'));
  check('REPORT.throttled-on-hass-updates',()=>{const n=requests.length;for(let i=0;i<20;i++)update();assert.equal(requests.length,n);});
  check('ISO.no-runtime-errors',()=>assert.deepEqual(errors,[]));
  check('ISO.no-transport-escapes',()=>assert.equal(escapeAttempts,0));
 }finally{
   const report={layer:'happy-dom programmatic simulation; no physical input or geometry',source_sha256:crypto.createHash('sha256').update(source).digest('hex'),counts:{passed:results.length},results,read_requests:requests.length,errors,escapeAttempts};
   if(process.env.IG_WEATHER_REPORT)fs.writeFileSync(process.env.IG_WEATHER_REPORT,JSON.stringify(report,null,2));
   console.log(JSON.stringify(report));await w.happyDOM.close();
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
