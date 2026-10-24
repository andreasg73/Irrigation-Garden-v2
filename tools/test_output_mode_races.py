"""Native HA mode changes at service boundaries. All outputs are virtual."""
import asyncio,hashlib,json,logging,tempfile,time
from pathlib import Path
from runtime_fixture import ROOT,create_hass
from network_fixture import sandbox_network
CASES=[f'{p}.{m}' for p in ['cancel','before_on','before_off'] for m in ['on','unknown','unavailable','uninitialized']]

async def case(name):
 phase,mode=name.split('.');h,calls=await create_hass(Path(tempfile.mkdtemp(prefix='kloggy-mode-')))
 rows=[];seen=[];entered=asyncio.Event();release=asyncio.Event();original=None;boundary='setup'
 def state(e):
  s=h.states.get(e);return s.state if s else None
 async def svc(d,s,**data):await h.services.async_call(d,s,data,blocking=True)
 async def boolean(n,v):await svc('input_boolean','turn_on' if v else 'turn_off',entity_id='input_boolean.irrigation_'+n)
 async def text(n,v):await svc('input_text','set_value',entity_id='input_text.irrigation_'+n,value=v)
 async def wait(f,timeout=18):
  async with asyncio.timeout(timeout):
   while not f():await asyncio.sleep(.015)
 def check(suffix,ok,detail=None):
  row={'id':name+'.'+suffix,'passed':bool(ok),'detail':detail};rows.append(row);print(json.dumps(row),flush=True)
 async def output(call):
  ids=call.data.get('entity_id',[]);ids=[ids] if isinstance(ids,str) else ids
  assert ids and all(e in {f'switch.kloggy_fixture_zone{i}' for i in range(1,17)} for e in ids)
  for eid in ids:
   calls.append([call.service,eid]);seen.append({'action':call.service,'entity':eid,'disabled':state('input_boolean.irrigation_disable_switches'),'initialized':state('input_boolean.irrigation_output_mode_initialized'),'at':time.monotonic()})
   if phase=='cancel' and call.service=='turn_off' and not entered.is_set():entered.set();await release.wait()
   h.states.async_set(eid,'on' if call.service=='turn_on' else 'off')
   if phase=='before_off' and call.service=='turn_on':entered.set()
 try:
  await wait(lambda:state('input_boolean.irrigation_stop_in_progress')=='off')
  await boolean('master_control_switch',True);await boolean('testing_mode',True);await boolean('disable_switches',False)
  await svc('input_number','set_value',entity_id='input_number.irrigation_number_of_zones',value=16)
  for z in range(1,17):
   await text(f'zone{z}_switch_entity_id',f'switch.kloggy_fixture_zone{z}')
   await svc('input_number','set_value',entity_id=f'input_number.irrigation_cycle3_zone{z}_duration',value=1 if z==1 else 0)
  await h.async_block_till_done();await wait(lambda:float(state('sensor.irrigation_cycle3_zone1_actual_duration_in_seconds') or 0)==1)
  h.services.async_register('switch','turn_on',output);h.services.async_register('switch','turn_off',output)
  if phase=='cancel':
   h.states.async_set('switch.kloggy_fixture_zone16','on');await text('active_switch','switch.kloggy_fixture_zone16')
   await svc('script','turn_on',entity_id='script.irrigation_cancel_irrigation')
  else:
   if phase=='before_on':
    original=h.services.async_services()['input_text']['set_value']
    async def gate(call):
     await original.job.target(call)
     ids=call.data.get('entity_id',[]);ids=[ids] if isinstance(ids,str) else ids
     if 'input_text.irrigation_active_switch' in ids and call.data.get('value')=='switch.kloggy_fixture_zone1' and not entered.is_set():entered.set();await release.wait()
    h.services.async_register('input_text','set_value',gate,schema=original.schema,supports_response=original.supports_response)
   await boolean('cycle3_running',True)
  boundary='service_gate';await wait(entered.is_set);first=len(calls)
  if mode=='on':await boolean('disable_switches',True)
  elif mode=='uninitialized':await boolean('output_mode_initialized',False)
  else:
   old=h.states.get('input_boolean.irrigation_disable_switches');h.states.async_set(old.entity_id,mode,dict(old.attributes))
  release.set();boundary='cleanup'
  await wait(lambda:state('script.irrigation_run_a_cycle')=='off' and state('script.irrigation_cancel_irrigation')=='off' and state('input_boolean.irrigation_stop_in_progress')=='off')
  # Master OFF first stops the worker, then enters CANCEL asynchronously.
  # Worker OFF + CANCEL OFF can therefore be an intermediate state.
  intermediate={e:state(e) for e in ['script.irrigation_run_a_cycle','script.irrigation_cancel_irrigation','input_boolean.irrigation_stop_in_progress','timer.irrigation_zone1_timer']}
  await wait(lambda:all(state(f'timer.irrigation_zone{z}_timer')=='idle' for z in range(1,17)) and all(state(f'input_boolean.irrigation_cycle{c}_running')=='off' for c in [1,2,3]) and state('script.irrigation_cancel_irrigation')=='off' and state('input_boolean.irrigation_stop_in_progress')=='off')
  check('no_new_output_after_change',calls[first:]==[],{'later':calls[first:],'inflight_before_change':calls[:first]})
  check('service_guards',all(r['disabled']=='off' and r['initialized']=='on' for r in seen),seen)
  check('cleanup_completes',all(state(f'timer.irrigation_zone{z}_timer')=='idle' for z in range(1,17)),{'intermediate':intermediate})
  if phase in ['cancel','before_off']:
   eid='switch.kloggy_fixture_zone'+('16' if phase=='cancel' else '1');check('unclosed_output_retained',state(eid)=='on' and state('input_text.irrigation_active_switch')==eid)
  else:check('never_opened',not any(s=='turn_on' for s,e in calls) and state('switch.kloggy_fixture_zone1')=='off')
 except Exception as e:check('unhandled',False,{'error':repr(e),'boundary':boundary,'entered':entered.is_set()})
 finally:
  release.set()
  if original:h.services.async_register('input_text','set_value',original.job.target,schema=original.schema,supports_response=original.supports_response)
  await boolean('disable_switches',True);await h.async_stop()
 return {'case':name,'results':rows,'switch_calls':calls,'observations':seen}

async def main():
 report={'layer':'HA2026.10.2; virtual outputs; explicit helper/service-boundary injections','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['Garden Irrigation','Logging'] for p in (ROOT/folder).glob('*.yaml')},'cases':[]}
 for name in CASES:
  report['cases'].append(await case(name));report['results']=[r for c in report['cases'] for r in c['results']]
  (ROOT/'tests/output_mode_races_results.json').write_text(json.dumps(report,indent=2)+'\n')
 assert all(r['passed'] for r in report['results'])
if __name__=='__main__':
 logging.basicConfig(level=logging.WARNING)
 with sandbox_network():asyncio.run(main())
