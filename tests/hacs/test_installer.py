"""Installer boundaries: original content, activation, recovery and native HA YAML."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest
from homeassistant.util.yaml import load_yaml

from custom_components.irrigation_garden import installer

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "custom_components/irrigation_garden/bundle.zip"


def stage(tmp_path, language="pl"):
    return installer.prepare(str(tmp_path), BUNDLE, language, "irrigation-garden")


def test_original_engine_and_dashboard_are_exact(tmp_path):
    result = stage(tmp_path)
    release = tmp_path / "irrigation_garden" / result["release"]
    originals = list((release / "original").rglob("*.yaml"))
    assert len(originals) == 29
    for path in originals:
        assert path.read_bytes() == (ROOT / path.relative_to(release / "original")).read_bytes()
    assert (release / "dashboard.yaml").read_bytes() == (ROOT / "dist/pl/irrigation_dashboard.yaml").read_bytes()
    package = load_yaml(str(tmp_path / "irrigation_garden/package.yaml"))
    _, files = installer.read_payload(BUNDLE)
    original = installer.merge_engine(files)
    marker = package["input_text"].pop("irrigation_garden_package_release")
    dashboard = package.pop("lovelace")["dashboards"]["irrigation-garden"]
    assert package == original
    assert marker["initial"] == result["release"].split("/")[-1]
    assert (tmp_path / dashboard["filename"]).is_file()


def test_idempotent_and_no_existing_configuration_changes(tmp_path):
    for path in ("configuration.yaml", ".storage/core.restore_state", "private/weather.yaml"):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("existing user configuration\n")
    before = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    first = stage(tmp_path)
    snapshot = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in (tmp_path / "irrigation_garden/releases").rglob("*") if p.is_file()}
    second = stage(tmp_path)
    assert second["release"] == first["release"]
    assert all((tmp_path / p).read_bytes() == body for p, body in before.items())
    assert snapshot == {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in (tmp_path / "irrigation_garden/releases").rglob("*") if p.is_file()}


def test_language_change_retains_previous_release_and_pointer(tmp_path):
    old = stage(tmp_path)
    pointer = tmp_path / "irrigation_garden/package.yaml"
    old_pointer = pointer.read_bytes()
    new = stage(tmp_path, "en")
    assert new["release"] != old["release"]
    assert (tmp_path / "irrigation_garden" / old["release"] / "dashboard.yaml").is_file()
    assert list((tmp_path / "irrigation_garden/previous").glob("*.yaml"))[0].read_bytes() == old_pointer
    assert load_yaml(str(pointer))["lovelace"]["dashboards"]["irrigation-garden"]["title"] == "Irrigation Garden"


@pytest.mark.parametrize("target", ["package.yaml", "release"])
def test_modified_managed_files_are_preserved(tmp_path, target):
    result = stage(tmp_path)
    path = tmp_path / "irrigation_garden" / ("package.yaml" if target == "package.yaml" else result["release"] + "/package.yaml")
    path.write_text("user modification\n")
    with pytest.raises(installer.InstallError):
        stage(tmp_path)
    assert path.read_text() == "user modification\n"


@pytest.mark.parametrize("relative", ["irrigation_garden", "irrigation_garden/releases"])
def test_symlink_escape_is_rejected(tmp_path, relative):
    outside = tmp_path / "outside"
    outside.mkdir()
    target = tmp_path / relative
    target.parent.mkdir(exist_ok=True)
    if relative.endswith("releases"):
        (target.parent / "installation.json").write_text('{"owner":"irrigation_garden"}')
    target.symlink_to(outside, target_is_directory=True)
    with pytest.raises(installer.InstallError):
        stage(tmp_path)
    assert not list(outside.iterdir())


def test_unknown_directory_is_preserved(tmp_path):
    target = tmp_path / "irrigation_garden"
    target.mkdir()
    (target / "user.txt").write_text("keep")
    with pytest.raises(installer.InstallError):
        stage(tmp_path)
    assert list(target.iterdir()) == [target / "user.txt"]


@pytest.mark.parametrize("language,url", [("de", "irrigation-garden"), ("pl", "../escape"), ("en", "nohyphen")])
def test_invalid_choices_create_nothing(tmp_path, language, url):
    with pytest.raises(installer.InstallError):
        installer.prepare(str(tmp_path), BUNDLE, language, url)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("fault", ["checksum", "traversal", "invalid_zip", "missing_manifest"])
def test_corrupt_payload_does_not_stage(tmp_path, fault):
    bundle = tmp_path / "bad.zip"
    if fault == "invalid_zip":
        bundle.write_bytes(b"not zip")
    else:
        with ZipFile(BUNDLE) as source:
            files = {p: source.read(p) for p in source.namelist()}
        if fault == "checksum":
            files["dashboard/pl.yaml"] += b"changed"
        elif fault == "missing_manifest":
            files["other.json"] = files.pop("manifest.json")
        else:
            manifest = json.loads(files["manifest.json"])
            body = files.pop("dependencies.json")
            del manifest["files"]["dependencies.json"]
            manifest["files"]["../outside.yaml"] = hashlib.sha256(body).hexdigest()
            files["../outside.yaml"] = body
            files["manifest.json"] = json.dumps(manifest).encode()
        with ZipFile(bundle, "w") as archive:
            for name, body in files.items():
                archive.writestr(name, body)
    with pytest.raises(installer.InstallError):
        installer.prepare(str(tmp_path), bundle, "pl", "irrigation-garden")
    assert not (tmp_path / "irrigation_garden").exists()


def test_interrupted_update_keeps_complete_old_activation(tmp_path, monkeypatch):
    stage(tmp_path)
    pointer = tmp_path / "irrigation_garden/package.yaml"
    before = pointer.read_bytes()
    write = installer._atomic_write

    def fail_commit(path, data):
        if path == pointer:
            raise OSError("injected disk failure at commit")
        write(path, data)

    monkeypatch.setattr(installer, "_atomic_write", fail_commit)
    with pytest.raises(OSError):
        stage(tmp_path, "en")
    assert pointer.read_bytes() == before
    assert load_yaml(str(pointer))["lovelace"]["dashboards"]["irrigation-garden"]["title"] == "Podlewanie Ogrodu"
    monkeypatch.setattr(installer, "_atomic_write", write)
    recovered = stage(tmp_path, "en")
    assert recovered["language"] == "en"
    assert load_yaml(str(pointer))["lovelace"]["dashboards"]["irrigation-garden"]["title"] == "Irrigation Garden"


def test_duplicate_original_entity_ids_fail_before_activation():
    with pytest.raises(installer.InstallError):
        installer.merge_engine({"Garden Irrigation/a.yaml": b"script: {same: {}}", "Logging/b.yaml": b"script: {same: {}}"})
