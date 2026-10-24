"""Native recorder + history_stats with original 32 stats and 16 proxy sensors."""
import asyncio,hashlib,json,logging,tempfile
from pathlib import Path
from runtime_fixture import create_hass,ROOT

async def main():
 hass,calls=await create_hass(Path(tempfile.mkdtemp(prefix='kloggy-history-')),history=True)
 results=[]
 def st(e):return hass.states.get(e).state if hass.states.get(e) else None
 async def svc(d,s,**data):await hass.services.async_call(d,s,data,blocking=True)
 async def wait(pred,t=15):
  async with asyncio.timeout(t):
   while not pred():await asyncio.sleep(.05)
 async def check(id,truth,detail=None):
  r={'id':id,'passed':bool(truth),'detail':detail};results.append(r);print(json.dumps(r),flush=True)
  if not truth:raise AssertionError(id)
 try:
  ids=[f'sensor.irrigation_zone{n}_total_time_{day}' for n in range(1,17) for day in ['today','yesterday']]
  await wait(lambda:all(st(e) not in [None,'unknown','unavailable'] for e in ids))
  await check('history.all32_entities',len(ids)==32)
  for n in range(1,17):
   await svc('input_text','set_value',entity_id=f'input_text.irrigation_zone{n}_switch_entity_id',value=f'switch.kloggy_fixture_zone{n}')
  await wait(lambda:all(st(f'binary_sensor.irrigation_zone{n}_activity')=='off' for n in range(1,17)))
  for n in range(1,17):hass.states.async_set(f'switch.kloggy_fixture_zone{n}','on')
  await wait(lambda:all(st(f'binary_sensor.irrigation_zone{n}_activity')=='on' for n in range(1,17)))
  await check('history.proxies16_follow_on',True)
  # Real time evidence, >=18 sec gives nonzero hours rounded to two decimals.
  await asyncio.sleep(20)
  for n in range(1,17):hass.states.async_set(f'switch.kloggy_fixture_zone{n}','off')
  await wait(lambda:all(st(f'binary_sensor.irrigation_zone{n}_activity')=='off' for n in range(1,17)))
  from homeassistant.components.recorder import get_instance
  recorder=get_instance(hass)
  await recorder.async_block_till_done()
  await svc('homeassistant','update_entity',entity_id=ids)
  await asyncio.sleep(.3)
  vals=[float(st(f'sensor.irrigation_zone{n}_total_time_today')) for n in range(1,17)]
  await check('history.native16_duration',all(.004 < v < .02 for v in vals),vals)
  await check('history.yesterday_zero',all(float(st(f'sensor.irrigation_zone{n}_total_time_yesterday'))==0 for n in range(1,17)))
  hass.states.async_set('switch.kloggy_fixture_zone16','unavailable')
  await wait(lambda:st('binary_sensor.irrigation_zone16_activity')=='unavailable')
  await check('history.unavailable_is_honest',True)
  # Re-mapping outside a run follows the new virtual output.
  await svc('input_text','set_value',entity_id='input_text.irrigation_zone16_switch_entity_id',value='switch.kloggy_fixture_zone1')
  hass.states.async_set('switch.kloggy_fixture_zone1','on');await wait(lambda:st('binary_sensor.irrigation_zone16_activity')=='on')
  await check('history.remap_dynamic',True)
 except Exception as e:
  results.append({'id':'unhandled','passed':False,'detail':repr(e)});print('FAILED',repr(e),flush=True)
 finally:
  (ROOT/'tests/history_results.json').write_text(json.dumps({'ha_version':'2026.10.2','layer':'native local recorder SQLite, history_stats and original templates; synthetic switches; actual 20s interval','results':results,'source_sha256':hashlib.sha256((ROOT/'Garden Irrigation/irrigation_globals_zones.yaml').read_bytes()).hexdigest()},indent=2))
  await hass.async_stop()
 if any(not r['passed'] for r in results):raise SystemExit(1)
if __name__=='__main__':
 logging.basicConfig(level=logging.WARNING)
 asyncio.run(main())
