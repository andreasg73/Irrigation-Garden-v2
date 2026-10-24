"""Exercise original UI synchronization automations in native HA (3 x 16 x 2)."""
import asyncio,tempfile,json,logging,hashlib
from pathlib import Path
from runtime_fixture import create_hass,ROOT
async def main():
 h,calls=await create_hass(Path(tempfile.mkdtemp(prefix='kloggy-ui-')));results=[]
 def st(e):return h.states.get(e).state
 async def wait(fn):
  async with asyncio.timeout(4):
   while not fn():await asyncio.sleep(.01)
 async def setnum(e,v):await h.services.async_call('input_number','set_value',{'entity_id':e,'value':v},blocking=True)
 def check(id,truth,detail=None):results.append({'id':id,'passed':bool(truth),'detail':detail});assert truth,id
 try:
  await wait(lambda:st('input_boolean.irrigation_stop_in_progress')=='off')
  await h.services.async_call('input_boolean','turn_on',{'entity_id':'input_boolean.irrigation_master_control_switch'},blocking=True)
  await h.async_block_till_done()
  for c in [1,2,3]:
   for z in range(1,17):
    slider=f'input_number.irrigation_cycle{c}_zone{z}_duration';box=slider+'_box'
    for source,target,value,way in [(slider,box,z+1,'slider_to_box'),(box,slider,z+20,'box_to_slider')]:
     await setnum(source,value);await wait(lambda:float(st(target))==value)
     check(f'ui.{c}.{z}.{way}',float(st(target))==value,{'source':source,'target':target,'value':value})
  for invalid in ['unknown','unavailable','bad','nan','inf']:
   for src,suffix in [(f'input_number.irrigation_cycle{c}_zone{z}_duration','_box') for c in [1,2,3] for z in [10,16]]+[(f'input_number.irrigation_cycle{c}_zone{z}_duration_box','') for c in [1,2,3] for z in [10,16]]:
    target=src+'_box' if suffix else src.removesuffix('_box')
    good=h.states.get(src);before=st(target)
    h.states.async_set(src,invalid,good.attributes);await h.async_block_till_done()
    check(f'ui.invalid.{invalid}.{src}',st(target)==before,{'before':before,'after':st(target)})
    h.states.async_set(src,good.state,good.attributes);await h.async_block_till_done()
  check('ui.no_switch_calls',calls==[])
 except Exception as e:results.append({'id':'unhandled','passed':False,'detail':repr(e)})
 finally:
  await h.async_stop()
  p=ROOT/'Garden Irrigation/irrigation_ui_control.yaml'
  (ROOT/'tests/ui_runtime_results.json').write_text(json.dumps({'ha_version':'2026.10.2','layer':'native input_number service and state_changed events','source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'results':results,'switch_calls':calls},indent=2))
  print('PASS',sum(r['passed'] for r in results),'/',len(results))
 assert all(r['passed'] for r in results)
logging.basicConfig(level=logging.ERROR);asyncio.run(main())
