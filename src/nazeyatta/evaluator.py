from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

OUTCOME_RANK = {
    "PASS": 0,
    "CAUTION": 1,
    "REVIEW": 2,
    "EVIDENCE_REQUIRED": 3,
    "BLOCK": 4,
}

# Effects a policy may assign to a *failed* requirement or an applicable rule.
# "PASS" is deliberately excluded: a policy must not be able to convert missing,
# stale, or invalid evidence into a pass (that would be a fail-open configuration).
POLICY_EFFECTS = {"CAUTION", "REVIEW", "EVIDENCE_REQUIRED", "BLOCK"}

EVIDENCE_STATES = {"VERIFIED", "PRESENT", "STALE", "INVALID", "MISSING", "UNKNOWN"}

EVIDENCE_LANES = ("legacy-v0.1", "provenance-v0.2")


class PolicyError(ValueError):
    """The policy bundle is malformed. Raised instead of silently weakening a rule."""


@dataclass(frozen=True)
class Finding:
    rule_id: str
    title: str
    hazard: str
    evidence_key: str | None
    evidence_state: str | None
    effect: str
    reason: str


@dataclass(frozen=True)
class Receipt:
    schema_version: str
    task_fingerprint: str
    policy_bundle_fingerprint: str
    evaluator_version: str
    outcome: str
    findings: list[dict[str, Any]]
    authority_granted: bool
    evidence_lane: str


# Input-size guards. Task and policy files are small by design; anything past these limits is
# treated as malformed input rather than something to evaluate (deep nesting would otherwise end
# in a RecursionError while fingerprinting).
MAX_INPUT_BYTES = 1_048_576
MAX_NESTING_DEPTH = 64
MAX_NODES = 100_000


def _check_shape(data: Any, path: str) -> None:
    """Reject pathological nesting/size without recursion (explicit stack)."""
    stack: list[tuple[Any, int]] = [(data, 0)]
    nodes = 0
    while stack:
        value, depth = stack.pop()
        nodes += 1
        if nodes > MAX_NODES:
            raise ValueError(f"{path}: too many nodes (> {MAX_NODES})")
        if depth > MAX_NESTING_DEPTH:
            raise ValueError(f"{path}: nesting deeper than {MAX_NESTING_DEPTH} levels")
        if isinstance(value, dict):
            for k, v in value.items():
                if not isinstance(k, (str, bool, int, float)) or k is None:
                    raise ValueError(f"{path}: unsupported mapping key {k!r}")
                stack.append((v, depth + 1))
        elif isinstance(value, (list, tuple)):
            stack.extend((v, depth + 1) for v in value)
        elif isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
            raise ValueError(f"{path}: NaN/Infinity values are not allowed")


def load_yaml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if p.is_file() and p.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError(f"{path}: file larger than {MAX_INPUT_BYTES} bytes")
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping in {path}")
    _check_shape(data, str(path))
    return data


def _json_default(value: Any) -> str:
    # YAML parses unquoted timestamps/dates into datetime objects. Fingerprints must
    # stay deterministic for such inputs instead of crashing with a TypeError.
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(f"unsupported value in fingerprint payload: {type(value).__name__}")


def _canonical(value: Any) -> Any:
    # Mapping keys become strings so that sort_keys cannot fail on mixed key types
    # (an unquoted YAML `on:` key is the boolean True, `1:` is an int, ...).
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    return value


def stable_hash(value: Any) -> str:
    # allow_nan=False: NaN/Infinity have no canonical JSON form, so they cannot be part of a
    # deterministic fingerprint. They are rejected as malformed input instead.
    payload = json.dumps(_canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                         default=_json_default, allow_nan=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _legacy_state(value: Any) -> str:
    """Normalise a v0.1 scalar evidence value to a canonical state, conservatively.

    Only ASCII strings are case-folded (``verified`` -> ``VERIFIED``). Anything else — non-string
    values, non-ASCII look-alikes (Turkish dotless i, full-width letters), embedded whitespace or
    zero-width characters — becomes ``INVALID`` rather than being coerced by ``str().upper()``.
    """
    if value is None:
        return "UNKNOWN"
    if not isinstance(value, str) or not value.isascii():
        return "INVALID"
    state = value.upper()
    return state if state in EVIDENCE_STATES else "INVALID"


def _accepted_states(rule_id: Any, req: dict[str, Any]) -> set[str]:
    raw = req.get("accepted_states", ["VERIFIED"])
    if not isinstance(raw, (list, tuple)) or not raw:
        raise PolicyError(f"rule {rule_id!r}: 'accepted_states' must be a non-empty list")
    out = set()
    for s in raw:
        if not isinstance(s, str) or not s.isascii() or s.upper() not in EVIDENCE_STATES:
            raise PolicyError(f"rule {rule_id!r}: unknown accepted state {s!r}")
        out.add(s.upper())
    return out


def _get(data: dict[str, Any], dotted: str) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _condition_matches(task: dict[str, Any], cond: dict[str, Any]) -> bool:
    if not isinstance(cond, dict) or "field" not in cond:
        raise PolicyError(f"condition must be a mapping with a 'field': {cond!r}")
    field = cond["field"]
    if not isinstance(field, str) or not field:
        raise PolicyError(f"condition 'field' must be a non-empty dotted string, got {field!r}")
    actual = _get(task, field)
    if "equals" in cond:
        return actual == cond["equals"]
    if "not_equals" in cond:
        return actual != cond["not_equals"]
    if "in" in cond:
        allowed = cond["in"]
        if isinstance(allowed, (str, bytes)) or not isinstance(allowed, (list, tuple, set)):
            # `in: write` would otherwise do substring matching against a string.
            raise PolicyError(f"'in' for field {field!r} must be a list, got {type(allowed).__name__}")
        return actual in allowed
    if "exists" in cond:
        expected_exists = cond["exists"]
        if not isinstance(expected_exists, bool):
            raise PolicyError(
                f"'exists' for field {field!r} must be a boolean, got {type(expected_exists).__name__}"
            )
        exists = actual is not None
        return exists is expected_exists
    raise PolicyError(f"unsupported condition: {cond}")


def _rule_matches(task: dict[str, Any], rule: dict[str, Any]) -> bool:
    when = rule.get("when", {})
    if not isinstance(when, dict):
        raise PolicyError(f"rule {rule.get('id')!r}: 'when' must be a mapping")
    unknown = set(when) - {"all", "any"}
    if unknown:
        # A typo such as `alll:` must not silently turn the rule into "applies to everything".
        raise PolicyError(f"rule {rule.get('id')!r}: unsupported selector(s) {sorted(unknown)!r} in 'when'")
    if "all" in when:
        return all(_condition_matches(task, c) for c in when["all"])
    if "any" in when:
        return any(_condition_matches(task, c) for c in when["any"])
    return True


def _policy_effect(rule_id: Any, value: Any, where: str) -> str:
    if not isinstance(value, str) or value not in POLICY_EFFECTS:
        raise PolicyError(
            f"rule {rule_id!r}: {where} effect must be one of {sorted(POLICY_EFFECTS)}, got {value!r}"
        )
    return value


def _effect_map(rule_id: Any, req: dict[str, Any]) -> dict[str, Any]:
    if "on" in req:
        effect_map = req["on"]
    elif True in req:
        # YAML 1.1 parses an unquoted `on:` key as the boolean True. Accept it instead of
        # silently dropping the whole map (which would weaken BLOCK to the default effect).
        effect_map = req[True]
    else:
        effect_map = {}
    if not isinstance(effect_map, dict):
        raise PolicyError(f"rule {rule_id!r}: 'on' must be a mapping of evidence state -> effect")
    return effect_map


def _evidence_lane(task: dict[str, Any]) -> str:
    """Select a supported input lane without silently downgrading explicit versions."""
    if task.get("schema_version") == "0.2":
        return "provenance-v0.2"
    if task.get("schema_version") in (None, "0.1"):
        return "legacy-v0.1"
    hint = " (write it as a quoted string, e.g. \"0.2\")" if isinstance(task.get("schema_version"), (int, float)) else ""
    raise ValueError(f"unsupported schema_version: {task.get('schema_version')!r}{hint}")


def _is_offset_datetime(value: Any) -> bool:
    """Accept ISO-8601 date-times with a timezone using only the standard library."""
    if isinstance(value, datetime):
        # An unquoted YAML timestamp is already parsed; it still needs a timezone.
        return value.tzinfo is not None
    if not isinstance(value, str) or "T" not in value:
        return False
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return datetime.fromisoformat(normalized).tzinfo is not None
    except ValueError:
        return False


def _v02_effective_state(
    evidence: dict[str, Any], evidence_records: Any, claim_key: str
) -> tuple[str, str | None]:
    """Resolve a v0.2 claim reference without treating malformed provenance as verified."""
    reference = evidence.get(claim_key)
    if reference is None:
        return "MISSING", "no Evidence Record ID was supplied"
    if not isinstance(reference, str) or not reference:
        return "INVALID", "Evidence Record ID must be a non-empty string"
    if not isinstance(evidence_records, dict):
        return "INVALID", "evidence_records must be a mapping in schema_version 0.2"

    record = evidence_records.get(reference)
    if record is None:
        return "MISSING", f"referenced Evidence Record {reference!r} does not exist"
    if not isinstance(record, dict):
        return "INVALID", f"Evidence Record {reference!r} must be a mapping"
    if record.get("evidence_id") != reference:
        return "INVALID", "evidence_id must match its evidence_records map key"
    if record.get("supports_claim") != claim_key:
        return "INVALID", f"supports_claim must equal {claim_key!r}"
    if not _is_offset_datetime(record.get("observed_at")):
        return "INVALID", "observed_at must be an ISO-8601 date-time with a timezone"
    observer = record.get("observer")
    if not isinstance(observer, dict) or not isinstance(observer.get("type"), str) or not observer["type"]:
        return "INVALID", "observer.type is required for provenance-qualified evidence"
    verification = record.get("verification")
    state = verification.get("state") if isinstance(verification, dict) else None
    if not isinstance(state, str) or state not in EVIDENCE_STATES:
        return "INVALID", "verification.state must be an allowed, uppercase evidence state"
    return state, None


def evaluate(task: dict[str, Any], policies: dict[str, Any], evaluator_version: str = "0.1.0a1") -> Receipt:
    evidence = task.get("evidence", {})
    if not isinstance(evidence, dict):
        raise ValueError("task.evidence must be a mapping")

    lane = _evidence_lane(task)
    evidence_records = task.get("evidence_records")
    rules = policies.get("rules", [])
    if not isinstance(rules, list):
        raise PolicyError("'rules' must be a list")
    findings: list[Finding] = []
    for rule in rules:
        if not isinstance(rule, dict):
            raise PolicyError(f"rule must be a mapping, got {type(rule).__name__}")
        missing = [k for k in ("id", "title", "hazard") if k not in rule]
        if missing:
            raise PolicyError(f"rule {rule.get('id')!r}: missing required key(s) {missing}")
        if not _rule_matches(task, rule):
            continue

        requires = rule.get("requires", [])
        if not requires:
            effect = _policy_effect(rule["id"], rule.get("effect", "CAUTION"), "'effect'")
            findings.append(Finding(
                rule_id=rule["id"],
                title=rule["title"],
                hazard=rule["hazard"],
                evidence_key=None,
                evidence_state=None,
                effect=effect,
                reason=rule.get("reason", "applicable rule"),
            ))
            continue

        for req in requires:
            if not isinstance(req, dict) or "evidence" not in req:
                raise PolicyError(f"rule {rule['id']!r}: each 'requires' entry needs an 'evidence' key")
            key = req["evidence"]
            if lane == "provenance-v0.2":
                state, resolution_error = _v02_effective_state(evidence, evidence_records, key)
            else:
                # v0.1 remains accepted for compatibility, but these scalar assertions are
                # not provenance-qualified Evidence Records.
                state = _legacy_state(evidence.get(key))
                resolution_error = None
            accepted = _accepted_states(rule["id"], req)
            if state in accepted:
                continue
            effect_map = _effect_map(rule["id"], req)
            effect = _policy_effect(
                rule["id"],
                effect_map.get(state.lower(), effect_map.get("default", "EVIDENCE_REQUIRED")),
                f"'on' ({state.lower()})",
            )
            findings.append(Finding(
                rule_id=rule["id"],
                title=rule["title"],
                hazard=rule["hazard"],
                evidence_key=key,
                evidence_state=state,
                effect=effect,
                reason=resolution_error or req.get("reason", f"required evidence {key} is {state}"),
            ))

    outcome = "PASS"
    for finding in findings:
        if OUTCOME_RANK[finding.effect] > OUTCOME_RANK[outcome]:
            outcome = finding.effect

    return Receipt(
        schema_version="0.2",
        task_fingerprint=stable_hash({k: v for k, v in task.items() if k != "receipt"}),
        policy_bundle_fingerprint=stable_hash(policies),
        evaluator_version=evaluator_version,
        outcome=outcome,
        findings=[asdict(f) for f in findings],
        authority_granted=False,
        evidence_lane=lane,
    )
