"""Original template boundaries; independent expected outcomes."""
import asyncio,json
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
from pathlib import Path
import yaml
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.helpers.template import Template
ROOT=Path(__file__).resolve().parents[1]
async def main():
 hass=HomeAssistant(str(ROOT/'tests/boundaries'));results=[]
 dt_util.set_default_time_zone(ZoneInfo('Europe/Warsaw'))
 def put(e,v,a=None):hass.states.async_set(e,str(v),a or {})
 def render(t,v=None):return Template(t,hass).async_render(v or {},strict=True)
 def ck(id,a,e):results.append({'id':id,'passed':a==e,'actual':a,'expected':e})
 docs={p.name:yaml.safe_load(p.read_text()) for p in (ROOT/'Garden Irrigation').glob('*.yaml')}
 put('input_boolean.irrigation_master_control_switch','on');put('input_number.irrigation_number_of_zones',1)
 next_template=next(s['state'] for block in docs['irrigation_globals.yaml']['template'] for s in block.get('sensor',[]) if s['unique_id']=='irrigation_next_run')
 for c,start in [(1,'20:00:00'),(2,'14:00:00')]:
  put(f'input_text.irrigation_cycle{c}_name',f'Cycle{c}');put(f'input_boolean.irrigation_cycle{c}_schedule_enabled','on')
  put(f'input_datetime.irrigation_cycle{c}_start_time',start)
  put(f'input_boolean.irrigation_cycle{c}_zone1_every_day','on');put(f'input_number.irrigation_cycle{c}_zone1_duration','1')
 for c in [1,2,3]:put(f'input_boolean.irrigation_cycle{c}_running','off')
 with patch('homeassistant.util.dt.now',return_value=datetime(2026,10,21,12,tzinfo=ZoneInfo('Europe/Warsaw'))):
  ck('next_run.earlier_cycle2_no_sensor_time',render(next_template),'Cycle2 cycle at 14:00')
  for v in ['0','0.0','unknown','unavailable']:
   put('input_number.irrigation_cycle2_zone1_duration',v)
   ck('next_run.ignore_'+v,render(next_template),'Cycle1 cycle at 20:00')
 put('input_number.irrigation_cycle2_zone1_duration','1')
 with patch('homeassistant.util.dt.now',return_value=datetime(2026,10,21,23,tzinfo=ZoneInfo('Europe/Warsaw'))):
  ck('next_run.tomorrow_earliest',render(next_template),'Tomorrow at 14:00')
  put('input_boolean.irrigation_cycle2_schedule_today_only','on')
  ck('next_run.today_only_no_tomorrow',render(next_template),'Tomorrow at 20:00')
 # Yesterday has calendar-day boundaries even on 23- and 25-hour days.
 history=next(s for s in docs['irrigation_globals_zones.yaml']['sensor'] if s['unique_id']=='irrigation_zone1_total_time_yesterday')
 for dt,expected in [(datetime(2026,3,30,12,tzinfo=ZoneInfo('Europe/Warsaw')),23),(datetime(2026,10,26,12,tzinfo=ZoneInfo('Europe/Warsaw')),25)]:
  with patch('homeassistant.util.dt.now',return_value=dt):
   start=datetime.fromisoformat(str(render(history['start'])));end=datetime.fromisoformat(str(render(history['end'])))
   ck('history.DST_'+dt.date().isoformat(),(end.timestamp()-start.timestamp())/3600,expected)
 # Complement waits must never accept unknown/unavailable as success.
 scheduler=docs['irrigation_triggered.yaml']['automation'][0]
 wait_template=next(a['wait_template'] for a in scheduler['action'][0]['then'] if 'wait_template'in a)
 for value,expected in [('unknown',False),('unavailable',False),('on',False),('off',True)]:
  put('binary_sensor.fixture_gate',value)
  ck('schedule.not_on_'+value,render(wait_template,{'trigger':{'id':'cycle1'},'wait_for_entity_name':'binary_sensor.fixture_gate','wait_for_entity_state':'not on'}),expected)
 report={'ha_version':'2026.10.2','layer':'actual HA renderer; fixed test clocks; no devices','results':results}
 (ROOT/'tests/boundary_results.json').write_text(json.dumps(report,indent=2))
 print(json.dumps(report,indent=2));await hass.async_stop()
 if any(not r['passed'] for r in results):raise SystemExit(1)
if __name__=='__main__':asyncio.run(main())
