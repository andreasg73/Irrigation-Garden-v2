"""Build-time localization of PRESENTATION only in original Kloggy Lovelace.

INI values are JSON strings: quotes/newlines/percent signs survive losslessly.
Existing JavaScript executes unchanged in an arrow closure; only its returned
display text is translated. Action payloads, conditions, entities and options
are never walked. No HA service calls, runtime plugin or lovelace_gen required.
"""
import ast,configparser,copy,hashlib,json,re
from pathlib import Path

DISPLAY={'name','title','label','tooltip','content','state_display','prefix','suffix'}
SKIP={'service_data','target','conditions','triggers_update','variables','options','styles','card_mod','style'}
JINJA=re.compile(r'({{.*?}}|{%.*?%}|{#.*?#})',re.S)
QUOTED=re.compile(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"")
TECH=re.compile(r'^(?:input_[a-z_]+\.|sensor\.|binary_sensor\.|script\.|timer\.|mdi:|var\(|#[0-9a-fA-F])')
RUNTIME=['SYSTEM IS OFF','SYSTEM IDLE','SYSTEM IS ON','No scheduled cycles','No cycles scheduled','No next run','Not configured','Unavailable','Unknown','Cycle1','Cycle2','Manual Cycle','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']+[f'Zone{n}' for n in range(1,17)]
LITERAL_SKIP={'active','off','on','undefined','s','m','h','Cycle','at','of events'}
RUNTIME.extend(['NOTHING SCHEDULED','Watering...','Changing Zone...','STOP: output not confirmed OFF','mins','unknown','unavailable','NO SCHEDULE TODAY OR TOMORROW','Tomorrow','cycle','secs','January','February','March','April','May','June','July','August','September','October','November','December','Today','Use Forecast','Use Actual','Use Highest','Cancelled',' Cycle'])
CLASH_TEXT=['You have set ', ' to start at the same time as ', ' to start before ', ' has ended.', ' will not run.', 'No timing errors found! Please check code...']
ROW_LABELS={
 'input_boolean.irrigation_disable_switches':'Disable Switches',
 'input_boolean.irrigation_rainfall_use_rolling_values':'Use Rolling Rainfall Totals',
 'input_number.logging_irrigation_days_to_keep':'Days to keep',
 'input_select.irrigation_high_temp_options':'High Temperature Source',
 'input_text.irrigation_external_sensor_rainfall_last_twenty_four_hours':'Last 24 hours',
 **{f'input_text.irrigation_external_sensor_rainfall_between_{a}_and_{b}_hours_ago':label for a,b,label in [('24','48','24 to 48 hours ago'),('48','72','48 to 72 hours ago'),('72','96','72 to 96 hours ago'),('96','120','96 to 120 hours ago')]}}

def key_for(text):
 slug=re.sub('[^a-z0-9]+','_',text.lower()).strip('_')[:60] or 'text'
 return slug+'__'+hashlib.sha256(text.encode()).hexdigest()[:8]

def meaningful(s):
 return bool(re.search('[A-Za-z]',s)) and not TECH.search(s) and not re.match(r'^[\w-]+\s*:[^;]+;',s) and bool(re.sub('<[^>]*>','',s).strip())

def extract(data):
 out=set()
 def scan(value):
  if value.lstrip().startswith('[[[') or value.lstrip().startswith('${'):
   for m in QUOTED.finditer(value):
    try:s=ast.literal_eval(m.group()).strip()
    except (ValueError,SyntaxError):continue
    if meaningful(s) and not s.startswith('_') and s not in LITERAL_SKIP and not re.fullmatch(r'(zone|cycle)\d+',s):out.add(s)
  elif '{{' in value or '{%' in value:
   for s in JINJA.split(value):
    if not s.startswith(('{{','{%','{#')) and meaningful(s.strip()):out.add(s.strip())
  elif meaningful(value.strip()):out.add(value.strip())
 def walk(x):
  if isinstance(x,dict):
   for k,v in x.items():
    if k in SKIP:continue
    if k=='custom_fields' and isinstance(v,dict):
     for field in v.values():
      if isinstance(field,str):scan(field)
      else:walk(field)
    elif k in DISPLAY and isinstance(v,str):scan(v)
    else:walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(data);out.update(RUNTIME);out.update(CLASH_TEXT);out.update(ROW_LABELS.values())
 # Fragments consist of display text returned by the original callbacks.
 out.update(['Cycle','at','of events','Hour and','Hours and','Minute','Minutes','SCHEDULE','Seconds (testing mode)'])
 return {key_for(s):s for s in sorted(out)}

def write_catalog(path,language,native,messages):
 p=configparser.ConfigParser(interpolation=None);p.optionxform=str
 p['meta']={'language':language,'native_name':native,'fallback':'en','format':'1'}
 p['messages']={k:json.dumps(v,ensure_ascii=False) for k,v in messages.items()}
 with Path(path).open('w',encoding='utf-8') as f:
  f.write('; Values are JSON strings. Preserve technical IDs, HTML tags and units.\n')
  p.write(f)

def read_catalog(path):
 p=configparser.ConfigParser(interpolation=None,strict=True);p.optionxform=str
 with Path(path).open(encoding='utf-8-sig') as f:p.read_file(f)
 if p.get('meta','format')!='1':raise ValueError('Unsupported catalog format')
 out={}
 for k,v in p['messages'].items():
  value=json.loads(v)
  if not isinstance(value,str):raise ValueError('Translation must be a string: '+k)
  out[k]=value
 return dict(p['meta']),out

def validate(base,translated):
 extra=set(translated)-set(base)
 if extra:raise ValueError('Unknown translation keys: '+str(sorted(extra)))
 for k,value in translated.items():
  src=base[k]
  if any(x in value for x in ['{{','{%','{#','[[[','${']):raise ValueError('Template delimiters in translation: '+k)
  if re.findall(r'<[^>]+>',src)!=re.findall(r'<[^>]+>',value):raise ValueError('HTML markup changed: '+k)
  ids=lambda s:sorted(re.findall(r'\b(?:input_[a-z_]+|sensor|binary_sensor|script|timer)\.[a-zA-Z0-9_\[\], ]+',s))
  if ids(src)!=ids(value):raise ValueError('Technical references changed: '+k)

def literal_replace(value,pairs):
 if not pairs:return value
 mapping=dict(pairs)
 parts=[]
 for src in sorted(mapping,key=len,reverse=True):
  a=r'(?<!\w)' if src and (src[0].isalnum() or src[0]=='_') else ''
  b=r'(?!\w)' if src and (src[-1].isalnum() or src[-1]=='_') else ''
  parts.append(a+re.escape(src)+b)
 return re.sub('|'.join(parts),lambda m:mapping[m.group()],value)

def js_return_wrapper(body,pairs,expression=False):
 # Protect custom helper names (and their uppercase forms). Stock defaults are
 # presentation labels; all other user-supplied names remain byte-for-byte.
 protect="""const locks=[];
const ids=['input_text.irrigation_cycle1_name','input_text.irrigation_cycle2_name','input_text.irrigation_cycle3_name','input_text.irrigation_previous_run_cycle_name','input_text.irrigation_notification_user1_name','input_text.irrigation_notification_user2_name'];
for(let z=1;z<=16;z++)ids.push('input_text.irrigation_zone'+z+'_name');
if(typeof states==='object')for(const id of ids){
 if(!Object.prototype.hasOwnProperty.call(states,id))continue;const e=states[id];
 let n=e?.state;if(id==='input_text.irrigation_previous_run_cycle_name'&&typeof n==='string')n=n.replace(/ \\(Cancelled\\)$/,'');
 if(typeof n!=='string'||!n||['unknown','unavailable'].includes(n)||/^(Cycle[12]|Manual Cycle|Zone\\d+)$/.test(n))continue;
 locks.push(n,n.toUpperCase());
}
for(const n of [...new Set(locks)].sort((a,b)=>b.length-a.length)){if(n&&text.includes(n)){const token='\\uE000'+saved.length+'\\uE001';saved.push([token,n]);text=text.split(n).join(token);}}
"""
 table=json.dumps(sorted(pairs,key=lambda p:len(p[0]),reverse=True),ensure_ascii=False,separators=(',',':'))
 original=('('+body+')') if expression else '(()=>{'+body+'})()'
 result="const value="+original+";if(typeof value!=='string')return value;let text=value;const saved=[];"+protect
 result+='const pairs='+table+";const esc=s=>s.replace(/[.*+?^$()|[\\]\\\\]/g,'\\\\$&').replace(/[{}]/g,'\\\\$&');const word=c=>/^[\\p{L}\\p{N}_]$/u.test(c);"
 result+="if(pairs.length){const map=new Map(pairs);const pattern=pairs.map(([s])=>(word(s[0])?'(?<![\\\\p{L}\\\\p{N}_])':'')+esc(s)+(word(s[s.length-1])?'(?![\\\\p{L}\\\\p{N}_])':'')).join('|');text=text.replace(new RegExp(pattern,'gu'),s=>map.get(s));}"
 result+="for(const [token,n]of saved)text=text.split(token).join(n);return text;"
 return result

def localize(data,language,catalog_dir):
 catalog_dir=Path(catalog_dir)
 if not re.fullmatch(r'[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*',language):raise ValueError('Invalid language code')
 meta,base=read_catalog(catalog_dir/'en.ini');expected=extract(data)
 if base!=expected:raise ValueError('Source catalog is stale; regenerate en.ini and reconcile translations')
 selected_meta,override=read_catalog(catalog_dir/(language+'.ini'))
 if selected_meta.get('language')!=language:raise ValueError('Catalog language metadata does not match filename')
 validate(base,override)
 missing=sorted(set(base)-set(override));merged={**base,**override}
 if language=='en':return copy.deepcopy(data),{'language':'en','catalog_messages':len(base),'fallback_keys':[],'changed_fields':0}
 pairs=[(src,merged[k]) for k,src in base.items() if merged[k]!=src]
 # Uppercase names are rendered by the original cards, not stored in helpers.
 allpairs=dict(pairs)
 for a,b in pairs:
  if a in RUNTIME:allpairs.setdefault(a.upper(),b.upper())
 pairs=list(allpairs.items());changes=[]
 def display(v,path):
  stripped=v.strip()
  if stripped.startswith('[[[') and stripped.endswith(']]]'):
   body=stripped[3:-3];selected=[(a,b) for a,b in pairs if a in body or a in RUNTIME or a in [x.upper() for x in RUNTIME]]
   return '[[[\n'+js_return_wrapper(body,selected)+'\n]]]'
  if stripped.startswith('${') and stripped.endswith('}'):
   body=stripped[2:-1];selected=[(a,b) for a,b in pairs if a in body or a in RUNTIME]
   return '${ (()=>{'+js_return_wrapper(body,selected,True)+'})() }'
  if '{{' in v or '{%' in v:
   parts=JINJA.split(v)
   def translate_part(p):
    if p.startswith('{{') and 'clash_text' in p:
     # Only this displayed backend sentence is localized. Its original
     # expression is evaluated once; user-defined cycle names are protected.
     expression=p[2:-2].strip()
     names=['input_text.irrigation_cycle1_name','input_text.irrigation_cycle2_name']
     result='{% set ig_clash = namespace(text=('+expression+') | default("", true), names=[]) %}'
     for i,name in enumerate(names):
      token='\uE100'+str(i)+'\uE101'
      result+='{% set ig_name = states('+json.dumps(name)+') %}'
      result+='{% if ig_name not in ["", "unknown", "unavailable"] %}{% set ig_clash.names = ig_clash.names + [('+json.dumps(token)+', ig_name)] %}{% set ig_clash.text = ig_clash.text | replace(ig_name, '+json.dumps(token)+') %}{% endif %}'
     for phrase in CLASH_TEXT:
      result+='{% set ig_clash.text = ig_clash.text | replace('+json.dumps(phrase)+', '+json.dumps(merged[key_for(phrase)],ensure_ascii=False)+') %}'
     result+='{% for token, name in ig_clash.names %}{% set ig_clash.text = ig_clash.text | replace(token, name) %}{% endfor %}{{ ig_clash.text }}'
     return result
    return p if p.startswith(('{{','{%','{#')) else literal_replace(p,pairs)
   return ''.join(translate_part(p) for p in parts)
  return literal_replace(v,pairs)
 def walk(x,path=''):
  if isinstance(x,dict):
   out={}
   for k,v in x.items():
    if k in SKIP:out[k]=copy.deepcopy(v)
    elif k=='custom_fields' and isinstance(v,dict):
     out[k]={}
     for field,text in v.items():
      out[k][field]=display(text,path+'/custom_fields/'+field) if isinstance(text,str) else walk(text,path+'/custom_fields/'+field)
      if out[k][field]!=text:changes.append(path+'/custom_fields/'+field)
    elif k in DISPLAY and isinstance(v,str):
     out[k]=display(v,path+'/'+k)
     if out[k]!=v:changes.append(path+'/'+k)
    else:out[k]=walk(v,path+'/'+k)
   if path.rsplit('/',2)[-2:-1]==['entities'] and not x.get('type') and 'name' not in x and x.get('entity') in ROW_LABELS:
    label=ROW_LABELS[x['entity']];out['name']=merged[key_for(label)];changes.append(path+'/name')
   if x.get('type')=='custom:button-card' and x.get('show_state') and 'state_display' not in x and x.get('entity') in ['input_text.irrigation_current_status','input_select.irrigation_high_temp_options','sensor.irrigation_weather_outlook']:
    out['state_display']='[[[\n'+js_return_wrapper('return entity?.state;',pairs)+'\n]]]';changes.append(path+'/state_display')
   return out
  if isinstance(x,list):return [walk(v,path+'/'+str(i)) for i,v in enumerate(x)]
  return x
 localized=walk(data)
 return localized,{'language':language,'catalog_messages':len(base),'translated_messages':len(override),'fallback_keys':missing,'changed_fields':len(changes),'changed_paths':changes}

