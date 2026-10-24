#!/usr/bin/env python3
"""Offline converter of kloggy's parameterized Lovelace !includes to plain JSON.
Requires PyYAML + Jinja2. Does not access HA, devices, or automations.
WARNING: generated panel requires compatible custom cards and engine entities.
"""
import argparse
import json
from pathlib import Path
import jinja2
import yaml

class BuildError(Exception):
    pass

class Compiler:
    def __init__(self, root):
        self.root = root.resolve(strict=True)
        self.env = jinja2.Environment(undefined=jinja2.StrictUndefined,
                                       autoescape=False, keep_trailing_newline=True)
        self.loaded = []
    def compile(self, path, args=None, parents=()):
        path = path.resolve(strict=True)
        if path != self.root and self.root not in path.parents:
            raise BuildError("Include outside root: " + str(path))
        if path in parents or len(parents) > 80:
            raise BuildError("Recursive/deep include: " + str(path))
        try:
            raw = path.read_text(encoding="utf-8")
            source = self.env.from_string(raw).render(**(args or {})) if raw.splitlines()[0].lower().startswith("# lovelace_gen") else raw
        except (OSError, jinja2.TemplateError) as e:
            raise BuildError(f"Jinja in {path}: {e}") from e
        compiler = self
        class Loader(yaml.SafeLoader):
            pass
        def include(loader, node):
            if isinstance(node, yaml.ScalarNode):
                name, params = loader.construct_scalar(node), {}
            elif isinstance(node, yaml.SequenceNode):
                items = loader.construct_sequence(node, deep=True)
                if not items or not isinstance(items[0], str) or any(not isinstance(x, dict) for x in items[1:]):
                    raise BuildError("Malformed !include in " + str(path))
                name, params = items[0], {}
                for entry in items[1:]:
                    params.update(entry)
            else:
                raise BuildError("Unsupported !include in " + str(path))
            return compiler.compile(path.parent / name, params, (*parents, path))
        def file_ref(loader, node):
            if not isinstance(node, yaml.ScalarNode):
                raise BuildError("Unsupported !file in " + str(path))
            return loader.construct_scalar(node)
        Loader.add_constructor("!include", include)
        Loader.add_constructor("!file", file_ref)
        try:
            result = yaml.load(source, Loader=Loader)
        except yaml.YAMLError as e:
            raise BuildError(f"YAML in {path}: {e}") from e
        self.loaded.append(str(path.relative_to(self.root)))
        return result

def custom_types(obj):
    found = set()
    def walk(item):
        if isinstance(item, dict):
            for key in ("type", "card_type", "row_type"):
                if isinstance(item.get(key), str) and item[key].startswith("custom:"):
                    found.add(item[key])
            for value in item.values():
                walk(value)
        elif isinstance(item, list):
            for value in item:
                walk(value)
    walk(obj)
    return sorted(found)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True, help="Original lovelace/ directory")
    p.add_argument("--entry", default="view_garden_irrigation.yaml")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    compiler = Compiler(args.source)
    view = compiler.compile(args.source / args.entry)
    if not isinstance(view, dict) or "sections" not in view:
        raise BuildError("Expected original irrigation view with sections")
    data = {"views": [view]}
    body = json.dumps(data, ensure_ascii=False, indent=2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(body + "\n", encoding="utf-8")
    report = {"files": compiler.loaded, "files_count": len(compiler.loaded),
              "custom_cards_required": custom_types(data), "output": str(args.output),
              "note": "No HA deployment. Requires frontend and card compatibility tests."}
    if args.report:
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

