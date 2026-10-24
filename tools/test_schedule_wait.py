"""Natural HA time triggers and independent wait/abort oracles; virtual entities only."""
import asyncio,json,tempfile,logging,hashlib
from pathlib import Path
from datetime import timedelta
from homeassistant.util import dt as dt_util
from runtime_fixture import create_hass,ROOT
async def main():
 h,calls=await create_hass(Path(tempfile.mkdtemp(prefix='kloggy-wait-')));results=[];starts=[]
 def st(e):return h.states.get(e).state if h.states.get(e) else None
 def changed(e):
  s=e.data.get('new_state')
  if s and s.entity_id in ['input_boolean.irrigation_cycle1_running','input_boolean.irrigation_cycle2_running'] and s.state=='on':starts.append(s.entity_id)
 un=h.bus.async_listen('state_changed',changed)
 async def wait(pred,seconds=8):
  async with asyncio.timeout(seconds):
   while not pred():await asyncio.sleep(.025)
 async def svc(d,s,**data):await h.services.async_call(d,s,data,blocking=True)
 async def boolean(n,v):await svc('input_boolean','turn_on' if v else 'turn_off',entity_id='input_boolean.irrigation_'+n)
 async def number(n,v):await svc('input_number','set_value',entity_id='input_number.irrigation_'+n,value=v)
 async def text(n,v):await svc('input_text','set_value',entity_id='input_text.irrigation_'+n,value=v)
 def ck(id,truth,detail=None):results.append({'id':id,'passed':bool(truth),'detail':detail});print(json.dumps(results[-1]),flush=True)
 def busy():return (h.states.get('automation.irrigation_triggered').attributes.get('current',0))>0
 async def quiet():await wait(lambda:not busy() and st('script.irrigation_run_a_cycle')=='off' and st('input_boolean.irrigation_stop_in_progress')=='off')
 try:
  await boolean('master_control_switch',True);await h.async_block_till_done()
  await boolean('testing_mode',True);await boolean('disable_switches',True);await number('number_of_zones',1)
  await text('zone1_switch_entity_id','switch.kloggy_fixture_zone1');await text('external_sensor_raining_now','binary_sensor.fixture_raining')
  for c in [1,2]:
   await number(f'cycle{c}_zone1_duration',10);await boolean(f'cycle{c}_zone1_every_day',True);await boolean(f'cycle{c}_wait_for_entity',True)
   await text(f'cycle{c}_wait_for_entity_name','binary_sensor.fixture_ready');await text(f'cycle{c}_wait_for_entity_state','not in on, open')
   for case in ['release','disabled','rain','timeout_abort','timeout_continue','unknown_policy','master_off']:
    await quiet();await boolean('master_control_switch',True);await h.async_block_till_done()
    await boolean(f'cycle{c}_schedule_enabled',True);await boolean('ignore_schedule_if_raining',case=='rain')
    await boolean(f'cycle{c}_wait_for_entity_name_timeout_continue',case=='timeout_continue')
    await number(f'cycle{c}_wait_for_entity_name_timeout_duration',1 if case.startswith('timeout') or case=='unknown_policy' else 5)
    h.states.async_set('binary_sensor.fixture_ready','unavailable');h.states.async_set('binary_sensor.fixture_raining','off')
    first=len(starts);when=dt_util.now()+timedelta(seconds=2)
    await svc('input_datetime','set_datetime',entity_id=f'input_datetime.irrigation_cycle{c}_start_time',time=when.strftime('%H:%M:%S'))
    await wait(busy)
    if case=='disabled':await boolean(f'cycle{c}_schedule_enabled',False)
    if case=='rain':h.states.async_set('binary_sensor.fixture_raining','on')
    if case=='unknown_policy':h.states.async_set(f'input_boolean.irrigation_cycle{c}_wait_for_entity_name_timeout_continue','unavailable')
    if case=='master_off':await boolean('master_control_switch',False)
    if case in ['release','disabled','rain','master_off']:
     await asyncio.sleep(.15)
     if case=='release':ck(f'c{c}.unknown_does_not_release',len(starts)==first)
     h.states.async_set('binary_sensor.fixture_ready','off')
    if case in ['release','timeout_continue']:
     await wait(lambda:len(starts)>first)
     ck(f'c{c}.{case}',starts[first:]==[f'input_boolean.irrigation_cycle{c}_running'])
    else:
     await wait(lambda:not busy());await asyncio.sleep(.25)
     ck(f'c{c}.{case}.no_start',starts[first:]==[],starts[first:])
    await svc('script','irrigation_cancel_irrigation');await quiet();await boolean(f'cycle{c}_schedule_enabled',False)
  ck('wait.no_switch_calls',calls==[],calls)
 finally:
  un();await h.async_stop()
 report={'layer':'Native HA natural wall-clock time triggers, wait_template and original worker; dry run virtual sources','results':results,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT).rglob('*.yaml')}}
 (ROOT/'tests/schedule_wait_results.json').write_text(json.dumps(report,indent=2));assert all(x['passed'] for x in results)
logging.basicConfig(level=logging.ERROR);asyncio.run(main())
