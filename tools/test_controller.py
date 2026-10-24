"""Actual HA automations: optional controller diagnostics, no physical services."""
import asyncio,json,tempfile,logging,hashlib
from pathlib import Path
from runtime_fixture import create_hass,ROOT
async def main():
 h,calls=await create_hass(Path(tempfile.mkdtemp(prefix='kloggy-wifi-')));out=[];notifications=[]
 def state(e):return h.states.get(e).state if h.states.get(e) else None
 async def svc(d,s,**data):await h.services.async_call(d,s,data,blocking=True)
 async def boolean(n,on):await svc('input_boolean','turn_on' if on else 'turn_off',entity_id='input_boolean.irrigation_'+n)
 async def text(n,v):await svc('input_text','set_value',entity_id='input_text.irrigation_'+n,value=v)
 async def wait(test):
  async with asyncio.timeout(5):
   while not test():await asyncio.sleep(.025)
 async def record(id,truth,detail=None):
  out.append({'id':id,'passed':bool(truth),'detail':detail});assert truth,id
 try:
  await wait(lambda:state('input_boolean.irrigation_stop_in_progress')=='off')
  await boolean('master_control_switch',True)
  await wait(lambda:state('automation.irrigation_warning_controller_unavailable')=='on')
  await h.async_block_till_done()
  await record('wifi.none_optional',state('binary_sensor.irrigation_controllers_available')=='on')
  h.states.async_set('sensor.fixture_wifi1','-60');h.states.async_set('sensor.fixture_wifi2','-70')
  await text('external_sensor_controller_1_wifi','sensor.fixture_wifi1');await text('external_sensor_controller_2_wifi','sensor.fixture_wifi2')
  await wait(lambda:state('binary_sensor.irrigation_controllers_available')=='on')
  await record('wifi.both_configured',True)
  h.states.async_set('sensor.fixture_wifi2','unavailable');await wait(lambda:state('binary_sensor.irrigation_controllers_available')=='off')
  await wait(lambda:h.states.get('automation.irrigation_warning_controller_unavailable').attributes.get('last_triggered') is not None);await record('wifi.second_controller_detected',h.states.get('automation.irrigation_warning_controller_unavailable').attributes.get('last_triggered') is not None)
  await record('wifi.no_notify_dependency',state('script.notify') is None and calls==[])
  h.states.async_set('sensor.fixture_wifi2','-70');await wait(lambda:state('binary_sensor.irrigation_controllers_available')=='on')
  # Explicit local stub for optional author notification system. No external send.
  async def notify(call):notifications.append(dict(call.data))
  h.services.async_register('script','notify',notify);h.states.async_set('script.notify','off')
  h.states.async_set('input_text.notifications_user1_name','Fixture One');h.states.async_set('input_text.notifications_user2_name','Fixture Two')
  await boolean('notify_user1',True);await boolean('notify_user2',True)
  await boolean('ha_notify_of_controller_wifi_events',False);await boolean('user_notify_of_controller_wifi_events',False)
  h.states.async_set('sensor.fixture_wifi1','unknown');await wait(lambda:state('binary_sensor.irrigation_controllers_available')=='off');await asyncio.sleep(.2)
  await record('wifi.toggles_off_suppress',notifications==[])
  h.states.async_set('sensor.fixture_wifi1','-60');await wait(lambda:state('binary_sensor.irrigation_controllers_available')=='on');await asyncio.sleep(.2)
  await record('wifi.recovery_toggles_off_suppress',notifications==[])
  await boolean('ha_notify_of_controller_wifi_events',True);await boolean('user_notify_of_controller_wifi_events',True)
  h.states.async_set('sensor.fixture_wifi2','unavailable');await wait(lambda:len(notifications)==3)
  await record('wifi.recipients_distinct',sorted(x['tell'] for x in notifications if 'tell' in x)==['Fixture One','Fixture Two'],notifications)
  h.states.async_set('sensor.fixture_wifi2','-70');await wait(lambda:len(notifications)==4)
  await record('wifi.recovery_persistent',notifications[-1].get('show') is True and 'AVAILABLE' in notifications[-1]['message'])
  await record('wifi.no_switch_calls',calls==[])
 except Exception as e:out.append({'id':'unhandled','passed':False,'detail':repr(e)})
 finally:
  await h.async_stop()
  report={'layer':'native HA 2026.10.2; notification stub local only','results':out,'switch_calls':calls,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'Garden Irrigation').glob('*.yaml')}}
  (ROOT/'tests/controller_results.json').write_text(json.dumps(report,indent=2,default=str));print(json.dumps(out,default=str))
 assert all(r['passed'] for r in out)
logging.basicConfig(level=logging.ERROR);asyncio.run(main())
