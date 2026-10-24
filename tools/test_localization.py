"""Meaningful contracts: English identity, protected logic, fallback and hostile input."""
import copy,json,tempfile,unittest
from pathlib import Path
from localize_lovelace import localize,read_catalog,write_catalog,validate,DISPLAY,JINJA,key_for
ROOT=Path(__file__).resolve().parents[1]
BASE=json.loads((ROOT/'dist/en/irrigation_dashboard.json').read_text())
META,EN=read_catalog(ROOT/'i18n/en.ini')

def strip_display(x):
 if isinstance(x,dict):return {k:({f:('<display>' if isinstance(t,str) else strip_display(t)) for f,t in v.items()} if k=='custom_fields' and isinstance(v,dict) else strip_display(v)) for k,v in x.items() if k not in DISPLAY}
 if isinstance(x,list):return [strip_display(v) for v in x]
 return x

class Contracts(unittest.TestCase):
 def test_current_source_preserves_prechange_control_structure(self):
  original=json.loads((ROOT/'tests/fixtures/stage41-english-before.json').read_text())
  def without_style(x):
   if isinstance(x,dict):return {k:without_style(v) for k,v in x.items() if k not in {'styles','style','card_mod'} | DISPLAY}
   if isinstance(x,list):return [without_style(v) for v in x]
   return x
  self.assertEqual(without_style(original),without_style(BASE))
 def test_rain_schedule_label_both_states_and_action(self):
  translated,_=localize(BASE,'pl',ROOT/'i18n');found=[]
  def walk(x):
   if isinstance(x,dict):
    if x.get('type')=='custom:button-card' and x.get('entity')=='input_boolean.irrigation_ignore_schedule_if_raining':found.append(x)
    for v in x.values():walk(v)
   elif isinstance(x,list):
    for v in x:walk(v)
  walk(translated);self.assertEqual(len(found),1);card=found[0]
  self.assertEqual(card['name'],'Pomijaj harmonogramy podczas deszczu')
  self.assertEqual({s['value']:s['name'] for s in card['state']},{'on':card['name'],'off':card['name']})
  self.assertEqual(card['tap_action'],{'action':'toggle'})
  self.assertIn({'white-space':'normal'},card['styles']['name'])
 def test_english_is_exact_original(self):
  x,r=localize(BASE,'en',ROOT/'i18n');self.assertEqual(x,BASE);self.assertEqual(r['changed_fields'],0)
 def test_polish_keeps_all_control_structure(self):
  x,r=localize(BASE,'pl',ROOT/'i18n');self.assertEqual(strip_display(x),strip_display(BASE));self.assertFalse(r['fallback_keys']);self.assertGreater(r['changed_fields'],900)
 def test_original_javascript_and_jinja_are_unchanged(self):
  translated,_=localize(BASE,'pl',ROOT/'i18n');seen=0
  def walk(a,b):
   nonlocal seen
   if isinstance(a,dict):
    for k,v in a.items():walk(v,b[k])
   elif isinstance(a,list):
    for x,y in zip(a,b):walk(x,y)
   elif isinstance(a,str):
    if a!=b and a.strip().startswith('[[['):self.assertIn(a.strip()[3:-3],b);seen+=1
    if '{{' in a or '{%' in a:
     if 'clash_text' in a:
      for part in JINJA.findall(a):
       self.assertIn(part[2:-2].strip() if 'clash_text' in part else part,b)
     else:self.assertEqual(JINJA.findall(a),JINJA.findall(b))
    # config-template-card treats ANY ${ as an expression; never introduce it
    # inside a nested button-card's JavaScript regex or literal dictionary.
    if '${' not in a:self.assertNotIn('${',b)
  walk(BASE,translated);self.assertGreater(seen,0)
 def test_displayed_clash_message_preserves_custom_names(self):
  import jinja2
  translated,_=localize(BASE,'pl',ROOT/'i18n')
  found=[]
  def walk(x):
   if isinstance(x,dict):
    if isinstance(x.get('content'),str) and 'ig_clash' in x['content']:found.append(x['content'])
    for v in x.values():walk(v)
   elif isinstance(x,list):
    for v in x:walk(v)
  walk(translated);self.assertEqual(len(found),1)
  names={'input_text.irrigation_cycle1_name':'You have set A','input_text.irrigation_cycle2_name':'B will not run.'}
  text='You have set You have set A to start before B will not run. has ended.<br><br>You have set A will not run.'
  rendered=jinja2.Environment().from_string(found[0]).render(states=lambda k:names[k],state_attr=lambda *a:text)
  self.assertIn('Ustawiono start cyklu You have set A przed zakończeniem cyklu B will not run..',rendered)
  self.assertIn('You have set A nie zostanie uruchomiony.',rendered)
 def test_missing_key_falls_back_and_new_language_needs_no_code(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d);write_catalog(path/'en.ini','en','English',EN)
   write_catalog(path/'fr.ini','fr','Français',{key_for('Number Of Zones'):'Nombre de zones'})
   x,r=localize(BASE,'fr',path);self.assertEqual(len(r['fallback_keys']),len(EN)-1)
   text=json.dumps(x,ensure_ascii=False);self.assertIn('Nombre de zones',text);self.assertIn('Weather Sensors',text)
 def test_apostrophe_quotes_percent_and_unicode_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'pl.ini';v={key_for('Name'):'Nazwa „A” / O\'Brien / 100% / żółć\nDruga linia'}
   write_catalog(p,'pl','Polski',v);self.assertEqual(read_catalog(p)[1],v);validate(EN,v)
   p.write_bytes(b'\xef\xbb\xbf'+p.read_bytes());self.assertEqual(read_catalog(p)[1],v)
 def test_invalid_markup_template_and_unknown_key_rejected(self):
  with self.assertRaises(ValueError):validate(EN,{key_for('Every<br>day'):'Codziennie'})
  with self.assertRaises(ValueError):validate(EN,{key_for('Name'):'{{ states() }}'})
  with self.assertRaises(ValueError):validate(EN,{'not_a_key':'text'})
 def test_invalid_language_path_rejected(self):
  with self.assertRaises(ValueError):localize(BASE,'../pl',ROOT/'i18n')
 def test_duplicate_and_mismatched_catalog_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);write_catalog(p/'en.ini','en','English',EN);write_catalog(p/'pl.ini','fr','wrong',{})
   with self.assertRaises(ValueError):localize(BASE,'pl',p)
   (p/'pl.ini').write_text('[meta]\nformat=1\n[messages]\nx="one"\nx="two"\n')
   with self.assertRaises(Exception):read_catalog(p/'pl.ini')

if __name__=='__main__':unittest.main()

