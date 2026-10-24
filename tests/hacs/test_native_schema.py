"""Validate the actual include chain with HA's complete check_config command."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from custom_components.irrigation_garden.installer import prepare

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("language", ["en", "pl"])
def test_native_package_configuration(tmp_path, language):
    prepare(str(tmp_path), ROOT / "custom_components/irrigation_garden/bundle.zip", language, "irrigation-garden")
    # An unrelated package survives the same include mapping used on migration.
    (tmp_path / "unrelated.yaml").write_text("input_boolean:\n  retained_weather_adapter: {}\n")
    (tmp_path / "configuration.yaml").write_text(
        "homeassistant:\n  packages:\n"
        "    retained_weather: !include unrelated.yaml\n"
        "    irrigation_garden: !include irrigation_garden/package.yaml\n"
    )
    result = subprocess.run([sys.executable, "-m", "homeassistant", "--script", "check_config", "-c", str(tmp_path), "--json"], capture_output=True, text=True, timeout=240)
    assert result.returncode == 0, result.stderr + result.stdout
    report = json.loads(result.stdout)
    assert report["total_errors"] == report["total_warnings"] == 0, report
    assert "lovelace" in report["components"] and "script" in report["components"]
    assert not any(word in result.stderr for word in ("ERROR:", "Invalid config", "Traceback")), result.stderr
