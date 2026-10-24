"""Independent dated rainfall oracle on native HA, virtual sources and controlled calendar."""
import asyncio,json,tempfile,logging,hashlib
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch
from pathlib import Path
from runtime_fixture import create_hass,ROOT
async def main():
 root=Path(tempfile.mkdtemp(prefix='kloggy-rain-calendar-'));out=[]
 clock=[datetime(2026,11,1,12,tzinfo=ZoneInfo('Europe/Warsaw'))]
 with patch('homeassistant.util.dt.now',side_effect=lambda:clock[0]):
  h,calls=await create_hass(root)
  def st(e):return h.states.get(e).state if h.states.get(e) else None
  def ck(id,actual,expected):out.append({'id':id,'passed':actual==expected,'actual':actual,'expected':expected})
  async def settle():await h.async_block_till_done();await asyncio.sleep(.15)
  async def svc(d,s,**data):await h.services.async_call(d,s,data,blocking=True)
  async def number(n,v):await svc('input_number','set_value',entity_id='input_number.irrigation_'+n,value=v)
  async def rain(today,yesterday):
   for n,v in [('today',today),('yesterday',yesterday)]:h.states.async_set('sensor.fixture_rain_'+n,str(v),{'unit_of_measurement':'mm'},timestamp=clock[0].timestamp())
   await settle()
  async def tick():await svc('automation','trigger',entity_id='automation.irrigation_rainfall_nightly_update',skip_condition=False);await settle()
  try:
   await svc('input_boolean','turn_on',entity_id='input_boolean.irrigation_master_control_switch');await settle()
   for n in ['today','yesterday']:await svc('input_text','set_value',entity_id='input_text.irrigation_external_sensor_rainfall_'+n,value='sensor.fixture_rain_'+n)
   for n in range(1,5):await number('rainfall_percentage_'+str(n),100)
   await number('rainfall_threshold',20);await number('days_of_rainfall_history_used',1)
   await rain(1,5)
   ck('day1.multiplier',st('input_number.irrigation_rainfall_multiplier'),'0.7')
   clock[0]+=timedelta(days=1);await rain(2,3)
   await number('days_of_rainfall_history_used',2);await settle()
   ck('missed_midnight.two_days_ago',st('input_number.irrigation_rainfall_2'),'5.0')
   ck('missed_midnight.weighted_total',st('input_number.irrigation_rainfall_multiplier'),'0.5')
   before=[st('input_number.irrigation_rainfall_'+str(n)) for n in [2,3,4]]
   await tick();await tick()
   ck('same_day.idempotent',[st('input_number.irrigation_rainfall_'+str(n)) for n in [2,3,4]],before)
   await svc('input_boolean','turn_off',entity_id='input_boolean.irrigation_master_control_switch');await settle()
   clock[0]+=timedelta(days=1);await rain(1,120.5)
   ck('master_off.collects_history',st('input_number.irrigation_rainfall_2'),'3.0')
   await h.async_stop();h,new_calls=await create_hass(root);calls+=new_calls;await settle()
   clock[0]+=timedelta(days=1);await rain(4,0)
   ck('restart.master_off',st('input_boolean.irrigation_master_control_switch'),'off')
   ck('restart.retains_large_rain',st('input_number.irrigation_rainfall_2'),'120.5')
   ck('restart.threshold_stops',st('input_number.irrigation_rainfall_multiplier'),'0.0')
   clock[0]+=timedelta(days=2);await rain(1,2)
   await number('rainfall_multiplier',.65);await tick()
   ck('gap.retains_multiplier',st('input_number.irrigation_rainfall_multiplier'),'0.65')
   ck('gap.readiness_off',st('binary_sensor.irrigation_rainfall_data_ready'),'off')
   valid=h.states.get('binary_sensor.irrigation_rainfall_data_ready')
   ck('gap.missing_day_not_zero',valid.attributes.get('valid',{}).get('input_number.irrigation_rainfall_2') if valid else None,False)
   await number('days_of_rainfall_history_used',1);await settle()
   ck('gap.unneeded_day_ignored',st('input_number.irrigation_rainfall_multiplier'),'0.85')
   clock[0]+=timedelta(days=1);await tick()
   ck('stale_day.readiness_off',st('binary_sensor.irrigation_rainfall_data_ready'),'off')
   ck('stale_day.retains_multiplier',st('input_number.irrigation_rainfall_multiplier'),'0.85')
   await rain(1,2);await tick()
   ck('identical_fresh_report.recovers',st('binary_sensor.irrigation_rainfall_data_ready'),'on')
   ck('identical_fresh_report.multiplier',st('input_number.irrigation_rainfall_multiplier'),'0.85')
   before=st('input_text.irrigation_rainfall_daily_records')
   await rain(1,10001);await tick()
   ck('out_of_range.not_cached',st('input_text.irrigation_rainfall_daily_records'),before)
   ck('out_of_range.not_ready',st('binary_sensor.irrigation_rainfall_data_ready'),'off')
   ck('out_of_range.retains_multiplier',st('input_number.irrigation_rainfall_multiplier'),'0.85')
   await rain(1,1.5);await tick()
   ck('corrected_yesterday.not_maximum',st('input_number.irrigation_rainfall_multiplier'),'0.88')
   ck('corrected_yesterday.cached',json.loads(st('input_text.irrigation_rainfall_daily_records'))[-1],[str((clock[0]-timedelta(days=1)).date()),1.5])
   # Rolling mode uses the author's independent 24-hour buckets, not dated daily history.
   rolling=['last_twenty_four_hours','between_24_and_48_hours_ago','between_48_and_72_hours_ago','between_72_and_96_hours_ago','between_96_and_120_hours_ago']
   for n,name in enumerate(rolling):
    await svc('input_text','set_value',entity_id='input_text.irrigation_external_sensor_rainfall_'+name,value='sensor.fixture_rolling_'+str(n))
    h.states.async_set('sensor.fixture_rolling_'+str(n),str(n+1),{'unit_of_measurement':'mm'},timestamp=clock[0].timestamp())
   await svc('input_boolean','turn_on',entity_id='input_boolean.irrigation_rainfall_use_rolling_values')
   await number('days_of_rainfall_history_used',4);await settle()
   ck('rolling.five_buckets_preserved',st('input_number.irrigation_rainfall_multiplier'),'0.25')
   ck('rolling.no_daily_dependency',st('binary_sensor.irrigation_rainfall_data_ready'),'on')
   h.states.async_set('sensor.fixture_rolling_3','unavailable');await settle()
   ck('rolling.missing_retains_multiplier',st('input_number.irrigation_rainfall_multiplier'),'0.25')
   ck('rolling.missing_not_ready',st('binary_sensor.irrigation_rainfall_data_ready'),'off')
   ck('calendar.no_switch_calls',calls,[])
  finally:await h.async_stop()
 report={'layer':'Native HA controlled Nov 1-7 calendar and real graceful stop/start; virtual sensors only','results':out,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT).rglob('*.yaml')}}
 (ROOT/'tests/rainfall_calendar_results.json').write_text(json.dumps(report,indent=2));print(json.dumps(out,indent=2));assert all(r['passed'] for r in out)
logging.basicConfig(level=logging.ERROR);asyncio.run(main())
