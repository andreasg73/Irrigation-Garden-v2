"""Original Master/remote selection with foreign aliases and renamed owned IDs.

Native HA only. Three unused remote actions are inert fixture placeholders;
the original remote master action is executed without MQTT or devices.
"""
import asyncio, copy, hashlib, json, logging, tempfile
from pathlib import Path
from unittest.mock import patch
import yaml
from runtime_fixture import ROOT, create_hass
from network_fixture import sandbox_network

async def main():
    original_load = yaml.safe_load
    remote = original_load((ROOT/'Garden Irrigation/irrigation_remote_control.yaml').read_text())
    remote_switch = next(a for a in remote['automation'] if a['id']=='irrigation_remote_control_switch')
    def inert(id, alias, initial):
        return {'id':id, 'alias':alias, 'initial_state':initial,
                'triggers':[{'trigger':'event','event_type':'fixture_never_emitted'}],
                'actions':[{'stop':'Inert fixture placeholder'}]}
    def load(text):
        doc=original_load(text)
        if not isinstance(doc,dict):return doc
        for a in doc.get('automation',[]):
            if a.get('id')=='irrigation_ui_show_weather_adjust_settings':
                a['alias']='Renamed package weather settings'
        if any(a.get('id')=='irrigation_master_control_switch_on' for a in doc.get('automation',[])):
            doc['automation'] += [
                inert('fixture_foreign_on','Irrigation Outside Package Enabled',True),
                inert('fixture_foreign_off','Irrigation Outside Package Disabled',False),
                inert('fixture_foreign_remote','Irrigation Remote Control Outside Package',True),
                copy.deepcopy(remote_switch),
                inert('irrigation_remote_control_cancel','Renamed package remote cancel',True),
                inert('irrigation_remote_control_queued_notification','Irrigation Remote Control Queued Notification',True),
                inert('irrigation_remote_control_button_pressed','Irrigation Remote Control Button Pressed',True),
            ]
        return doc
    rows=[]
    with patch('runtime_fixture.yaml.safe_load',side_effect=load):
        h,calls=await create_hass(Path(tempfile.mkdtemp(prefix='kloggy-ownership-')))
    def state(e):return h.states.get(e).state
    async def svc(d,s,e):await h.services.async_call(d,s,{'entity_id':e},blocking=True)
    async def settle():
        await h.async_block_till_done()
        async with asyncio.timeout(10):
            while any(h.states.get(e).attributes.get('current',0) for e in ['automation.irrigation_master_control_switch_off','automation.irrigation_master_control_switch_on','automation.irrigation_remote_control_switch']) or state('script.irrigation_cancel_irrigation')!='off':
                await asyncio.sleep(.02)
        await h.async_block_till_done()
    def check(id,e,expected):
        row={'id':id,'passed':state(e)==expected,'entity':e,'expected':expected,'actual':state(e),'automation_id':h.states.get(e).attributes.get('id')}
        rows.append(row);print(json.dumps(row),flush=True)
    foreign_on='automation.irrigation_outside_package_enabled'
    foreign_off='automation.irrigation_outside_package_disabled'
    foreign_remote='automation.irrigation_remote_control_outside_package'
    owned='automation.renamed_package_weather_settings'
    owned_remote='automation.renamed_package_remote_cancel'
    master='input_boolean.irrigation_master_control_switch'
    remote_helper='input_boolean.irrigation_remote_control'
    try:
        await settle()
        check('startup.foreign_enabled_preserved',foreign_on,'on')
        check('startup.renamed_owned_disabled',owned,'off')
        check('startup.renamed_remote_disabled',owned_remote,'off')
        await svc('automation','turn_on',foreign_on)
        await svc('automation','turn_off',foreign_off)
        await svc('automation','turn_off',owned)
        await svc('input_boolean','turn_on',master);await settle()
        check('master_on.foreign_disabled_preserved',foreign_off,'off')
        check('master_on.foreign_enabled_preserved',foreign_on,'on')
        check('master_on.renamed_owned_enabled',owned,'on')
        await svc('automation','turn_off',foreign_remote)
        await svc('automation','turn_off',owned_remote)
        await svc('input_boolean','turn_on',remote_helper);await settle()
        check('remote_on.foreign_disabled_preserved',foreign_remote,'off')
        check('remote_on.renamed_owned_enabled',owned_remote,'on')
        await svc('automation','turn_on',foreign_remote)
        await svc('automation','turn_on',owned_remote)
        await svc('input_boolean','turn_off',remote_helper);await settle()
        check('remote_off.foreign_enabled_preserved',foreign_remote,'on')
        check('remote_off.renamed_owned_disabled',owned_remote,'off')
        await svc('automation','turn_on',foreign_on)
        await svc('automation','turn_on',owned)
        await svc('input_boolean','turn_off',master);await settle()
        check('master_off.foreign_enabled_preserved',foreign_on,'on')
        check('master_off.renamed_owned_disabled',owned,'off')
        rows.append({'id':'containment.no_switch_calls','passed':not calls,'calls':list(calls)})
    finally:
        await h.async_stop()
    report={'scope':'Native HA; original master and remote switch; explicitly injected foreign aliases and owned rename; three inert remote actions','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'Garden Irrigation').glob('*.yaml'))},'results':rows}
    (ROOT/'tests/ownership_results.json').write_text(json.dumps(report,indent=2)+'\n')
    assert all(x['passed'] for x in rows)

if __name__=='__main__':
    logging.basicConfig(level=logging.WARNING)
    with sandbox_network():asyncio.run(main())
