"""Subset JSON Schema (draft 2020-12 style) validation — stdlib only, no jsonschema dep."""
from __future__ import annotations

import re
from typing import Any

# Keywords we intentionally support; anything else on a schema object is reported.
SUPPORTED_KEYWORDS = frozenset(
    {
        "$schema",
        "$id",
        "title",
        "description",
        "default",
        "type",
        "properties",
        "required",
        "additionalProperties",
        "enum",
        "const",
        "oneOf",
        "anyOf",
        "allOf",
        "if",
        "then",
        "else",
        "items",
        "$ref",
        "$defs",
        "minLength",
        "maxLength",
        "minimum",
        "maximum",
        "minItems",
        "maxItems",
        "pattern",
        "format",
    }
)


def _unsupported_keywords(schema: dict[str, Any], path: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if not isinstance(schema, dict):
        return out
    for k in schema:
        if k in SUPPORTED_KEYWORDS:
            continue
        if k.startswith("x-"):
            continue
        out.append((f"{path}:unsupported_keyword:{k}", k))
    return out


def _resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any] | None:
    if not ref.startswith("#/"):
        return None
    cur: Any = root
    for part in ref[2:].split("/"):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur if isinstance(cur, dict) else None


def _validate_type(
    instance: Any,
    t: str,
    path: str,
    issue_code: str,
) -> list[tuple[str, str]]:
    err: list[tuple[str, str]] = []
    ok = False
    if t == "object" and isinstance(instance, dict):
        ok = True
    elif t == "array" and isinstance(instance, list):
        ok = True
    elif t == "string" and isinstance(instance, str):
        ok = True
    elif t == "integer" and type(instance) is int:
        ok = True
    elif t == "number" and isinstance(instance, (int, float)) and not isinstance(instance, bool):
        ok = True
    elif t == "boolean" and isinstance(instance, bool):
        ok = True
    elif t == "null" and instance is None:
        ok = True
    if not ok:
        err.append((issue_code, f"type {t!r} want at {path} got {type(instance).__name__}"))
    return err


def validate_instance(
    instance: Any,
    schema: dict[str, Any],
    *,
    root: dict[str, Any] | None = None,
    path: str = "$",
    issue_code: str = "V1-SCHEMA",
    strict_additional: bool = True,
) -> list[tuple[str, str]]:
    """Return list of (issue_code, detail). strict_additional enforces additionalProperties: false."""
    root = root or schema
    errors: list[tuple[str, str]] = []

    if not isinstance(schema, dict):
        return errors

    for det, kw in _unsupported_keywords(schema, path):
        errors.append(("V1-SCHEMA-UNSUPPORTED-KEYWORD", f"{det}"))

    if "$ref" in schema:
        tgt = _resolve_ref(root, str(schema["$ref"]))
        if tgt is None:
            errors.append((issue_code, f"bad $ref {schema['$ref']!r} at {path}"))
            return errors
        return validate_instance(instance, tgt, root=root, path=path, issue_code=issue_code, strict_additional=strict_additional)

    if "oneOf" in schema and isinstance(schema["oneOf"], list):
        match_count = 0
        for i, br in enumerate(schema["oneOf"]):
            if not isinstance(br, dict):
                continue
            e = validate_instance(instance, br, root=root, path=f"{path}/oneOf[{i}]", issue_code=issue_code, strict_additional=strict_additional)
            if not e:
                match_count += 1
        if match_count == 0:
            errors.append(("V1-SCHEMA-ONEOF-NO-MATCH", f"oneOf: no branch matched at {path}"))
            return errors
        if match_count > 1:
            errors.append(("V1-SCHEMA-ONEOF-MULTI-MATCH", f"oneOf: {match_count} branches matched at {path}"))
            return errors
        # exactly one branch matched — continue to sibling keywords on this schema object

    if "anyOf" in schema and isinstance(schema["anyOf"], list):
        any_ok = False
        for i, br in enumerate(schema["anyOf"]):
            if isinstance(br, dict):
                e = validate_instance(instance, br, root=root, path=f"{path}/anyOf[{i}]", issue_code=issue_code, strict_additional=strict_additional)
                if not e:
                    any_ok = True
                    break
        if not any_ok:
            errors.append(("V1-SCHEMA-ANYOF-NO-MATCH", f"anyOf: no branch matched at {path}"))
            return errors

    if "allOf" in schema and isinstance(schema["allOf"], list):
        pre_allof = len(errors)
        for i, br in enumerate(schema["allOf"]):
            if isinstance(br, dict):
                errors.extend(
                    validate_instance(instance, br, root=root, path=f"{path}/allOf[{i}]", issue_code=issue_code, strict_additional=strict_additional)
                )
        if len(errors) > pre_allof:
            return errors
        # allOf branches passed — continue to sibling keywords (type/properties/additionalProperties)

    if "if" in schema and isinstance(schema["if"], dict):
        if_errs = validate_instance(instance, schema["if"], root=root, path=f"{path}/if", issue_code=issue_code, strict_additional=strict_additional)
        if not if_errs:
            if isinstance(schema.get("then"), dict):
                errors.extend(
                    validate_instance(
                        instance,
                        schema["then"],
                        root=root,
                        path=f"{path}/then",
                        issue_code=issue_code,
                        strict_additional=strict_additional,
                    )
                )
        elif isinstance(schema.get("else"), dict):
            errors.extend(
                validate_instance(
                    instance,
                    schema["else"],
                    root=root,
                    path=f"{path}/else",
                    issue_code=issue_code,
                    strict_additional=strict_additional,
                )
            )
        return errors

    if "enum" in schema and isinstance(schema["enum"], list):
        if instance not in schema["enum"]:
            errors.append((issue_code, f"enum at {path} want one of {schema['enum']!r} got {instance!r}"))
        return errors

    if "const" in schema:
        if instance != schema["const"]:
            errors.append((issue_code, f"const at {path} want {schema['const']!r} got {instance!r}"))
        return errors

    st = schema.get("type")
    if st is None and isinstance(instance, dict) and isinstance(schema.get("properties"), dict):
        st = "object"
    if isinstance(st, list):
        branch_errs: list[list[tuple[str, str]]] = []
        for t in st:
            if not isinstance(t, str):
                continue
            e = _validate_type(instance, t, path, issue_code)
            if not e:
                return []
            branch_errs.append(e)
        errors.extend(branch_errs[0] if branch_errs else [(issue_code, f"type union fail at {path}")])
        return errors

    if isinstance(st, str):
        errors.extend(_validate_type(instance, st, path, issue_code))
        if errors:
            return errors
        if st == "object" and isinstance(instance, dict):
            props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
            req = schema.get("required") if isinstance(schema.get("required"), list) else []
            addl = schema.get("additionalProperties")
            for rk in req:
                if rk not in instance:
                    errors.append((issue_code, f"missing required {rk!r} at {path}"))
            for k, v in instance.items():
                if k in props and isinstance(props[k], dict):
                    errors.extend(
                        validate_instance(
                            v,
                            props[k],
                            root=root,
                            path=f"{path}/{k}",
                            issue_code=issue_code,
                            strict_additional=strict_additional,
                        )
                    )
                elif strict_additional and addl is False and k not in props:
                    errors.append((issue_code, f"additional property forbidden {k!r} at {path}"))
                elif isinstance(addl, dict) and k not in props:
                    errors.extend(
                        validate_instance(
                            v,
                            addl,
                            root=root,
                            path=f"{path}/{k}",
                            issue_code=issue_code,
                            strict_additional=strict_additional,
                        )
                    )
            if isinstance(schema.get("minProperties"), int) and len(instance) < int(schema["minProperties"]):
                errors.append((issue_code, f"minProperties at {path}"))
        elif st == "array" and isinstance(instance, list):
            it = schema.get("items")
            mn = schema.get("minItems")
            mx = schema.get("maxItems")
            if isinstance(mn, int) and len(instance) < mn:
                errors.append((issue_code, f"minItems at {path}"))
            if isinstance(mx, int) and len(instance) > mx:
                errors.append((issue_code, f"maxItems at {path}"))
            if isinstance(it, dict):
                for i, el in enumerate(instance):
                    errors.extend(
                        validate_instance(
                            el,
                            it,
                            root=root,
                            path=f"{path}[{i}]",
                            issue_code=issue_code,
                            strict_additional=strict_additional,
                        )
                    )
        elif st == "string" and isinstance(instance, str):
            if isinstance(schema.get("minLength"), int) and len(instance) < int(schema["minLength"]):
                errors.append((issue_code, f"minLength at {path}"))
            if isinstance(schema.get("maxLength"), int) and len(instance) > int(schema["maxLength"]):
                errors.append((issue_code, f"maxLength at {path}"))
            pat = schema.get("pattern")
            if isinstance(pat, str):
                if not re.search(pat, instance):
                    errors.append((issue_code, f"pattern mismatch at {path}"))
        elif st in ("integer", "number") and isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if "minimum" in schema and isinstance(instance, (int, float)):
                if instance < schema["minimum"]:
                    errors.append((issue_code, f"minimum at {path}"))
            if "maximum" in schema and isinstance(instance, (int, float)):
                if instance > schema["maximum"]:
                    errors.append((issue_code, f"maximum at {path}"))
    return errors
