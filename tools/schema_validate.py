"""Run native HA check_config AND require clean stderr (JSON may underreport templates)."""
import json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
proc=subprocess.run([sys.executable,'-m','homeassistant','--script','check_config','-c',str(root/'tests/schema-config'),'--json'],capture_output=True,text=True)
try:data=json.loads(proc.stdout)
except ValueError:data={'parse_error':proc.stdout}
errors=[line for line in proc.stderr.splitlines() if 'ERROR:' in line or 'Invalid config' in line or 'Traceback' in line]
report={'exit_code':proc.returncode,'native_json':data,'stderr_errors':errors,'stderr':proc.stderr,'passed':proc.returncode==0 and data.get('total_errors')==0 and not errors}
(root/'tests/schema_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'passed':report['passed'],'native_errors':data.get('total_errors'),'stderr_errors':len(errors)}))
if not report['passed']:raise SystemExit(1)
