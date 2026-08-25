from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
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


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping in {path}")
    return data


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _get(data: dict[str, Any], dotted: str) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _condition_matches(task: dict[str, Any], cond: dict[str, Any]) -> bool:
    field = cond["field"]
    actual = _get(task, field)
    if "equals" in cond:
        return actual == cond["equals"]
    if "not_equals" in cond:
        return actual != cond["not_equals"]
    if "in" in cond:
        return actual in cond["in"]
    if "exists" in cond:
        exists = actual is not None
        return exists is bool(cond["exists"])
    raise ValueError(f"unsupported condition: {cond}")


def _rule_matches(task: dict[str, Any], rule: dict[str, Any]) -> bool:
    when = rule.get("when", {})
    if "all" in when:
        return all(_condition_matches(task, c) for c in when["all"])
    if "any" in when:
        return any(_condition_matches(task, c) for c in when["any"])
    return True


def evaluate(task: dict[str, Any], policies: dict[str, Any], evaluator_version: str = "0.1.0a1") -> Receipt:
    evidence = task.get("evidence", {})
    if not isinstance(evidence, dict):
        raise ValueError("task.evidence must be a mapping")

    findings: list[Finding] = []
    for rule in policies.get("rules", []):
        if not _rule_matches(task, rule):
            continue

        requires = rule.get("requires", [])
        if not requires:
            effect = rule.get("effect", "CAUTION")
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
            key = req["evidence"]
            state = str(evidence.get(key, "UNKNOWN")).upper()
            accepted = {s.upper() for s in req.get("accepted_states", ["VERIFIED"])}
            if state in accepted:
                continue
            effect_map = req.get("on", {})
            effect = effect_map.get(state.lower(), effect_map.get("default", "EVIDENCE_REQUIRED"))
            findings.append(Finding(
                rule_id=rule["id"],
                title=rule["title"],
                hazard=rule["hazard"],
                evidence_key=key,
                evidence_state=state,
                effect=effect,
                reason=req.get("reason", f"required evidence {key} is {state}"),
            ))

    outcome = "PASS"
    for finding in findings:
        if OUTCOME_RANK[finding.effect] > OUTCOME_RANK[outcome]:
            outcome = finding.effect

    return Receipt(
        schema_version="0.1",
        task_fingerprint=stable_hash({k: v for k, v in task.items() if k != "receipt"}),
        policy_bundle_fingerprint=stable_hash(policies),
        evaluator_version=evaluator_version,
        outcome=outcome,
        findings=[asdict(f) for f in findings],
        authority_granted=False,
    )
