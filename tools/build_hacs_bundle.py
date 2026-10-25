"""Build a deterministic HACS payload from the SAME published original engine/UI."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
component = ROOT / "custom_components/irrigation_garden"
files = {p.relative_to(ROOT).as_posix(): p.read_bytes() for folder in ("Garden Irrigation", "Logging") for p in sorted((ROOT/folder).glob("*.yaml"))}
assert len(files) == 29
for language in ("en", "pl"):
    files["dashboard/" + language + ".yaml"] = (ROOT/"dist"/language/"irrigation_dashboard.yaml").read_bytes()
files["dependencies.json"] = (ROOT/"dependencies.json").read_bytes()
manifest = {"format": 1, "upstream": "kloggy/HA-Irrigation-Version2", "files": {name: hashlib.sha256(body).hexdigest() for name, body in sorted(files.items())}}
files["manifest.json"] = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
with ZipFile(component / "bundle.zip", "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
    for name, body in sorted(files.items()):
        info = ZipInfo(name, date_time=(2026, 10, 24, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, body)
print(json.dumps({"files": len(files), "bytes": (component/"bundle.zip").stat().st_size, "sha256": hashlib.sha256((component/"bundle.zip").read_bytes()).hexdigest()}))
