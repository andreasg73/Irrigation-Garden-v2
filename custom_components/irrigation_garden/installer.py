"""Prepare original YAML packages without modifying HA config or entity state.

No network, HA services, shell commands, .storage edits, or automatic activation.
The only activation point is the user's explicit package include + HA restart.
"""
from __future__ import annotations

from contextlib import suppress
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
from threading import RLock
from zipfile import BadZipFile, ZipFile

import yaml

from .const import INSTALL_DIR, VERSION

_PREPARE_LOCK = RLock()


class InstallError(ValueError):
    """Unsafe input, modified managed files, or an incomplete payload."""


def validate_choices(language: str, dashboard_url: str) -> None:
    import re
    if language not in {"en", "pl"}:
        raise InstallError("Unsupported language")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)+", dashboard_url):
        raise InstallError("Dashboard URL must be a hyphenated lowercase slug")


def _checked_path(root: Path, relative: str) -> Path:
    part = PurePosixPath(relative)
    if part.is_absolute() or not part.parts or any(p in {".", ".."} for p in part.parts) or "\\" in relative:
        raise InstallError("Unsafe path")
    candidate = root.joinpath(*part.parts)
    current = root
    for component in part.parts:
        current /= component
        if current.is_symlink():
            raise InstallError("Symlink in installation path")
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise InstallError("Path escapes installation root")
    return candidate


def read_payload(bundle: Path) -> tuple[dict, dict[str, bytes]]:
    """Read only a bounded, allowlisted ZIP; never extract archive paths."""
    try:
        return _read_payload(bundle)
    except (BadZipFile, KeyError, TypeError, UnicodeError, RuntimeError) as err:
        raise InstallError("Invalid installation bundle") from err


def _read_payload(bundle: Path) -> tuple[dict, dict[str, bytes]]:
    with ZipFile(bundle) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or len(names) != 33:
            raise InstallError("Unexpected bundle member count")
        if sum(x.file_size for x in archive.infolist()) > 20_000_000:
            raise InstallError("Oversized bundle")
        manifest = json.loads(archive.read("manifest.json"))
        expected = manifest["files"]
        if set(names) != set(expected) | {"manifest.json"}:
            raise InstallError("Bundle manifest mismatch")
        engine = {p for p in expected if p.startswith(("Garden Irrigation/", "Logging/"))}
        if len(engine) != 29 or {p for p in expected if p.startswith("dashboard/")} != {"dashboard/en.yaml", "dashboard/pl.yaml"}:
            raise InstallError("Bundle is missing the original engine or languages")
        if set(expected) - engine != {"dashboard/en.yaml", "dashboard/pl.yaml", "dependencies.json"}:
            raise InstallError("Unexpected bundle content")
        result = {}
        for name, digest in expected.items():
            _checked_path(Path("/payload"), name)
            info = archive.getinfo(name)
            if info.file_size > 10_000_000 or sum(x.file_size for x in archive.infolist()) > 20_000_000:
                raise InstallError("Oversized bundle")
            body = archive.read(name)
            if hashlib.sha256(body).hexdigest() != digest:
                raise InstallError("Bundle checksum mismatch: " + name)
            result[name] = body
        return manifest, result


def merge_engine(files: dict[str, bytes]) -> dict:
    """Merge top-level original package domains, rejecting conflicting IDs."""
    merged: dict = {}
    for name in sorted(files):
        if not name.startswith(("Garden Irrigation/", "Logging/")):
            continue
        package = yaml.safe_load(files[name])
        if not isinstance(package, dict):
            raise InstallError("Invalid engine package")
        for domain, config in package.items():
            if config is None:
                continue
            if isinstance(config, list):
                if domain in merged and not isinstance(merged[domain], list):
                    raise InstallError("Conflicting domain types")
                merged.setdefault(domain, []).extend(config)
            elif isinstance(config, dict):
                if domain in merged and not isinstance(merged[domain], dict):
                    raise InstallError("Conflicting domain types")
                target = merged.setdefault(domain, {})
                for key, value in config.items():
                    if key in target:
                        raise InstallError("Duplicate engine ID: " + str(key))
                    target[key] = value
            else:
                raise InstallError("Unsupported engine domain")
    return merged


def _atomic_write(path: Path, data: bytes) -> None:
    """Same-filesystem atomic replacement; don't follow existing symlinks."""
    if path.is_symlink():
        raise InstallError("Symlink destination")
    fd, temporary = tempfile.mkstemp(prefix=".prepare-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        with suppress(FileNotFoundError):
            os.unlink(temporary)


def prepare(config_dir: str, bundle: Path, language: str, dashboard_url: str) -> dict:
    """Serialize staging requests from configuration and options flows."""
    with _PREPARE_LOCK:
        return _prepare(config_dir, bundle, language, dashboard_url)


def _prepare(config_dir: str, bundle: Path, language: str, dashboard_url: str) -> dict:
    """Stage immutable content, then atomically replace ONE include pointer.

    Existing unknown files and edited releases are never overwritten. Older
    releases and previous include pointers remain available for manual rollback.
    No effect on a running engine until HA reloads its YAML configuration.
    """
    validate_choices(language, dashboard_url)
    manifest, files = read_payload(bundle)
    root = Path(config_dir).resolve()
    install = _checked_path(root, INSTALL_DIR)
    install.mkdir(mode=0o700, exist_ok=True)
    marker = _checked_path(install, "installation.json")
    pointer = _checked_path(install, "package.yaml")
    previous = marker.read_text() if marker.exists() else None
    if previous is None and any(install.iterdir()):
        raise InstallError("Installation directory is not owned by this installer")
    old = json.loads(previous) if previous else None
    if old and old.get("owner") != "irrigation_garden":
        raise InstallError("Installation directory belongs to another owner")
    allowed_pointers = {old.get("pointer_sha256"), old.get("previous_pointer_sha256")} if old else set()
    if pointer.exists() and hashlib.sha256(pointer.read_bytes()).hexdigest() not in allowed_pointers:
        raise InstallError("Managed include pointer was edited; preserve it manually")

    fingerprint = hashlib.sha256(bundle.read_bytes() + language.encode() + dashboard_url.encode()).hexdigest()[:20]
    release_relative = "releases/" + fingerprint
    release = _checked_path(install, release_relative)
    package = merge_engine(files)
    package.setdefault("input_text", {})["irrigation_garden_package_release"] = {
        "name": "Irrigation Garden installed package release", "max": 64, "initial": fingerprint,
    }
    if "lovelace" in package:
        raise InstallError("Original packages unexpectedly define Lovelace")
    package["lovelace"] = {"dashboards": {dashboard_url: {
        "mode": "yaml", "title": "Podlewanie Ogrodu" if language == "pl" else "Irrigation Garden",
        "icon": "mdi:sprinkler-variant", "show_in_sidebar": True, "require_admin": True,
        "filename": f"{INSTALL_DIR}/{release_relative}/dashboard.yaml",
    }}}
    generated = {"package.yaml": yaml.safe_dump(package, allow_unicode=True, sort_keys=False, width=110).encode(),
                 "dashboard.yaml": files["dashboard/" + language + ".yaml"],
                 "payload-manifest.json": json.dumps(manifest, indent=2).encode()}
    generated.update({"original/" + p: b for p, b in files.items() if p.startswith(("Garden Irrigation/", "Logging/"))})
    # Validate every destination BEFORE any write and preflight edited releases.
    for name, body in generated.items():
        dest = _checked_path(release, name)
        if dest.exists() and dest.read_bytes() != body:
            raise InstallError("Existing release contains edited files: " + name)
    install_manifest = {"owner": "irrigation_garden", "version": VERSION, "language": language,
                        "dashboard_url": dashboard_url, "release": release_relative}
    pointer_body = ('!include "' + release_relative + '/package.yaml"\n').encode()
    install_manifest["pointer_sha256"] = hashlib.sha256(pointer_body).hexdigest()
    if pointer.exists():
        install_manifest["previous_pointer_sha256"] = hashlib.sha256(pointer.read_bytes()).hexdigest()
    # Marker makes an interrupted first preparation recognizable, without activation.
    # The active pointer is the sole commit point and is always written last.
    if not marker.exists():
        _atomic_write(marker, json.dumps({"owner": "irrigation_garden"}).encode())
    for name, body in generated.items():
        dest = _checked_path(release, name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            _atomic_write(dest, body)
    if pointer.exists() and pointer.read_bytes() != pointer_body:
        backups = _checked_path(install, "previous")
        backups.mkdir(exist_ok=True)
        backup = _checked_path(backups, hashlib.sha256(pointer.read_bytes()).hexdigest() + ".yaml")
        if not backup.exists():
            _atomic_write(backup, pointer.read_bytes())
    # Both known pointers are recorded before commit. An interrupted replacement
    # can be retried without accepting arbitrary user-edited include content.
    _atomic_write(marker, (json.dumps(install_manifest, indent=2) + "\n").encode())
    _atomic_write(pointer, pointer_body)
    return install_manifest
