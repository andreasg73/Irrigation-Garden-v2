"""Failure, scheduling and restart evidence using original HA components."""
import asyncio,json,logging,tempfile,hashlib
from pathlib import Path
from datetime import timedelta
from homeassistant.util import dt as dt_util
from runtime_fixture import create_hass,ROOT

async def main():
    root=Path(tempfile.mkdtemp(prefix='kloggy-restart-'));faults={}
    hass,calls=await create_hass(root,faults=faults)
    results=[];all_calls=[]
    def st(e):return hass.states.get(e).state if hass.states.get(e) else None
    async def wait(pred,seconds=12):
        async with asyncio.timeout(seconds):
            while not pred():await asyncio.sleep(.025)
    async def svc(d,s,**data):await hass.services.async_call(d,s,data,blocking=True)
    async def boolean(n,v):await svc('input_boolean','turn_on' if v else 'turn_off',entity_id='input_boolean.irrigation_'+n)
    async def number(n,v):await svc('input_number','set_value',entity_id='input_number.irrigation_'+n,value=v)
    async def text(n,v):await svc('input_text','set_value',entity_id='input_text.irrigation_'+n,value=v)
    async def check(id,truth,detail=None):
        r={'id':id,'passed':bool(truth),'detail':detail};results.append(r);print(json.dumps(r),flush=True)
        if not truth:raise AssertionError(id)
    def quiet():return st('script.irrigation_run_a_cycle')=='off' and st('input_boolean.irrigation_stop_in_progress')=='off' and all(st(f'input_boolean.irrigation_cycle{c}_running')=='off' for c in [1,2,3])
    async def ready():await wait(quiet);await boolean('master_control_switch',True);await asyncio.sleep(.1)
    async def start():await boolean('cycle3_running',True)
    try:
        await ready();await boolean('testing_mode',True);await boolean('disable_switches',False);await number('number_of_zones',2)
        for n in [1,2]:
            await text(f'zone{n}_switch_entity_id',f'switch.kloggy_fixture_zone{n}')
            await number(f'cycle3_zone{n}_duration',1)
        await asyncio.sleep(.1)
        first=len(calls);faults[('turn_on','switch.kloggy_fixture_zone1')]='ignore';await start()
        await wait(lambda:st('input_boolean.irrigation_master_control_switch')=='off');await wait(quiet)
        await check('fault.no_on_ack',not any(s=='turn_on' and e.endswith('zone2') for s,e in calls[first:]) and st('switch.kloggy_fixture_zone1')=='off')
        faults.clear();await ready();faults[('turn_off','switch.kloggy_fixture_zone1')]='ignore';first=len(calls);await start()
        await wait(lambda:st('input_boolean.irrigation_master_control_switch')=='off');await wait(quiet)
        await check('fault.no_off_ack_blocks_next',st('switch.kloggy_fixture_zone1')=='on' and st('input_text.irrigation_active_switch')=='switch.kloggy_fixture_zone1' and not any(s=='turn_on' and e.endswith('zone2') for s,e in calls[first:]))
        faults.clear();await wait(lambda:st('switch.kloggy_fixture_zone1')=='off',8);await wait(quiet)
        await check('fault.off_retry_recovers',st('input_text.irrigation_active_switch')=='')
        # Changing mode mid-run must suppress OFF too, retain unresolved output, then retry.
        await ready();await number('cycle3_zone1_duration',20);await asyncio.sleep(.1);await start()
        await wait(lambda:st('switch.kloggy_fixture_zone1')=='on');await boolean('disable_switches',True);first=len(calls)
        await svc('script','irrigation_cancel_irrigation');await wait(quiet)
        await check('dryrun.midrun_no_off',calls[first:]==[] and st('input_text.irrigation_active_switch')=='switch.kloggy_fixture_zone1')
        await boolean('disable_switches',False);await wait(lambda:st('switch.kloggy_fixture_zone1')=='off',8);await wait(quiet)
        # Native clock/time triggers for BOTH automatic cycles, without automation.trigger.
        await number('number_of_zones',1)
        for c in [1,2]:
            await number(f'cycle{c}_zone1_duration',1);await boolean(f'cycle{c}_zone1_every_day',True)
            await boolean(f'cycle{c}_schedule_enabled',True)
            first=len(calls);when=dt_util.now()+timedelta(seconds=2)
            await svc('input_datetime','set_datetime',entity_id=f'input_datetime.irrigation_cycle{c}_start_time',time=when.strftime('%H:%M:%S'))
            await wait(lambda:any(s=='turn_on' for s,e in calls[first:]),8);await wait(quiet)
            await check(f'schedule.cycle{c}.native_time',[[s,e] for s,e in calls[first:] if s=='turn_on']==[['turn_on','switch.kloggy_fixture_zone1']])
            await boolean(f'cycle{c}_schedule_enabled',False)
        # Synthetic weather through real dynamically configured source sensors.
        await text('external_sensor_rainfall_today','sensor.fixture_rain');hass.states.async_set('sensor.fixture_rain','5',{'unit_of_measurement':'mm'})
        await number('rainfall_threshold',10);await number('days_of_rainfall_history_used',0)
        await wait(lambda:st('input_number.irrigation_rainfall_multiplier')=='0.5')
        hass.states.async_set('sensor.fixture_rain','unavailable');await asyncio.sleep(.2)
        await check('weather.rain_missing_preserves',st('input_number.irrigation_rainfall_multiplier')=='0.5' and st('sensor.irrigation_sensor_rainfall_today')=='unavailable')
        hass.states.async_set('sensor.fixture_rain','-4');await asyncio.sleep(.2)
        await check('weather.negative_rain_unavailable',st('sensor.irrigation_sensor_rainfall_today')=='unavailable' and st('input_number.irrigation_rainfall_multiplier')=='0.5')
        await text('external_sensor_current_temp','sensor.fixture_temperature');hass.states.async_set('sensor.fixture_temperature','-5',{'unit_of_measurement':'°C'})
        await wait(lambda:st('sensor.irrigation_sensor_current_temp')=='-5')
        await check('weather.negative_temperature_supported',st('sensor.irrigation_sensor_current_temp')=='-5')
        # Record manual settings, stop HA while actual original manual script waits.
        await number('number_of_zones',16)
        saved=[n+1 for n in range(1,17)]
        for n,v in enumerate(saved,1):await number(f'cycle3_zone{n}_duration',v)
        await text('zone16_switch_entity_id','switch.kloggy_fixture_zone16');await boolean('cycle1_schedule_enabled',True)
        await svc('script','turn_on',entity_id='script.irrigation_run_a_single_zone_on_demand',variables={'zone':'zone16'})
        await wait(lambda:st('switch.kloggy_fixture_zone16')=='on')
        await check('restart.snapshot_persisted_before_shutdown',st('input_text.irrigation_single_zone_backup').startswith('{'))
        all_calls.extend(calls);await hass.async_stop()
        # Second real HA lifecycle, same restore files; fixture output still ON.
        hass,calls=await create_hass(root,output_states={'switch.kloggy_fixture_zone16':'on'})
        await wait(quiet)
        await check('restart.master_off_and_output_closed',st('input_boolean.irrigation_master_control_switch')=='off' and st('switch.kloggy_fixture_zone16')=='off' and not any(s=='turn_on' for s,e in calls))
        await check('restart.manual_settings_restored',all(float(st(f'input_number.irrigation_cycle3_zone{n}_duration'))==v for n,v in enumerate(saved,1)) and st('input_text.irrigation_single_zone_backup')=='')
        await check('restart.schedules_remain_off',all(st(f'input_boolean.irrigation_cycle{c}_schedule_enabled')=='off' for c in [1,2]))
        await check('restart.output_mode_restored',st('input_boolean.irrigation_disable_switches')=='off')
    except Exception as e:
        results.append({'id':'unhandled','passed':False,'detail':repr(e)});print('FAILED',repr(e),flush=True)
    finally:
        all_calls.extend(calls)
        report={'ha_version':'2026.10.2','layer':'actual HA components, virtual switches; real graceful stop/start with restore-state files; simulated output persistence','results':results,'switch_calls':all_calls,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT).rglob('*.yaml')}}
        (ROOT/'tests/extended_results.json').write_text(json.dumps(report,indent=2))
        await hass.async_stop()
    if any(not r['passed'] for r in results):raise SystemExit(1)

if __name__=='__main__':
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())
