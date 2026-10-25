"""Create a self-contained UI fixture: no credentials, endpoints or physical targets."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from enhance_lovelace import UI_LABELS

out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
module=Path(os.environ.get('IG_UI_SOURCE', str(ROOT/'custom_components/irrigation_garden/frontend/irrigation-garden-ui.js'))).read_text()
labels={lang:{k:v[i] for k,v in UI_LABELS.items()} for lang,i in [('en',0),('pl',1)]}
html='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Irrigation Garden isolated UI fixture</title>
<style>body{font:16px system-ui;margin:16px;background:#eee;color:#17212b}hui-view{display:block;max-width:600px;margin:auto;padding:12px;background:var(--primary-background-color,#fff)}.controls{display:flex;flex-wrap:wrap;gap:8px;margin:10px}button,select{font:inherit;min-height:44px}#other{background:#fff;color:#17212b;padding:8px}pre{font-size:11px;white-space:pre-wrap;overflow-wrap:anywhere}irrigation-garden-entity-picker{margin-bottom:12px}</style>
<div id="other">Unrelated dashboard: unchanged</div><div class="controls"><label>Request behavior <select id="fault"><option value="none">Normal</option><option value="reject">Reject save</option><option value="delay">Delay save</option></select></label><button id="release">Release pending response</button><button id="update">Harmless HA update</button><button id="external">External mapping change</button><button id="active">Toggle watering fixture</button><button id="rename">Rename candidate fixture</button><button id="remount">Remount widgets</button><label>Fixture language <select id="language"><option value="pl">Polski</option><option value="en">English</option></select></label></div>
<hui-view id="view"></hui-view><h3>Mock requests</h3><pre id="requests">[]</pre><h3>Fixture status</h3><pre id="status"></pre>
<script>
'use strict';
// Every network transport is blocked. Only local mock input_text writes exist.
for(const name of ['fetch','WebSocket','EventSource','XMLHttpRequest','Worker','SharedWorker'])window[name]=function(){throw Error('Fixture containment blocked '+name);};
navigator.sendBeacon=()=>{throw Error('Fixture containment blocked beacon');};
const LABELS=__LABELS__;
const entity=(entity_id,state,name,attributes={})=>({entity_id,state,attributes:{friendly_name:name,...attributes}});
let states={
 'input_text.irrigation_zone1_switch_entity_id':entity('input_text.irrigation_zone1_switch_entity_id','switch.virtual_zone_1','Valve mapping'),
 'input_text.irrigation_external_sensor_current_temp':entity('input_text.irrigation_external_sensor_current_temp','sensor.virtual_outdoor','Temperature mapping'),
 'input_text.irrigation_external_sensor_raining_now':entity('input_text.irrigation_external_sensor_raining_now','','Rain mapping'),
 'script.irrigation_run_a_cycle':entity('script.irrigation_run_a_cycle','off','Virtual worker'),
 'switch.virtual_zone_1':entity('switch.virtual_zone_1','off','Garden front'),
 'switch.virtual_zone_2':entity('switch.virtual_zone_2','off','Garden rear'),
 'switch.virtual_zone_offline':entity('switch.virtual_zone_offline','unavailable','Offline garden'),
 'sensor.virtual_outdoor':entity('sensor.virtual_outdoor','15','Outdoor temperature',{unit_of_measurement:'°C'}),
 'sensor.virtual_celsius':entity('sensor.virtual_celsius','19','Greenhouse temperature',{unit_of_measurement:'°C'}),
 'sensor.virtual_fahrenheit':entity('sensor.virtual_fahrenheit','70','Wrong temperature unit',{unit_of_measurement:'°F'}),
 'sensor.virtual_humidity':entity('sensor.virtual_humidity','65','Humidity',{unit_of_measurement:'%'}),
 'binary_sensor.virtual_contact':entity('binary_sensor.virtual_contact','off','Aqara contact rain',{device_class:'opening'}),
 'sensor.virtual_hostile':entity('sensor.virtual_hostile','1','<img src=x onerror=alert(1)>',{unit_of_measurement:'°C'})
};
const calls=[];let pending=[];let widgets=[];let tick=0;
function update(){const h={states:{...states},themes:{darkMode:false},user:{id:'fixture-user'},callService:service};for(const w of widgets)w.hass=h;document.getElementById('status').textContent=JSON.stringify({mapping:states['input_text.irrigation_zone1_switch_entity_id'].state,temperature:states['input_text.irrigation_external_sensor_current_temp'].state,worker:states['script.irrigation_run_a_cycle'].state,pending:pending.length,tick},null,2);document.getElementById('requests').textContent=JSON.stringify(calls,null,2);}
async function service(domain,action,data){if(domain!=='input_text'||action!=='set_value'||!['input_text.irrigation_zone1_switch_entity_id','input_text.irrigation_external_sensor_current_temp','input_text.irrigation_external_sensor_raining_now'].includes(data.entity_id))throw Error('Fixture rejected unsupported request');calls.push({domain,action,data:{...data}});const behavior=document.getElementById('fault').value;update();if(behavior==='reject')throw Error('Controlled backend failure');if(behavior==='delay')await new Promise(resolve=>{pending.push(resolve);update();});states={...states,[data.entity_id]:{...states[data.entity_id],state:data.value}};update();}
window.loadCardHelpers=async()=>({createCardElement(config){const child=document.createElement('div');child.textContent='Original-card boundary fixture';child.style.cssText='padding:16px;background:var(--card-background-color);color:var(--primary-text-color)';child.getCardSize=()=>2;return child;}});
function mount(){const view=document.getElementById('view');view.replaceChildren();const ui_labels=LABELS[document.getElementById('language').value];widgets=[];for(const c of [{type:'irrigation-garden-appearance'},{type:'irrigation-garden-themed-card',card:{type:'markdown',content:'Original-card boundary fixture'}},{type:'irrigation-garden-entity-picker',entity:'input_text.irrigation_zone1_switch_entity_id',domains:['switch'],guard_watering:true,name:'Zawór strefy 1'},{type:'irrigation-garden-entity-picker',entity:'input_text.irrigation_external_sensor_current_temp',domains:['sensor'],units:['°C'],name:'Temperatura'},{type:'irrigation-garden-entity-picker',entity:'input_text.irrigation_external_sensor_raining_now',domains:['binary_sensor'],name:'Deszcz teraz'}]){const w=document.createElement(c.type);w.setConfig({...c,ui_labels});widgets.push(w);view.append(w);}update();}
document.getElementById('release').onclick=()=>{const p=pending;pending=[];p.forEach(resolve=>resolve());update();};
document.getElementById('update').onclick=()=>{tick++;states={...states};update();};
document.getElementById('external').onclick=()=>{states={...states,'input_text.irrigation_zone1_switch_entity_id':{...states['input_text.irrigation_zone1_switch_entity_id'],state:'switch.virtual_zone_offline'}};update();};
document.getElementById('active').onclick=()=>{const s=states['script.irrigation_run_a_cycle'];states={...states,[s.entity_id]:{...s,state:s.state==='off'?'on':'off'}};update();};
document.getElementById('rename').onclick=()=>{const s=states['switch.virtual_zone_2'];states={...states,[s.entity_id]:{...s,attributes:{friendly_name:'Renamed rear garden'}}};update();};
document.getElementById('remount').onclick=mount;document.getElementById('language').onchange=mount;
</script><script>__MODULE__</script><script>mount();</script>'''
html=html.replace('__LABELS__',json.dumps(labels,ensure_ascii=False)).replace('__MODULE__',module)
(out/'fixture.html').write_text(html)
print(out/'fixture.html')
