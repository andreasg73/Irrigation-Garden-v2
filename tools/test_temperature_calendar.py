"""Native HA temperature lifecycle under a controlled calendar, virtual sensors only."""
import asyncio,json,tempfile,logging,hashlib
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch
from pathlib import Path
from homeassistant.util import dt as dt_util
from runtime_fixture import create_hass,ROOT
async def main():
 root=Path(tempfile.mkdtemp(prefix='kloggy-temperature-calendar-'));results=[]
 clock=[datetime(2026,11,1,12,tzinfo=ZoneInfo('Europe/Warsaw'))]
 with patch('homeassistant.util.dt.now',side_effect=lambda:clock[0]):
  h,calls=await create_hass(root)
  def st(e):return h.states.get(e).state if h.states.get(e) else None
  async def settle():await h.async_block_till_done();await asyncio.sleep(.15)
  async def svc(d,s,**data):await h.services.async_call(d,s,data,blocking=True)
  async def temperature(actual,forecast):
   h.states.async_set('sensor.fixture_temperature',str(actual),{'unit_of_measurement':'°C'},timestamp=clock[0].timestamp())
   h.states.async_set('sensor.fixture_forecast',str(forecast),{'unit_of_measurement':'°C'},timestamp=clock[0].timestamp())
   await settle()
  def ck(id,actual,expected):results.append({'id':id,'passed':actual==expected,'actual':actual,'expected':expected})
  try:
   await svc('input_boolean','turn_on',entity_id='input_boolean.irrigation_master_control_switch');await settle()
   await svc('input_text','set_value',entity_id='input_text.irrigation_external_sensor_current_temp',value='sensor.fixture_temperature')
   await svc('input_text','set_value',entity_id='input_text.irrigation_external_sensor_forecast_high_temp',value='sensor.fixture_forecast')
   await svc('input_number','set_value',entity_id='input_number.irrigation_temperature_baseline',value=25)
   await svc('input_number','set_value',entity_id='input_number.irrigation_days_of_temp_history_used',value=0)
   await svc('input_select','select_option',entity_id='input_select.irrigation_high_temp_options',option='Use Actual')
   await temperature(30,35)
   ck('day1.maximum',st('input_number.irrigation_temperature_highest_actual_temp_today'),'30.0')
   clock[0]+=timedelta(days=1)
   await temperature(10,15)
   ck('missed.midnight.new_day_lower',st('input_number.irrigation_temperature_highest_actual_temp_today'),'10.0')
   ck('missed.midnight.yesterday',st('input_number.irrigation_high_temp_1'),'30.0')
   ck('new_day.multiplier',st('input_number.irrigation_temp_multiplier'),'0.4')
   await temperature(18,20);await temperature(12,14)
   ck('same_day.retains_maximum',st('input_number.irrigation_temperature_highest_actual_temp_today'),'18.0')
   before_records=st('input_text.irrigation_temperature_daily_records')
   await svc('automation','trigger',entity_id='automation.irrigation_temperature_nightly_update',skip_condition=False);await settle()
   ck('same_day.nightly_is_idempotent',st('input_text.irrigation_temperature_daily_records'),before_records)
   clock[0]+=timedelta(days=2)
   await temperature(8,12)
   ck('gap.new_day_lower',st('input_number.irrigation_temperature_highest_actual_temp_today'),'8.0')
   ck('gap.two_days_ago',st('input_number.irrigation_high_temp_2'),'18.0')
   before=st('input_number.irrigation_temp_multiplier')
   await svc('input_number','set_value',entity_id='input_number.irrigation_days_of_temp_history_used',value=1);await settle()
   ck('gap.retains_multiplier',st('input_number.irrigation_temp_multiplier'),before)
   ck('gap.readiness_off',st('binary_sensor.irrigation_temperature_data_ready'),'off')
   valid=h.states.get('binary_sensor.irrigation_temperature_data_ready').attributes['valid']
   ck('gap.calendar_validity',[valid['input_number.irrigation_high_temp_1'],valid['input_number.irrigation_high_temp_2']],[False,True])
   await svc('input_boolean','turn_off',entity_id='input_boolean.irrigation_master_control_switch');await settle()
   await temperature(20,25)
   ck('master_off.weather_still_collected',st('input_number.irrigation_temperature_highest_actual_temp_today'),'20.0')
   await h.async_stop()
   h,new_calls=await create_hass(root);calls+=new_calls;await settle()
   ck('restart.master_stays_off',st('input_boolean.irrigation_master_control_switch'),'off')
   clock[0]+=timedelta(days=1)
   await temperature(9,13)
   ck('restart.next_day_lower',st('input_number.irrigation_temperature_highest_actual_temp_today'),'9.0')
   ck('restart.dated_yesterday',st('input_number.irrigation_high_temp_1'),'20.0')
   ck('restart.readiness_recovers',st('binary_sensor.irrigation_temperature_data_ready'),'on')
   before=st('input_number.irrigation_temp_multiplier')
   clock[0]+=timedelta(days=1)
   await svc('automation','trigger',entity_id='automation.irrigation_temperature_nightly_update',skip_condition=False);await settle()
   ck('stale_source.new_day_pending',[st('input_boolean.irrigation_temperature_'+k+'_reset_pending') for k in ['actual','forecast']],['on','on'])
   ck('stale_source.not_relabelled',json.loads(st('input_text.irrigation_temperature_daily_records'))[-1],[clock[0].date().isoformat(),None,None])
   ck('stale_source.retains_multiplier',st('input_number.irrigation_temp_multiplier'),before)
   ck('stale_source.readiness_off',st('binary_sensor.irrigation_temperature_data_ready'),'off')
   # Identical source values emit state_reported, not state_changed. The polling action must recover them.
   await temperature(9,13)
   await svc('automation','trigger',entity_id='automation.irrigation_temperature_nightly_update',skip_condition=False);await settle()
   ck('identical_fresh_report.recovers',st('binary_sensor.irrigation_temperature_data_ready'),'on')
   ck('journal.fits_helper',len(st('input_text.irrigation_temperature_daily_records'))<=255,True)
   clock[0]+=timedelta(days=1)
   await svc('input_number','set_value',entity_id='input_number.irrigation_days_of_temp_history_used',value=0)
   await temperature(-5,-2)
   ck('negative.new_day_maximum',st('input_number.irrigation_temperature_highest_actual_temp_today'),'-5.0')
   ck('negative.multiplier_clamped',st('input_number.irrigation_temp_multiplier'),'0.0')
   ck('calendar.no_switch_calls',calls,[])
  finally:
   await h.async_stop()
 report={'layer':'Native components, controlled dt.now calendar, actual graceful stop/start restore-state; no physical devices','results':results,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'Garden Irrigation').glob('*temperature.yaml')}}
 (ROOT/'tests/temperature_calendar_results.json').write_text(json.dumps(report,indent=2));print(json.dumps(results,indent=2))
 assert all(r['passed'] for r in results)
logging.basicConfig(level=logging.ERROR);asyncio.run(main())
