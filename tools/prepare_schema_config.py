"""Prepare a local native HA schema check, never a production installation."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'tests/schema-config'
out.mkdir(parents=True,exist_ok=True)
lines=[]
for folder in ('Garden Irrigation','Logging'):
 for p in sorted((ROOT/folder).glob('*.yaml')):
  lines.append(f'  test_{p.stem}: !include "{p}"')
(out/'configuration.yaml').write_text('homeassistant:\n  packages:\n'+'\n'.join('  '+line for line in lines)+'\n')
print(out)
