"""Isolated HA core startup; no HTTP, MQTT, shell or device integration loaded."""
import asyncio,json,logging
from network_fixture import sandbox_network
from pathlib import Path
import yaml
from homeassistant.core import HomeAssistant
from homeassistant import loader,bootstrap,config_entries
from homeassistant.setup import async_setup_component
from homeassistant.core_config import async_process_ha_core_config

ROOT=Path(__file__).resolve().parents[1]
async def create_hass(root_override=None, faults=None, output_states=None, history=False):
    root=root_override or ROOT/'tests/local-ha-minimal'
    root.mkdir(parents=True,exist_ok=True)
    hass=HomeAssistant(str(root))
    loader.async_setup(hass)
    config={'homeassistant':{'name':'Kloggy Offline Test','time_zone':'Europe/Warsaw','country':'PL','latitude':52.0,'longitude':19.0,'unit_system':'metric'}}
    allow={'input_boolean','input_text','input_number','input_datetime','input_select','script','automation','template','timer','group'}
    for p in sorted((ROOT/'Garden Irrigation').glob('*.yaml')):
        if p.name in ['irrigation_logging_remote.yaml']:
            continue
        doc=yaml.safe_load(p.read_text())
        for k,v in doc.items():
            if k not in allow:continue
            if p.name=='irrigation_remote_control.yaml' and k=='automation':continue
            if v is None:config.setdefault(k,{})
            elif isinstance(v,list):config.setdefault(k,[]).extend(v)
            else:config.setdefault(k,{}).update(v)
    config.setdefault('input_boolean',{})['logging_irrigation']={'initial':False}
    if history:
        config['recorder']={'db_url':'sqlite:///'+str(root/'history.db'),'commit_interval':0,'include':{'entity_globs':['binary_sensor.irrigation_zone*_activity','sensor.irrigation_sensor_*'],'entities':['sensor.night_or_day']}}
        config['sensor']=yaml.safe_load((ROOT/'Garden Irrigation/irrigation_globals_zones.yaml').read_text())['sensor']
    # Restrict all valve actions to virtual outputs at the service boundary.
    calls=[]
    faults=faults if faults is not None else {}
    output_states=output_states or {}
    async def switch(call):
        ids=call.data.get('entity_id',[])
        if isinstance(ids,str):ids=[ids]
        if not ids or any(e not in {f'switch.kloggy_fixture_zone{n}' for n in range(1,17)} for e in ids):
            raise RuntimeError('Containment rejected switch target '+repr(ids))
        for eid in ids:
            calls.append([call.service,eid])
            mode=faults.get((call.service,eid))
            if mode=='raise':raise RuntimeError('Injected virtual output failure')
            if mode=='ignore':continue
            hass.states.async_set(eid,'on' if call.service=='turn_on' else 'off')
    hass.services.async_register('switch','turn_on',switch)
    hass.services.async_register('switch','turn_off',switch)
    for n in range(1,17):
        eid=f'switch.kloggy_fixture_zone{n}'
        hass.states.async_set(eid,output_states.get(eid,'off'))
    hass.config_entries = config_entries.ConfigEntries(hass,config)
    await loader.async_get_custom_components(hass)
    await bootstrap.async_load_base_functionality(hass)
    await async_process_ha_core_config(hass,config['homeassistant'])
    result=[]
    if history:
        from homeassistant.helpers import recorder
        recorder.async_initialize_recorder(hass)
        result.append(('recorder',await async_setup_component(hass,'recorder',config)))
    for domain in ['homeassistant','persistent_notification','input_boolean','input_text','input_number','input_datetime','input_select','timer','group','script','template','automation']:
        result.append((domain,await async_setup_component(hass,domain,config)))
    if history:result.append(('sensor',await async_setup_component(hass,'sensor',config)))
    print('COMPONENTS',result,flush=True)
    print('BOOT',bool(result),flush=True)
    await hass.async_start()
    await hass.async_block_till_done()
    print('STATES',len(hass.states.async_all()),flush=True)
    print('SCRIPT',hass.states.get('script.irrigation_run_a_cycle'),flush=True)
    return hass,calls

async def main():
    hass,calls = await create_hass()
    report={'states':{s.entity_id:{'state':s.state,'attributes':dict(s.attributes)} for s in hass.states.async_all()},'switch_calls':calls}
    (ROOT/'tests/boot_probe_results.json').write_text(json.dumps(report,default=str,indent=2))
    await hass.async_stop()
    print('STOPPED',flush=True)

if __name__=='__main__':
    logging.basicConfig(level=logging.WARNING)
    with sandbox_network():
        asyncio.run(main())
