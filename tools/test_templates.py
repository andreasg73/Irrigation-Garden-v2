"""Read-only tests of candidate YAML using Home Assistant's real 2026.10 engine.

No server or device integrations are started. All states belong to this local
HomeAssistant object. Expected calculations below are independent Python math.
"""
import asyncio
import hashlib
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import yaml
from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT
checks=[]
def check(label,actual,expected):
    checks.append({'id':label,'passed':actual==expected,'actual':actual,'expected':expected})

async def main():
    hass=HomeAssistant(str(ROOT/'tests/template-runtime'))
    # Generated Lovelace is a derivative, not another engine package.
    sources={str(p.relative_to(SOURCE)):yaml.safe_load(p.read_text()) for folder in ['Garden Irrigation','Logging'] for p in (SOURCE/folder).glob('*.yaml')}
    def state(e,value,attrs=None):hass.states.async_set(e,str(value),attrs or {})
    def render(t,variables=None):return Template(t,hass).async_render(variables or {},strict=True)
    def walk(value):
        if isinstance(value,dict):
            for v in value.values():yield from walk(v)
        elif isinstance(value,list):
            for v in value:yield from walk(v)
        elif isinstance(value,str) and ('{{' in value or '{%' in value):yield value
    templates=[t for doc in sources.values() for t in walk(doc)]
    for i,t in enumerate(templates):
        try:Template(t,hass).ensure_valid();check(f'jinja-syntax-{i}',True,True)
        except Exception as e:check(f'jinja-syntax-{i}',str(e),True)
    for doc in sources.values():
        for domain in ['input_boolean','input_number','input_text','input_select']:
            for name,conf in (doc.get(domain) or {}).items():
                conf=conf or {}
                default={'input_boolean':'off','input_number':conf.get('min',0),'input_text':'','input_select':(conf.get('options') or [''])[0]}[domain]
                value=conf.get('initial',default)
                if isinstance(value,bool):value='on' if value else 'off'
                state(f'{domain}.{name}',value)
    state('input_boolean.irrigation_testing_mode','off')
    state('input_number.irrigation_weather_adjusted_maximum_duration_in_minutes',120)
    state('input_number.irrigation_weather_adjusted_minimum_duration_in_seconds',3)
    for cycle in [1,2,3]:
        doc=sources[f'Garden Irrigation/irrigation_globals_cycle{cycle}.yaml']
        sensors=doc['template'][0]['sensor']
        duration_sensor=next(s for s in sensors if s['unique_id']==f'irrigation_cycle{cycle}_duration_in_seconds')
        for z in range(1,17):
            state(f'input_number.irrigation_cycle{cycle}_zone{z}_duration',z)
            state(f'input_boolean.irrigation_cycle{cycle}_zone{z}_every_day','off')
            for day in ['mon','tue','wed','thu','fri','sat','sun']:
                state(f'input_boolean.irrigation_cycle{cycle}_zone{z}_{day}','on' if day=='wed' else 'off')
        for weekday,day in enumerate(['mon','tue','wed','thu','fri','sat','sun']):
            with patch('homeassistant.util.dt.now',return_value=datetime(2026,10,19+weekday,12,tzinfo=ZoneInfo('Europe/Warsaw'))):
                values=render(duration_sensor['attributes']['zone_duration'])
            for z in range(1,17):
                expected=z*60 if cycle==3 or day=='wed' else 0
                check(f'duration-c{cycle}-z{z}-{day}',int(values[f'zone{z}']),expected)
        # Every-day supersedes the per-day selector, and each count must select
        # the first N zones, not the longest N durations.
        for z in range(1,17):
            state(f'input_boolean.irrigation_cycle{cycle}_zone{z}_every_day','on')
            state(f'sensor.irrigation_cycle{cycle}_zone{z}_actual_duration_in_seconds',z*60)
        values=render(duration_sensor['attributes']['zone_duration'])
        for z in range(1,17):check(f'every-day-c{cycle}-z{z}',int(values[f'zone{z}']),z*60)
        for n in range(1,17):
            state('input_number.irrigation_number_of_zones',n)
            check(f'cycle-total-c{cycle}-n{n}',render(duration_sensor['state']),sum(range(1,n+1))*60)
        for s in sensors:
            if 'zone' in s['unique_id']:
                check('missing-parent-'+s['unique_id'],render(s['state']),0)
    # UI: both directions on all 48 duration pairs. Reject transient states.
    sync=next(a for a in sources['Garden Irrigation/irrigation_ui_control.yaml']['automation'] if a['id']=='irrigation_ui_duration_synchronisation')
    for c in [1,2,3]:
        for z in range(1,17):
            for suffix,other in [('', '_box'),('_box','')]:
                eid=f'input_number.irrigation_cycle{c}_zone{z}_duration{suffix}'
                expected=f'input_number.irrigation_cycle{c}_zone{z}_duration{other}'
                state(eid,7)
                trigger={'entity_id':eid,'to_state':{'state':'7'}}
                check(f'ui-map-c{c}-z{z}{suffix}',render(sync['action'][0]['data']['entity_id'],{'trigger':trigger}),expected)
                check(f'ui-value-c{c}-z{z}{suffix}',render(sync['action'][0]['data']['value'],{'trigger':trigger}),7)
    for value in ['unknown','unavailable','', 'NaN','inf']:
        eid='input_number.irrigation_cycle1_zone10_duration'
        state(eid,value)
        check('ui-ignore-'+value,render(sync['condition'][0]['value_template'],{'trigger':{'entity_id':eid,'to_state':{'state':value}}}),False)
    rain=next(a for a in sources['Garden Irrigation/irrigation_weather_rainfall.yaml']['automation'] if a['id']=='irrigation_rainfall_calculate_multiplier')['action'][0]['data']['value']
    for rolling in [False,True]:
        state('input_boolean.irrigation_rainfall_use_rolling_values','on' if rolling else 'off')
        ids=['sensor.irrigation_sensor_rainfall_last_twenty_four_hours','sensor.irrigation_sensor_rainfall_between_24_and_48_hours_ago','sensor.irrigation_sensor_rainfall_between_48_and_72_hours_ago','sensor.irrigation_sensor_rainfall_between_72_and_96_hours_ago','sensor.irrigation_sensor_rainfall_between_96_and_120_hours_ago'] if rolling else ['sensor.irrigation_sensor_rainfall_today','sensor.irrigation_sensor_rainfall_yesterday','input_number.irrigation_rainfall_2','input_number.irrigation_rainfall_3','input_number.irrigation_rainfall_4']
        for e,v in zip(ids,[2,4,6,8,10]):state(e,v)
        for d,v in enumerate([100,75,50,25],1):state(f'input_number.irrigation_rainfall_percentage_{d}',v)
        state('input_number.irrigation_rainfall_threshold',20)
        for days in range(5):
            state('input_number.irrigation_days_of_rainfall_history_used',days)
            expected=round(max(0,1-(2+sum([4,4.5,4,2.5][:days]))/20),2)
            check(f'rain-{rolling}-days{days}',render(rain),expected)
    temp=next(a['data']['value'] for a in sources['Garden Irrigation/irrigation_weather_temperature.yaml']['script']['irrigation_temperature_calculate_multiplier']['sequence'] if a.get('data',{}).get('entity_id')=='input_number.irrigation_temp_multiplier')
    state('input_number.irrigation_temperature_baseline',20)
    state('input_number.irrigation_temperature_highest_actual_temp_today',30)
    state('input_number.irrigation_temperature_highest_forecast_high_temp_today',40)
    for d,v in enumerate([20,15,10,5],1):state(f'input_number.irrigation_high_temp_{d}',v)
    for option,v in [('Use Actual',30),('Use Forecast',40),('Use Highest',40)]:
        state('input_select.irrigation_high_temp_options',option)
        for days in range(5):
            state('input_number.irrigation_days_of_temp_history_used',days)
            expected=round((v+sum([20,15,10,5][:days]))/(days+1)/20,2)
            check(f'temp-{option}-{days}',render(temp),expected)
    manifest={str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE.rglob('*.yaml')}
    report={'ha_version':'2026.10.2','scope':'actual HA Jinja engine, local states; no live devices or frontend','checks':checks,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'manifest':manifest}
    (ROOT/'tests/template_results.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ['checks','manifest']}))
    for c in checks:
        if not c['passed']:print(c)
    await hass.async_stop()
    if report['failed']:raise SystemExit(1)

if __name__=='__main__':asyncio.run(main())
