"""Offline publication gates: source paths, generated consistency and private artifacts."""
import hashlib,json,re
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
canonical=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
packages=[]
for folder in ('Garden Irrigation','Logging'):
 for p in sorted((ROOT/folder).glob('*.yaml')):
  assert isinstance(yaml.safe_load(p.read_text()),dict),p
  packages.append(p)
assert len(packages)==29,len(packages)
assert len(list((ROOT/'lovelace').rglob('*.yaml')))==41
registry=(ROOT/'installation/packages.yaml').read_text()
targets=re.findall(r'!include "([^"]+)"',registry)
assert len(targets)==29
expected={str(p.relative_to(ROOT)) for p in packages}
assert {p.removeprefix('/config/irrigation_garden_v2/') for p in targets}==expected
for lang in ('en','pl'):
 out=ROOT/'dist'/lang
 data=json.loads((out/'irrigation_dashboard.json').read_text())
 assert yaml.safe_load((out/'irrigation_dashboard.yaml').read_text())==data
 manifest=json.loads((out/'manifest.json').read_text())
 assert manifest['semantic_sha256']==hashlib.sha256(canonical(data)).hexdigest()
 assert manifest['source_count']==41 and manifest['language']==lang
 assert sha(ROOT/manifest['ui_module']['path'])==manifest['ui_module']['sha256']
 assert manifest['ui_enhancements']['section_wrappers']==3 and manifest['ui_enhancements']['picker_rows']>0
 for row in manifest['source_files']:
  assert sha(ROOT/row['path'])==row['sha256'],row['path']
 for name,digest in manifest['catalogs'].items():assert sha(ROOT/'i18n'/name)==digest
 for name,digest in manifest['build_tools'].items():assert sha(ROOT/'tools'/name)==digest
 for name,row in manifest['generated'].items():assert sha(out/name)==row['sha256']
 assert data['views'][0]['title']==('Irrigation Garden' if lang=='en' else 'Podlewanie Ogrodu')
private=re.compile(r'(?i)(?:192\.168\.1\.|Bearer\s+[A-Za-z0-9._-]{16,}|eyJhbGci[A-Za-z0-9._-]+|kloggy_test_zawor|irrigation_v2_workbench|libfile_[a-z0-9]+)')
checked=0
for p in ROOT.rglob('*'):
 if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts:continue
 rel=p.relative_to(ROOT)
 if p.name=='check_publication.py':continue
 if rel.parts[0]=='tests' and len(rel.parts)>1 and rel.parts[1]!='fixtures':continue
 assert p.name not in ('secrets.yaml','home-assistant.log'),rel
 if p.suffix in ('.yaml','.ini','.json','.py','.js','.cjs','.md','.txt'):
  assert not private.search(p.read_text()),rel
  checked+=1
print(json.dumps({'package_yaml':29,'authoring_yaml':41,'languages':['en','pl'],'hashes_and_roundtrips':'passed','files_privacy_scanned':checked}))
