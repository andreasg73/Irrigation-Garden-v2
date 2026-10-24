"""Actual original HA scripts/automations; virtual outputs only; no real HA access."""
import asyncio,json,logging,hashlib,tempfile,time
from pathlib import Path
from datetime import datetime,timezone
from runtime_fixture import create_hass,ROOT
from network_fixture import sandbox_network

async def main():
    hass,calls=await create_hass(Path(tempfile.mkdtemp(prefix='kloggy-runtime-')))
    results=[];cleanup_transitions=[]
    def observe_cleanup(event):
        if event.data['entity_id']=='input_boolean.irrigation_cycle3_running' and event.data.get('new_state') and event.data['new_state'].state=='off':
            cleanup_transitions.append({e:hass.states.get(e).state if hass.states.get(e) else None for e in ['script.irrigation_cancel_irrigation','input_boolean.irrigation_stop_in_progress','input_text.irrigation_active_switch']})
    hass.bus.async_listen('state_changed',observe_cleanup)
    async def check(name,truth,detail=None):
        results.append({'id':name,'passed':bool(truth),'detail':detail})
        print(json.dumps(results[-1]),flush=True)
        if not truth:raise AssertionError(name+': '+str(detail))
    def state(e):return hass.states.get(e).state if hass.states.get(e) else None
    async def svc(d,s,**data):
        await hass.services.async_call(d,s,data,blocking=True)
    async def until(pred,timeout=10):
        async with asyncio.timeout(timeout):
            while not pred(): await asyncio.sleep(.025)
    async def settle():
        # Pending Script waits must not block the harness.
        await asyncio.sleep(.08)
    async def boolean(name,value):await svc('input_boolean','turn_on' if value else 'turn_off',entity_id='input_boolean.irrigation_'+name)
    async def number(name,value):await svc('input_number','set_value',entity_id='input_number.irrigation_'+name,value=value)
    async def text(name,value):await svc('input_text','set_value',entity_id='input_text.irrigation_'+name,value=value)
    async def start(c):await boolean(f'cycle{c}_running',True)
    async def cancel(**kw):
        await until(lambda:state('input_boolean.irrigation_stop_in_progress')=='off')
        await svc('script','irrigation_cancel_irrigation',**kw);await settle()
        await until(lambda:state('input_boolean.irrigation_stop_in_progress')=='off')
    async def idle():await until(lambda:state('script.irrigation_run_a_cycle')=='off' and all(state(f'input_boolean.irrigation_cycle{c}_running')=='off' for c in range(1,4)) and state('script.irrigation_cancel_irrigation')=='off' and state('input_boolean.irrigation_stop_in_progress')=='off',30)
    def outputs_off():return all(state(f'switch.kloggy_fixture_zone{n}')=='off' for n in range(1,17))
    try:
        await check('startup.safe',outputs_off() and not calls and state('input_boolean.irrigation_master_control_switch')=='off')
        await boolean('master_control_switch',True);await settle()
        await check('startup.cycle_names',all(state(f'input_text.irrigation_cycle{c}_name') in [f'Cycle{c}','Manual Cycle'] for c in range(1,4)),[state(f'input_text.irrigation_cycle{c}_name') for c in range(1,4)])
        await number('number_of_zones',16)
        await boolean('testing_mode',True)
        # Test-only fixture acceleration of original pause helper; no source rewrite.
        old=hass.states.get('input_number.irrigation_pause_between_zones_in_seconds')
        hass.states.async_set(old.entity_id,'0',dict(old.attributes))
        for n in range(1,17):
            await text(f'zone{n}_switch_entity_id',f'switch.kloggy_fixture_zone{n}')
            for c in range(1,4):
                await number(f'cycle{c}_zone{n}_duration',1)
                if c<3:await boolean(f'cycle{c}_zone{n}_every_day',True)
        await boolean('disable_switches',False);await settle()
        for c in range(1,4):
            first=len(calls);await start(c)
            await until(lambda:state('script.irrigation_run_a_cycle')=='on')
            await idle()
            expected=[[s,f'switch.kloggy_fixture_zone{n}'] for n in range(1,17) for s in ['turn_on','turn_off']]
            await check(f'cycle{c}.zones1-16.sequence',calls[first:]==expected,{'actual':calls[first:]})
            await check(f'cycle{c}.cleanup',outputs_off() and state('input_text.irrigation_active_switch')=='' and all(state(f'timer.irrigation_zone{n}_timer')=='idle' for n in range(1,17)))
        # CANCEL at each zone boundary with all previous settings preserved.
        for arg in ['', 'zone0','zone17','bad',None]:
            first=len(calls);await boolean('disable_switches',True)
            await svc('timer','start',entity_id='timer.irrigation_zone16_timer',duration=30)
            await cancel(cycle='nonsense',zone=arg)
            await check('cancel.invalid.'+repr(arg),state('timer.irrigation_zone16_timer')=='idle' and len(calls)==first)
        # Dry run through active worker and cancel: zero ON and zero OFF calls.
        first=len(calls);await start(3)
        await until(lambda:state('timer.irrigation_zone1_timer')=='active')
        await cancel();await idle()
        await check('dryrun.no_switch_actions',len(calls)==first)
        # Remapping a running zone must still close the original output.
        await boolean('disable_switches',False);await number('cycle3_zone1_duration',20);await settle();await start(3)
        await until(lambda:state('switch.kloggy_fixture_zone1')=='on')
        await text('zone1_switch_entity_id','switch.kloggy_fixture_zone16');await cancel(zone='')
        await check('cancel.remap_snapshot',outputs_off() and state('script.irrigation_run_a_cycle')=='off')
        await text('zone1_switch_entity_id','switch.kloggy_fixture_zone1')
        # Master OFF while active: no later ON; schedules remain off.
        await boolean('cycle1_schedule_enabled',True);await boolean('cycle2_schedule_enabled',True)
        await start(3);await until(lambda:state('switch.kloggy_fixture_zone1')=='on')
        await boolean('master_control_switch',False);await idle();await settle()
        after=len(calls);await asyncio.sleep(1.2)
        await check('master_off.stops_worker',outputs_off() and not any(s=='turn_on' for s,e in calls[after:]) and all(state(f'input_boolean.irrigation_cycle{c}_schedule_enabled')=='off' for c in [1,2]))
        # Manual zone uses original cycle3; cancel restores ALL 16 durations.
        await boolean('master_control_switch',True);await settle()
        saved=[(n%5)+1 for n in range(1,17)]
        for n,v in enumerate(saved,1):await number(f'cycle3_zone{n}_duration',v)
        await boolean('cycle1_schedule_enabled',True);await boolean('cycle2_schedule_enabled',False)
        await settle();first=len(calls)
        await svc('script','turn_on',entity_id='script.irrigation_run_a_single_zone_on_demand',variables={'zone':'zone16'})
        await until(lambda:state('switch.kloggy_fixture_zone16')=='on')
        await check('manual.zone16.only',[(s,e) for s,e in calls[first:] if s=='turn_on']==[('turn_on','switch.kloggy_fixture_zone16')])
        await boolean('master_control_switch',False);await idle();await settle()
        await check('manual.master_off_restores',all(float(state(f'input_number.irrigation_cycle3_zone{n}_duration'))==v for n,v in enumerate(saved,1)) and state('input_text.irrigation_single_zone_backup')=='' and all(state(f'input_boolean.irrigation_cycle{c}_schedule_enabled')=='off' for c in [1,2]))
        # Worker failure represented by legitimate script.turn_off: watchdog must close.
        await boolean('master_control_switch',True);await settle();await number('cycle3_zone1_duration',20);await settle();await start(3)
        await until(lambda:state('switch.kloggy_fixture_zone1')=='on')
        await svc('script','turn_off',entity_id='script.irrigation_run_a_cycle')
        await until(outputs_off,8);await idle()
        await check('watchdog.worker_stopped',outputs_off() and state('input_text.irrigation_active_switch')=='')
    except Exception as e:
        results.append({'id':'unhandled','passed':False,'detail':repr(e)})
        print('FAILED',repr(e),flush=True)
    finally:
        await cancel()
        manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT).rglob('*.yaml')}
        report={'ha_version':'2026.10.2','layer':'actual local HA integrations and original YAML scripts; virtual switch services; zero hardware/production access','fixture_pause_override_seconds':0,'results':results,'switch_calls':calls,'cleanup_transitions':cleanup_transitions,'source_sha256':manifest}
        (ROOT/'tests/runtime_results.json').write_text(json.dumps(report,indent=2))
        await hass.async_stop()
    if any(not r['passed'] for r in results):raise SystemExit(1)

if __name__=='__main__':
    logging.basicConfig(level=logging.WARNING)
    with sandbox_network():asyncio.run(main())
