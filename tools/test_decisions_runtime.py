"""Native HA journal tests with contained virtual outputs; no production HA access."""
import asyncio
import json
import logging
import tempfile
from pathlib import Path

from runtime_fixture import create_hass, ROOT
from network_fixture import sandbox_network


async def main():
    root=Path(tempfile.mkdtemp(prefix='ig-decisions-'))
    hass, calls = await create_hass(root)
    checks = []
    emissions=[]
    hass.bus.async_listen('irrigation_decision',lambda event:emissions.append(dict(event.data)))
    def state(entity):
        s = hass.states.get(entity)
        return s.state if s else None
    def records():
        s = hass.states.get('sensor.irrigation_last_decision')
        return list(s.attributes.get('records', [])) if s else []
    def check(name, truth, detail=None):
        checks.append({'id': name, 'passed': bool(truth), 'detail': detail})
        print(json.dumps(checks[-1], default=str), flush=True)
        assert truth, (name, detail)
    async def svc(domain, service, **data):
        await hass.services.async_call(domain, service, data, blocking=True)
    async def boolean(suffix, value):
        await svc('input_boolean', 'turn_on' if value else 'turn_off', entity_id='input_boolean.irrigation_'+suffix)
    async def number(suffix, value):
        await svc('input_number', 'set_value', entity_id='input_number.irrigation_'+suffix, value=value)
    async def text(suffix, value):
        await svc('input_text', 'set_value', entity_id='input_text.irrigation_'+suffix, value=value)
    async def until(pred, timeout=20):
        async with asyncio.timeout(timeout):
            while not pred():
                await asyncio.sleep(.025)
    async def cycle(c):
        before=len(emissions)
        await boolean(f'cycle{c}_running', True)
        await until(lambda: state('script.irrigation_run_a_cycle')=='on')
        await until(lambda: state('script.irrigation_run_a_cycle')=='off', 35)
        await asyncio.sleep(.2)
        return emissions[before:]
    try:
        # Burst emissions must not lose records when all zones are skipped.
        for n in range(75):
            hass.bus.async_fire('irrigation_decision', {'reason':'duration_zero','cycle':'cycle1','zone':n % 16 + 1,'sequence':n})
        await hass.async_block_till_done()
        journal=records()
        check('journal.bounded-burst-order', len(journal)==64 and [r['sequence'] for r in journal]==list(range(11,75)), len(journal))
        await boolean('master_control_switch', True)
        await boolean('disable_switches', True)
        await boolean('testing_mode', True)
        await number('number_of_zones', 2)
        await number('weather_adjusted_minimum_duration_in_seconds', 3)
        await number('weather_adjusted_maximum_duration_in_minutes', 60)
        old=hass.states.get('input_number.irrigation_pause_between_zones_in_seconds')
        hass.states.async_set(old.entity_id,'0',dict(old.attributes))
        for c in (1,2,3):
            await number(f'cycle{c}_zone1_duration', 10)
            await number(f'cycle{c}_zone2_duration', 0)
            if c<3:
                await boolean(f'cycle{c}_zone1_every_day', True)
                await boolean(f'cycle{c}_adjust_for_rainfall', True)
                await boolean(f'cycle{c}_adjust_for_temperature', True)
        # Set final multipliers after enabling weather options; native option
        # automations have finished before this snapshot is exercised.
        await asyncio.sleep(.2)
        await number('rainfall_multiplier', .5)
        await number('temp_multiplier', .8)
        await asyncio.sleep(.3)
        entries=await cycle(1)
        selected=next(r for r in entries if r.get('zone')==1 and r.get('reason')=='duration_selected')
        check('weather.snapshot-factors-and-runtime', selected['seconds']==selected['expected']==4 and selected['rain_factor']==.5 and selected['temperature_factor']==.8, selected)
        check('zone.zero-explained', any(r['reason']=='duration_zero' and r['zone']==2 for r in entries))
        check('simulation.no-output-calls', not calls, calls)
        await number('rainfall_multiplier', 0)
        await asyncio.sleep(.2)
        entries=await cycle(1)
        check('rain.zero-explained', any(r['reason']=='rain_adjusted_zero' and r['zone']==1 for r in entries), entries)
        entries=await cycle(3)
        manual=next(r for r in entries if r.get('zone')==1)
        check('manual.ignores-weather', manual['seconds']==manual['expected']==10 and manual['rain'] is False and manual['temperature'] is False, manual)
        check('history.snapshot-not-recomputed', any(r.get('rain_factor')==.5 and r.get('seconds')==4 for r in records()))
        # Native scheduled trigger path: real timer trigger at the next second.
        await boolean('cycle1_schedule_enabled', True)
        await boolean('ignore_schedule_if_raining', True)
        await text('external_sensor_raining_now', 'binary_sensor.fixture_rain')
        async def scheduled_rain(value, expected):
            from datetime import timedelta
            from homeassistant.util import dt as dt_util
            hass.states.async_set('binary_sensor.fixture_rain',value)
            await svc('input_datetime','set_datetime',entity_id='input_datetime.irrigation_cycle1_start_time',time=(dt_util.now()+timedelta(seconds=2)).strftime('%H:%M:%S'))
            await until(lambda: records()[-1]['reason']==expected, 7)
            check('schedule.'+expected, state('script.irrigation_run_a_cycle')=='off')
        await scheduled_rain('on','raining_now')
        await scheduled_rain('unavailable','rain_unknown')
        check('all.diagnostics-never-actuate',not calls,calls)
        saved=records()
        await hass.async_stop()
        hass, calls=await create_hass(root)
        check('journal.restored-after-restart',records()==saved)
    finally:
        await hass.async_stop()
        (ROOT/'tests/decisions-results.json').write_text(json.dumps(checks,default=str,indent=2))


if __name__=='__main__':
    logging.basicConfig(level=logging.WARNING)
    with sandbox_network():
        asyncio.run(main())
