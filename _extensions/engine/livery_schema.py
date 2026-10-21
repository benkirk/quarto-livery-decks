"""livery.yml's schema (livery.schema.json beside this file): validation for livery_build.py, and the
reference document generated from it.

    livery schema --doc [-o FILE]   write the reference (default liveries/REFERENCE.md)
    livery schema --doc --check     exit 1 if the committed reference is not the schema's

A livery.yml is checked as written, before `extends` merges its parent's, so a flavor names only
what it changes; nothing is required but `schema` and `name`. Of _brand.yml (the brand.yml
standard) only what the engine reads is checked. Errors read `<file>: <path>: <message>`.
"""

import json
import sys
from pathlib import Path

import jsonschema

HERE = Path(__file__).resolve().parent
SCHEMA = HERE / "livery.schema.json"
SCHEMAS = (1,)   # the schema numbers this engine reads
REFERENCE = HERE.parent.parent / "liveries" / "REFERENCE.md"
YAML_TYPES = {"array": "a list", "object": "a mapping", "string": "a string", "number": "a number",
              "integer": "a whole number", "boolean": "true or false", "null": "null"}


def load() -> dict:
    return json.loads(SCHEMA.read_text())


def _path(e: jsonschema.ValidationError) -> str:
    return ".".join(str(p) for p in e.absolute_path)


def _short(v) -> str:
    r = repr(v)
    return r if len(r) <= 40 else r[:37] + "..."


def _message(e: jsonschema.ValidationError) -> tuple[str, str]:
    """(path, message) in the livery's terms."""
    if e.validator in ("oneOf", "anyOf") and e.context:   # the branch the value meant: its own error
        inner = [c for c in e.context if c.validator != "type"]
        if inner:
            return _message(min(inner, key=lambda c: len(c.relative_schema_path)))
    path = _path(e)
    if e.validator == "additionalProperties":   # one line per unknown key, with its full path
        extra = sorted(set(e.instance) - set(e.schema.get("properties", {})))
        return ", ".join(f"{path}.{k}" if path else k for k in extra), "unknown key"
    if e.validator == "required":
        return path or "(top)", e.message.replace("is a required property", "is required")
    if e.validator == "const" and path == "schema":
        return path, f"{e.instance!r} is not a schema this engine reads ({', '.join(map(str, SCHEMAS))})"
    if e.validator == "pattern" and e.schema.get("$ref") is None:
        desc = e.schema.get("description")
        return path, f"{e.instance!r} is not {desc[0].lower() + desc[1:].rstrip('.') if desc else 'valid'}"
    if e.validator in ("oneOf", "anyOf"):
        return path, f"{_short(e.instance)} is not {e.schema.get('description', 'valid').rstrip('.')}"
    if e.validator in ("minItems", "maxItems"):
        lo, hi = e.schema.get("minItems"), e.schema.get("maxItems")
        want = f"{lo}" if lo == hi else f"at least {lo}" if hi is None else f"at most {hi}" if lo is None else f"{lo} to {hi}"
        return path, f"has {len(e.instance)} item{'s' * (len(e.instance) != 1)}, not {want}"
    if e.validator == "type":
        want = e.validator_value if isinstance(e.validator_value, list) else [e.validator_value]
        return path, f"{_short(e.instance)} is not {' or '.join(YAML_TYPES.get(t, t) for t in want)}"
    return path or "(top)", e.message.replace(repr(e.instance), _short(e.instance))


def check(knobs: dict, brand: dict, where: Path) -> list[str]:
    """Errors in a livery's livery.yml (knobs) and _brand.yml (brand), as `<file>: <path>: <message>`."""
    schema = load()
    # through JSON, as the schema sees it: YAML's integer keys (charts.sets) become strings
    knobs, brand = json.loads(json.dumps(knobs)), json.loads(json.dumps(brand))
    out = []
    for name, data, sch in (("livery.yml", knobs, schema),
                            ("_brand.yml", brand, {**schema["$defs"]["brand"], "$defs": schema["$defs"]})):
        v = jsonschema.Draft202012Validator(sch)
        for e in sorted(v.iter_errors(data), key=lambda e: (list(map(str, e.absolute_path)), e.validator)):
            path, msg = _message(e)
            out.append(f"{where / name}: {path}: {msg}")
    return out


# --- the reference -------------------------------------------------------------------------------

def _resolve(node: dict, schema: dict) -> dict:
    """The node with its $ref's target merged under it (the node's own keys win)."""
    while "$ref" in node:
        target = schema["$defs"][node["$ref"].rsplit("/", 1)[1]]
        node = {**target, **{k: v for k, v in node.items() if k != "$ref"}}
    return node


KINDS = {"color": "color", "color-or-role": "color or role", "role": "role", "role-or-hex": "role or hex",
         "path": "path", "image": "image", "box": "box"}   # $defs shown by their kind, not their JSON type


def _type(node: dict, schema: dict) -> str:
    if node.get("$ref", "").rsplit("/", 1)[-1] in KINDS:
        return KINDS[node["$ref"].rsplit("/", 1)[1]]
    node = _resolve(node, schema)
    if "x-kind" in node:   # the schema's own wording for a shape the walk would garble
        return node["x-kind"]
    if "enum" in node:
        return " \\| ".join(f"`{v}`" for v in node["enum"])
    if "const" in node:
        return f"`{node['const']}`"
    if "oneOf" in node:
        return " or ".join(_type(n, schema) for n in node["oneOf"])
    t = node.get("type", "")
    if isinstance(t, list):
        return " or ".join(t)
    if t == "number" and node.get("minimum") == 0 and node.get("maximum") == 1:
        return "fraction"
    if t == "array":
        n = node.get("minItems"), node.get("maxItems")
        items = _type(node.get("items", {}), schema) if isinstance(node.get("items"), dict) else ""
        count = f"{n[0]} " if n[0] is not None and n[0] == n[1] else ""
        return f"list of {count}{items}s".rstrip() if items and " " not in items else f"list of {count}{items}".rstrip()
    if t == "object" and "additionalProperties" in node and isinstance(node["additionalProperties"], dict):
        return "map"
    return t


def _default(node: dict, schema: dict) -> str:
    node = _resolve(node, schema)
    return "" if "default" not in node else f"`{json.dumps(node['default'])}`"


def _tables(path: str, node: dict, schema: dict, out: list):
    node = _resolve(node, schema)
    props = node.get("properties", {})
    extra = node.get("additionalProperties")
    if not props and not isinstance(extra, dict):
        return
    out += [f"### `{path}`" if path else "### The top level", ""]
    if node.get("description") and path:   # the top's is the page's introduction
        out += [node["description"], ""]
    out += ["| key | type | default | |", "|---|---|---|---|"]
    rows, nested = [], []
    for k, v in props.items():
        r = _resolve(v, schema)
        desc = r.get("x-slide") or r.get("description", "")   # a composition is described by its slide
        rows.append(f"| `{k}` | {_type(v, schema)} | {_default(v, schema)} | {desc} |")
        if "properties" in r or isinstance(r.get("additionalProperties"), dict):
            nested.append((f"{path}.{k}" if path else k, v))
        elif path == "compositions.<name>":   # a part, null or an object: the object's keys get a table
            obj = next((o for o in r.get("oneOf", []) if "properties" in o), None)
            if obj:
                nested.append((f"{path}.{k}", obj))
    if isinstance(extra, dict):
        key = node.get("x-key", "<name>")
        r = _resolve(extra, schema)
        rows.append(f"| `{key}` | {_type(extra, schema)} | {_default(extra, schema)} | {r.get('description', '')} |")
        if "properties" in r:
            nested.append((f"{path}.{key}" if path else key, extra))
    out += rows + [""]
    for p, v in nested:
        if path == "compositions":   # every composition has the same parts: one table stands for them all
            if p != "compositions.title":
                continue
            p = "compositions.<name>"
        _tables(p, v, schema, out)


def doc() -> str:
    schema = load()
    out = ["# livery.yml reference", "",
           "<!-- GENERATED by `livery schema --doc` from _extensions/engine/livery.schema.json; do not edit. -->", "",
           schema["description"], "",
           "Each file starts with the schema it is written for, and its first line lets an editor check it as you type:", "",
           "```yaml", "# yaml-language-server: $schema=../../_extensions/engine/livery.schema.json", "schema: 1",
           "name: mybrand", "```", "",
           "Value kinds: a *color* is a `_brand.yml` palette name or a `#RRGGBB` hex; a *role* is a role name "
           "(`roles` below); an *image* is a `_brand.yml` `logo.images` name; a *path* is relative to the livery; "
           "a *fraction* is of the slide's height unless the key says width. A key left out takes its default, "
           "or its parent's in a flavor.", ""]
    _tables("", schema, schema, out)
    return "\n".join(out).rstrip() + "\n"


def write_doc(output: Path = REFERENCE, check: bool = False) -> int:
    """Write the reference to output, or with check compare it; 1 when it is stale."""
    text = doc()
    if check:
        if not output.exists() or output.read_text() != text:
            print(f"stale: {output} (run livery schema --doc)")
            return 1
        print(f"{output}: current")
    else:
        output.write_text(text)
        print(f"wrote {output}")
    return 0
