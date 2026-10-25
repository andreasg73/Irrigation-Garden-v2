"""Portable independent math, journal and control-preservation contracts."""
import json
import ast
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import yaml
from jinja2 import StrictUndefined
from jinja2.nativetypes import NativeEnvironment

ROOT=Path(__file__).resolve().parents[1]
def source(path, before=False):
    obj=json.loads((ROOT/'tests/fixtures/decisions-before.json').read_text(encoding='utf-8'))[path] if before else yaml.safe_load((ROOT/path).read_text(encoding='utf-8'))
    def normalize(v):
        if isinstance(v,dict):return {k:normalize(x) for k,x in v.items()}
        if isinstance(v,list):return [normalize(x) for x in v]
        if isinstance(v,str):return '\n'.join(line.rstrip() for line in v.split('\n'))
        return v
    return normalize(obj)

class Decisions(unittest.TestCase):
    def test_worker_keeps_every_existing_control_action(self):
        path='Garden Irrigation/irrigation_run_a_cycle.yaml'
        before=source(path,True)['script']['irrigation_run_a_cycle']
        after=source(path)['script']['irrigation_run_a_cycle']
        def strip(obj):
            if isinstance(obj,list):
                return [strip(v) for v in obj if not (isinstance(v,dict) and (v.get('event')=='irrigation_decision' or ('variables' in v and all(k.startswith('decision_') for k in v['variables']))))]
            if isinstance(obj,dict):return {k:strip(v) for k,v in obj.items()}
            return obj
        self.assertEqual(before,strip(after))

    def test_schedule_native_admission_and_final_guards_unchanged(self):
        path='Garden Irrigation/irrigation_triggered.yaml'
        before=source(path,True)['automation'][0]
        after=source(path)['automation'][0]
        action=after['action']
        self.assertEqual(action[1]['if'][1]['conditions'][0]['conditions'],before['condition'])
        self.assertEqual(action[2:6],before['condition'])
        final=[a for a in before['action'] if a.get('condition')=='template'][-1]
        self.assertIn(final,action)
        self.assertEqual(next(a for a in action if a.get('if',[{}])[0].get('condition')=='not')['if'][0]['conditions'],[final])
        self.assertEqual(action[1]['then'][-1],{'stop':'Scheduled attempt rejected'})

    def test_cancel_journals_only_after_all_existing_safety_actions(self):
        path='Garden Irrigation/irrigation_cancel.yaml'
        before=source(path,True)['script']['irrigation_cancel_irrigation']['sequence']
        after=source(path)['script']['irrigation_cancel_irrigation']['sequence']
        self.assertEqual(after[:-1],before)
        self.assertEqual(after[-1]['then'][0]['event'],'irrigation_decision')

    def test_snapshot_formula_matches_independent_math(self):
        sequence=source('Garden Irrigation/irrigation_run_a_cycle.yaml')['script']['irrigation_run_a_cycle']['sequence']
        zone=next(a['repeat']['sequence'] for a in sequence if 'repeat' in a)
        templates=[a['variables'] for a in zone if 'variables' in a and any(k.startswith('decision_') for k in a['variables'])]
        env=NativeEnvironment(undefined=StrictUndefined)
        for cycle in ('cycle1','cycle3'):
            for rain,temp in ((1,1),(.5,.8),(0,1),(1,0),(1,2)):
                for today in (True,False):
                    for testing in (True,False):
                        variables=dict(decision_base=10,decision_rain=cycle!='cycle3',decision_temp=cycle!='cycle3',decision_rain_factor=rain,decision_temp_factor=temp,decision_min=300,decision_max=900,decision_today=(today or cycle=='cycle3'),decision_testing=testing,cycle=cycle)
                        value=env.from_string(templates[-1]['decision_expected']).render(variables)
                        if isinstance(value,str):value=ast.literal_eval(value.strip())
                        raw=600*(rain*temp if cycle!='cycle3' else 1)
                        bounded=(min(900,max(300,raw)) if raw and cycle!='cycle3' else raw)
                        expected=round(bounded/(60 if testing else 1)) if variables['decision_today'] else 0
                        self.assertEqual(value,expected,variables)

    def test_restored_journal_bound_and_snapshot_names(self):
        sensor=source('Garden Irrigation/irrigation_logging.yaml')['template'][0]['sensor'][0]
        env=NativeEnvironment(undefined=StrictUndefined)
        env.globals.update(now=lambda:datetime(2026,10,25,15,0),states=lambda e: {'input_text.irrigation_cycle1_name':'Morning','input_text.irrigation_zone1_name':'Lawn'}.get(e,'unknown'))
        old=[{'reason':'duration_zero','sequence':n} for n in range(64)]
        event={'reason':'duration_selected','cycle':'cycle1','zone':1,'seconds':240,'rain_factor':.5}
        result=env.from_string(sensor['attributes']['records']).render(this=SimpleNamespace(attributes={'records':old}),trigger=SimpleNamespace(event=SimpleNamespace(data=event)))
        if isinstance(result,str):result=ast.literal_eval(result.strip())
        self.assertEqual(len(result),64);self.assertEqual(result[0]['sequence'],1)
        self.assertEqual(result[-1]['cycle_name'],'Morning');self.assertEqual(result[-1]['zone_name'],'Lawn')
        self.assertEqual(result[-1]['rain_factor'],.5);self.assertEqual(old[-1]['sequence'],63)

if __name__=='__main__':unittest.main()
