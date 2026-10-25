/* Journal behavior and text safety through the actual module; all transports blocked. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
(async()=>{
 const {Window}=await import(pathToFileURL(require.resolve('happy-dom')).href);
 const w=new Window({url:'https://journal-fixture.invalid',settings:{enableJavaScriptEvaluation:true,disableJavaScriptFileLoading:true,disableCSSFileLoading:true}});
 for(const n of ['fetch','WebSocket','XMLHttpRequest'])w[n]=()=>{throw Error('Network forbidden');};
 w.eval(fs.readFileSync(path.join(__dirname,'../custom_components/irrigation_garden/frontend/irrigation-garden-ui.js'),'utf8'));
 const dashboard=JSON.parse(fs.readFileSync(path.join(__dirname,'../dist/pl/irrigation_dashboard.json'),'utf8'));
 const config=dashboard.views[0].sections[0].cards.find(c=>c.type==='custom:irrigation-garden-decisions');assert.ok(config);
 const card=w.document.createElement('irrigation-garden-decisions');card.setConfig(config);w.document.body.append(card);
 const states={};const update=()=>card.hass={states:{...states},locale:{language:'pl'},config:{time_zone:'Europe/Warsaw'},callService(){throw Error('Write forbidden');}};
 const set=records=>{states['sensor.irrigation_last_decision']={state:'duration_selected',attributes:{records}};update();};
 const q=s=>card.shadowRoot.querySelector(s),contains=s=>assert.ok(card.shadowRoot.textContent.includes(s),s);
 update();contains('nie jest wczytany');set([]);contains('Nie zapisano');
 const base={reason:'duration_selected',cycle:'cycle1',zone:1,at:'2026-10-25T12:00:00Z',base:10,seconds:240,expected:240,rain:true,rain_factor:.5,temperature:true,temperature_factor:.8,minimum:1,maximum:3600,physical:true};
 set([base]);contains('10 min');contains('4 min');contains('Korekta opadów: ×0.5 (-50%)');contains('Korekta temperatury: ×0.8 (-20%)');
 set([base,{reason:'raining_now',cycle:'cycle2',at:base.at,rain_source:'binary_sensor.rain',rain_state:'on'}]);contains('czujnik zgłasza deszcz');assert.equal(q('details').hidden,false);
 q('details').open=true;set([base,{...base,reason:'rain_unknown'}]);assert.equal(q('details').open,true);contains('nie potwierdza');
 set([{...base,physical:false,testing:true,seconds:4,expected:4}]);contains('symulacja');contains('Tryb testowy');
 set([{...base,rain_factor:0,seconds:0,expected:0,reason:'rain_adjusted_zero'}]);contains('obniżyła czas do zera');
 set([{...base,minimum:300,seconds:300,expected:300}]);contains('minimalnego czasu: 5 min');
 set([{...base,maximum:120,seconds:120,expected:120}]);contains('maksymalnego czasu: 2 min');
 set([{...base,seconds:123}]);contains('nie można potwierdzić dokładnej przyczyny');
 set([{...base,cycle_name:'<img src=x onerror=alert(1)>',zone_name:'<script>bad()</script>'}]);assert.equal(card.shadowRoot.querySelectorAll('img,script').length,0);contains('<img');
 set([{...base,rain_factor:'unavailable'}]);contains('Brak mnożnika');
 set(Array.from({length:80},(_,i)=>({...base,zone:i%16+1,at:base.at})));assert.equal(card.shadowRoot.querySelectorAll('li').length,63);
 set([null,{},'bad',base]);contains('Wybrano czas');
 // Reading new weather or renaming live helpers must not change historical text.
 const before=q('.latest').textContent;states['input_number.irrigation_rainfall_multiplier']={state:'0'};update();assert.equal(q('.latest').textContent,before);
 card.remove();w.close();console.log(JSON.stringify({journal_dom:'passed',cases:15,writes:0,network_requests:0}));
})().catch(e=>{console.error(e);process.exitCode=1;});
