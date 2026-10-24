"""Real HA shutdown jobs against candidate YAML; only virtual switch services."""
import asyncio, hashlib, json, logging, tempfile, time
from pathlib import Path
from homeassistant.const import EVENT_STATE_CHANGED
from runtime_fixture import ROOT, create_hass
from network_fixture import sandbox_network

CASES = ['cycle1', 'cycle2', 'cycle3', 'manual16', 'dryrun', 'dryrun_midrun', 'off_unacknowledged', 'cancel_inflight', 'master_off_inflight', 'master_off_queue_full']

async def run_case(name):
    faults = {}
    hass, calls = await create_hass(Path(tempfile.mkdtemp(prefix='kloggy-shutdown-')), faults=faults)
    results, timeline = [], []
    def state(entity):
        value = hass.states.get(entity)
        return value.state if value else None
    async def wait(predicate):
        async with asyncio.timeout(10):
            while not predicate(): await asyncio.sleep(.025)
    async def service(domain, action, **data):
        await hass.services.async_call(domain, action, data, blocking=True)
    async def boolean(name, on):
        await service('input_boolean', 'turn_on' if on else 'turn_off', entity_id='input_boolean.irrigation_'+name)
    async def number(name, value):
        await service('input_number', 'set_value', entity_id='input_number.irrigation_'+name, value=value)
    async def text(name, value):
        await service('input_text', 'set_value', entity_id='input_text.irrigation_'+name, value=value)
    def event(ev):
        entity = ev.data['entity_id']
        if entity.startswith(('switch.', 'script.irrigation_', 'timer.irrigation_', 'input_boolean.irrigation_master', 'input_boolean.irrigation_stop')):
            value = ev.data['new_state']
            timeline.append({'seconds':round(time.monotonic()-started,6), 'entity':entity, 'state':value.state if value else None})
    def check(suffix, passed, detail=None):
        results.append({'id':f'shutdown.{name}.{suffix}', 'passed':bool(passed), 'detail':detail})
        print(json.dumps(results[-1]), flush=True)
    started = time.monotonic()
    hass.bus.async_listen(EVENT_STATE_CHANGED, event)
    try:
        await boolean('master_control_switch', True)
        await asyncio.sleep(.15)
        await boolean('testing_mode', True)
        await boolean('disable_switches', name=='dryrun')
        await number('number_of_zones',16)
        for zone in range(1,17):
            await text(f'zone{zone}_switch_entity_id',f'switch.kloggy_fixture_zone{zone}')
        cycle = int(name[-1]) if name.startswith('cycle') else 3
        saved = [20+zone for zone in range(1,17)]
        for zone in range(1,17):
            await number(f'cycle{cycle}_zone{zone}_duration', saved[zone-1] if name=='manual16' else (60 if zone in [1,2] else 0))
            if cycle<3: await boolean(f'cycle{cycle}_zone{zone}_every_day',True)
        await boolean('cycle1_schedule_enabled',True)
        await boolean('cycle2_schedule_enabled',True)
        await asyncio.sleep(.1)
        if name=='manual16':
            await service('script','turn_on',entity_id='script.irrigation_run_a_single_zone_on_demand',variables={'zone':'zone16'})
        else:
            await boolean(f'cycle{cycle}_running',True)
        zone=16 if name=='manual16' else 1
        output=f'switch.kloggy_fixture_zone{zone}'
        await wait(lambda:state(f'timer.irrigation_zone{zone}_timer')=='active')
        check('active_before_stop', state('script.irrigation_run_a_cycle')=='on' and (name=='dryrun' or state(output)=='on'))
        if name=='dryrun_midrun': await boolean('disable_switches',True)
        if name=='off_unacknowledged': faults[('turn_off',output)]='ignore'
        gate_task=None
        if name in ['cancel_inflight','master_off_inflight','master_off_queue_full']:
            entered, release = asyncio.Event(), asyncio.Event()
            async def slow_off(call):
                ids=call.data.get('entity_id',[])
                if isinstance(ids,str): ids=[ids]
                if not ids or any(e not in {f'switch.kloggy_fixture_zone{n}' for n in range(1,17)} for e in ids):
                    raise RuntimeError('Containment rejected target '+repr(ids))
                for eid in ids:
                    calls.append(['turn_off',eid])
                    if not entered.is_set():
                        entered.set()
                        await release.wait()
                    hass.states.async_set(eid,'off')
            hass.services.async_register('switch','turn_off',slow_off)
            if name=='cancel_inflight':
                await service('script','turn_on',entity_id='script.irrigation_cancel_irrigation')
            else:
                await boolean('master_control_switch',False)
            await wait(entered.is_set)
            if name=='master_off_queue_full':
                for repeat in range(2):
                    await boolean('master_control_switch',True)
                    await asyncio.sleep(.05)
                    await boolean('master_control_switch',False)
                    await asyncio.sleep(.05)
            async def release_later():
                await asyncio.sleep(.5)
                release.set()
            gate_task=asyncio.create_task(release_later())
        first=len(calls); stopping=time.monotonic()
        await hass.async_stop()
        elapsed=time.monotonic()-stopping
        check('bounded_stop', elapsed<20, elapsed)
        should_remain_on=name in ['dryrun_midrun','off_unacknowledged']
        check('output_state',state(output)==('on' if should_remain_on else 'off'), {'state':state(output),'calls':calls[first:]})
        check('no_late_start',not any(action=='turn_on' for action,entity in calls[first:]))
        check('master_schedules_off', all(state('input_boolean.irrigation_'+suffix)=='off' for suffix in ['master_control_switch','cycle1_schedule_enabled','cycle2_schedule_enabled']))
        check('worker_timers_flags_cleared',state('script.irrigation_run_a_cycle')=='off' and state('script.irrigation_run_a_single_zone_on_demand')=='off' and all(state(f'timer.irrigation_zone{n}_timer')=='idle' for n in range(1,17)) and all(state(f'input_boolean.irrigation_cycle{c}_running')=='off' for c in [1,2,3]) and state('input_boolean.irrigation_stop_in_progress')=='off')
        check('captured_output',state('input_text.irrigation_active_switch')==(output if should_remain_on else ''),state('input_text.irrigation_active_switch'))
        if name.startswith('dryrun'):
            check('zero_switch_calls_during_stop',calls[first:]==[],calls[first:])
        if name=='manual16':
            check('settings_restored',state('input_text.irrigation_single_zone_backup')=='' and all(float(state(f'input_number.irrigation_cycle3_zone{z}_duration'))==saved[z-1] for z in range(1,17)))
        if name=='off_unacknowledged':
            check('off_attempted', ['turn_off',output] in calls[first:])
        # State-change ordering is independent of the call list.
        off_events=[i for i,e in enumerate(timeline) if e['entity']==output and e['state']=='off']
        worker_off=[i for i,e in enumerate(timeline) if e['entity']=='script.irrigation_run_a_cycle' and e['state']=='off']
        if not should_remain_on and name!='dryrun':
            check('worker_stopped_before_output_closed', bool(off_events and worker_off and worker_off[-1]<off_events[-1]))
        if gate_task: await gate_task
    except Exception as exc:
        check('unhandled',False,repr(exc))
        await hass.async_stop()
    return {'case':name,'results':results,'switch_calls':calls,'timeline':timeline}

async def main():
    report={'ha_version':'2026.10.2','layer':'actual async_stop and native shutdown trigger; virtual switches only','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT).rglob('*.yaml')},'cases':[]}
    for case in CASES:
        report['cases'].append(await run_case(case))
        report['results']=[r for c in report['cases'] for r in c['results']]
        (ROOT/'tests/shutdown_results.json').write_text(json.dumps(report,indent=2))
    if any(not r['passed'] for r in report['results']): raise SystemExit(1)

if __name__=='__main__':
    logging.basicConfig(level=logging.WARNING)
    with sandbox_network(): asyncio.run(main())
