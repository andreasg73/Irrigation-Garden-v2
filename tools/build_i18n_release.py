"""Compile original Kloggy authoring YAML with a replaceable INI language catalog.

python tools/build_i18n_release.py --language pl
python tools/build_i18n_release.py --language en --output candidate/generated/en
"""
import argparse,hashlib,json,configparser
from pathlib import Path
import yaml
from compile_lovelace import Compiler,custom_types
from localize_lovelace import localize,extract,write_catalog,key_for
from enhance_lovelace import enhance,UI_LABELS
from decision_labels import DECISION_LABELS
ROOT=Path(__file__).resolve().parents[1]
canonical=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
sha=lambda x:hashlib.sha256(x).hexdigest()

def build(candidate,output,language,catalog_dir):
 source=candidate/'lovelace';c=Compiler(source);base={'views':[c.compile(source/'view_garden_irrigation.yaml')]}
 used=set(c.loaded);expansions=len(c.loaded)
 c.compile(source/'garden_irrigation/settings/rainfall/item_settings_smartweather_stations_used.yaml')
 assert len(set(c.loaded))==41
 data,report=localize(base,language,catalog_dir)
 data,ui_report=enhance(data,language,catalog_dir)
 cache={}
 def share(x):
  if isinstance(x,dict):x={k:share(v) for k,v in x.items()}
  elif isinstance(x,list):x=[share(v) for v in x]
  else:return x
  return cache.setdefault(canonical(x),x)
 output.mkdir(parents=True,exist_ok=True)
 body='# GENERATED from original lovelace + i18n/'+language+'.ini; do not edit generated labels.\n'+yaml.safe_dump(share(data),allow_unicode=True,sort_keys=False,width=110)
 assert yaml.safe_load(body)==data
 assert '!include' not in body and '!file' not in body
 (output/'irrigation_dashboard.yaml').write_text(body,encoding='utf-8',newline='\n')
 (output/'irrigation_dashboard.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
 files=sorted(source.rglob('*.yaml'))
 manifest={'project':'Irrigation Garden','display_name':data['views'][0]['title'],'format_version':1,
  'build_tools':{name:sha((ROOT/'tools'/name).read_bytes()) for name in ['compile_lovelace.py','localize_lovelace.py','build_i18n_release.py','enhance_lovelace.py','decision_labels.py']},
  'target':'Original kloggy/HA-Irrigation-Version2; localized original Lovelace','language':language,'source_count':len(files),'reachable_source_count':len(used),'include_expansions':expansions,
  'source_files':[{'path':p.relative_to(candidate).as_posix(),'sha256':sha(p.read_bytes()),'normalized_text_sha256':sha(p.read_text().rstrip().encode()),'used_by_main':str(p.relative_to(source)) in used} for p in files],
  'catalogs':{name:sha((catalog_dir/name).read_bytes()) for name in sorted({'en.ini',language+'.ini'})},
  'semantic_sha256':sha(canonical(data)),'english_semantic_sha256':sha(canonical(base)),
  'generated':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in output.glob('irrigation_dashboard.*')},
  'checks':{'all_41_compiled':True,'pyyaml_roundtrip':True,'no_build_tags':True,'live_native_loader_equality':False},
  'ui_module':{'path':'custom_components/irrigation_garden/frontend/irrigation-garden-ui.js','sha256':sha((ROOT/'custom_components/irrigation_garden/frontend/irrigation-garden-ui.js').read_bytes())},
  'custom_cards':custom_types(data),'ui_enhancements':ui_report,'localization':report,'limitations':['Build-time language selection; rebuild after editing INI','Native HA dialog chrome follows HA profile language','User-defined names and all internal entity IDs, options, values, conditions and action payloads are preserved','No switch commands or engine YAML changes']}
 (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 return manifest

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--candidate',type=Path,default=ROOT);p.add_argument('--output',type=Path,default=ROOT/'generated');p.add_argument('--catalog-dir',type=Path,default=ROOT/'i18n');p.add_argument('--language')
 p.add_argument('--extract',action='store_true',help='Regenerate en.ini from source; reconcile other catalogs before building')
 a=p.parse_args()
 if a.extract:
  c=Compiler(a.candidate/'lovelace');data={'views':[c.compile(a.candidate/'lovelace/view_garden_irrigation.yaml')]};messages=extract(data);messages.update({key_for(pair[0]):pair[0] for pair in list(UI_LABELS.values())+list(DECISION_LABELS.values())});write_catalog(a.catalog_dir/'en.ini','en','English',messages);print(json.dumps({'extracted_messages':len(messages)}));return
 language=a.language
 if not language:
  config=configparser.ConfigParser(interpolation=None);config.read(a.catalog_dir/'build.ini');language=config.get('build','language',fallback='en')
 report=build(a.candidate,a.output,language,a.catalog_dir)
 print(json.dumps({'language':language,'catalog_messages':report['localization']['catalog_messages'],'fallback_keys':report['localization']['fallback_keys'],'changed_fields':report['localization']['changed_fields'],'generated':report['generated']},ensure_ascii=False))

if __name__=='__main__':main()
