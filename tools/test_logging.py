"""Original retention sequence in native HA; shell/update/notify are local stubs.
The test never opens or edits an actual log file.
"""
import asyncio,json,tempfile,logging,hashlib
from pathlib import Path
from datetime import timedelta
import yaml
from homeassistant.helpers.script import Script
from homeassistant.helpers.config_validation import SCRIPT_SCHEMA
from homeassistant.util import dt as dt_util
from runtime_fixture import create_hass,ROOT
async def main():
 h,switches=await create_hass(Path(tempfile.mkdtemp(prefix='kloggy-log-')));results=[];commands=[];lines=[];unavailable=False
 async def update(call):
  eid=call.data['entity_id'];eid=eid[0] if isinstance(eid,list) else eid
  if eid!='sensor.logging_my_log_irrigation_first_line':raise RuntimeError('Forbidden update')
  h.states.async_set(eid,'unavailable' if unavailable else lines[0] if lines else '')
  h.states.async_set('sensor.my_log_irrigation_log_size_bytes',str(sum(map(len,lines))))
 async def delete(call):
  commands.append(call.service)
  if unavailable:raise RuntimeError('Oracle detected deletion with unavailable first-line sensor')
  if lines:lines.pop(0)
 h.services.async_register('homeassistant','update_entity',update)
 h.services.async_register('shell_command','logging_log_file_delete_first_line',delete)
 doc=yaml.safe_load((ROOT/'Logging/logging.yaml').read_text())['script']['logging_clear_log_of_old_data']
 seq=Script(h,SCRIPT_SCHEMA(doc['sequence']),'Retention fixture','fixture',script_mode=doc['mode'])
 today=dt_util.now().date();header=lambda d:'===== '+d.strftime('%a %d %b %Y')+' ====='
 async def run(name):
  try:await seq.async_run({'log_name':name})
  except Exception as e:return repr(e)
 async def case(id,fn):
  before=len(commands);error=await fn();results.append({'id':id,'passed':error is None,'detail':error,'deletes':len(commands)-before})
 try:
  h.states.async_set('input_number.logging_irrigation_days_to_keep','7')
  h.states.async_set('sensor.my_log_irrigation_log_size_bytes','100')
  for bad in ['heating','',None,'../../configuration']:
   before=len(commands);err=await run(bad);results.append({'id':'retention.reject.'+str(bad),'passed':err is None and len(commands)==before})
  lines[:]=[header(today-timedelta(days=9)),'old1',header(today-timedelta(days=7)),'boundary',header(today),'today']
  err=await run('irrigation');results.append({'id':'retention.keep_boundary','passed':not err and lines==[header(today-timedelta(days=7)),'boundary',header(today),'today'],'detail':{'remaining':list(lines),'error':err}})
  h.states.async_set('input_number.logging_irrigation_days_to_keep','0');before=len(commands);err=await run('irrigation')
  results.append({'id':'retention.zero_keep_all','passed':not err and len(commands)==before})
  h.states.async_set('input_number.logging_irrigation_days_to_keep','7');unavailable=True;before=len(commands);err=await run('irrigation')
  results.append({'id':'retention.unavailable_no_delete','passed':not err and len(commands)==before,'detail':{'deletes':len(commands)-before,'error':err}})
  results.append({'id':'retention.no_switch_calls','passed':switches==[]})
 finally:
  await h.async_stop();p=ROOT/'Logging/logging.yaml'
  (ROOT/'tests/logging_results.json').write_text(json.dumps({'ha_version':'2026.10.2','layer':'native Script with in-memory log and restricted shell stubs','source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'results':results,'commands':commands},indent=2))
  print(json.dumps(results))
 assert all(r['passed'] for r in results)
logging.basicConfig(level=logging.ERROR);asyncio.run(main())
