from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import re
from typing import Any

from .evaluator import stable_hash


TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9._:/-]{0,127}$")

DECLARATION_KEYS = {
    "schema_version",
    "declaration_id",
    "task_id",
    "classification",
    "intended_action",
    "understood_allowed_scope",
    "understood_forbidden_scope",
    "recognized_hazards",
    "planned_controls",
    "stop_conditions",
    "declared_by",
    "declared_at",
}

BASELINE_KEYS = {
    "schema_version",
    "baseline_id",
    "task_id",
    "classification",
    "allowed_actions",
    "forbidden_actions",
    "required_hazard_ids",
    "required_control_ids",
    "required_stop_condition_ids",
    "source_refs",
    "prepared_by",
    "prepared_at",
}


class KYGateError(ValueError):
    """The KY declaration or validation baseline is structurally invalid."""


@dataclass(frozen=True)
class KYGateFinding:
    code: str
    effect: str
    detail: str


@dataclass(frozen=True)
class KYGateResult:
    schema_version: str
    task_id: str
    declaration_id: str
    baseline_id: str
    declaration_fingerprint: str
    baseline_fingerprint: str
    outcome: str
    findings: list[dict[str, str]]
    authority_granted: bool


def _require_mapping(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise KYGateError(f"{where} must be a mapping")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    missing = expected - actual
    extra = actual - expected
    if missing:
        raise KYGateError(f"{where} is missing required keys: {sorted(missing)!r}")
    if extra:
        raise KYGateError(f"{where} has unsupported keys: {sorted(extra)!r}")


def _require_string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise KYGateError(f"{where} must be a non-empty string")
    return value


def _require_token(value: Any, where: str) -> str:
    token = _require_string(value, where)
    if not TOKEN_RE.fullmatch(token):
        raise KYGateError(f"{where} must be a normalized lowercase token")
    return token


def _require_timestamp(value: Any, where: str) -> str:
    raw = _require_string(value, where)
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise KYGateError(f"{where} must be an ISO-8601 date-time") from exc
    if parsed.tzinfo is None:
        raise KYGateError(f"{where} must include a timezone")
    return raw


def _action(value: Any, where: str) -> tuple[str, str]:
    item = _require_mapping(value, where)
    _require_exact_keys(item, {"operation", "target"}, where)
    operation = _require_token(item.get("operation"), f"{where}.operation")
    target = _require_token(item.get("target"), f"{where}.target")
    return operation, target


def _action_set(value: Any, where: str, *, require_non_empty: bool) -> set[tuple[str, str]]:
    if not isinstance(value, list):
        raise KYGateError(f"{where} must be a list")
    if require_non_empty and not value:
        raise KYGateError(f"{where} must not be empty")
    if len(value) > 32:
        raise KYGateError(f"{where} must contain at most 32 actions")
    actions = [_action(v, f"{where}[{i}]") for i, v in enumerate(value)]
    if len(actions) != len(set(actions)):
        raise KYGateError(f"{where} contains duplicate actions")
    return set(actions)


def _ky_ids(value: Any, where: str) -> set[str]:
    if not isinstance(value, list):
        raise KYGateError(f"{where} must be a list")
    if not value:
        raise KYGateError(f"{where} must not be empty")
    if len(value) > 32:
        raise KYGateError(f"{where} must contain at most 32 items")
    ids: list[str] = []
    for i, raw in enumerate(value):
        item_where = f"{where}[{i}]"
        item = _require_mapping(raw, item_where)
        _require_exact_keys(item, {"id", "summary"}, item_where)
        ids.append(_require_token(item.get("id"), f"{item_where}.id"))
        summary = _require_string(item.get("summary"), f"{item_where}.summary")
        if len(summary) > 256:
            raise KYGateError(f"{item_where}.summary must be at most 256 characters")
    if len(ids) != len(set(ids)):
        raise KYGateError(f"{where} contains duplicate ids")
    return set(ids)


def _required_ids(value: Any, where: str) -> set[str]:
    if not isinstance(value, list):
        raise KYGateError(f"{where} must be a list")
    if len(value) > 32:
        raise KYGateError(f"{where} must contain at most 32 ids")
    ids = [_require_token(v, f"{where}[{i}]") for i, v in enumerate(value)]
    if len(ids) != len(set(ids)):
        raise KYGateError(f"{where} contains duplicate ids")
    return set(ids)


def _validate_declaration_metadata(declaration: dict[str, Any]) -> None:
    _require_exact_keys(declaration, DECLARATION_KEYS, "declaration")
    if declaration.get("schema_version") != "0.2":
        raise KYGateError("declaration.schema_version must be '0.2'")
    if declaration.get("classification") != "WORKER_SELF_REPORT":
        raise KYGateError("declaration.classification must be WORKER_SELF_REPORT")

    declared_by = _require_mapping(declaration.get("declared_by"), "declaration.declared_by")
    _require_exact_keys(declared_by, {"type", "identifier"}, "declaration.declared_by")
    if declared_by.get("type") != "worker":
        raise KYGateError("declaration.declared_by.type must be 'worker'")
    _require_string(declared_by.get("identifier"), "declaration.declared_by.identifier")
    _require_timestamp(declaration.get("declared_at"), "declaration.declared_at")


def _validate_baseline_metadata(baseline: dict[str, Any]) -> None:
    _require_exact_keys(baseline, BASELINE_KEYS, "baseline")
    if baseline.get("schema_version") != "0.1":
        raise KYGateError("baseline.schema_version must be '0.1'")
    if baseline.get("classification") != "NORMALIZED_VALIDATION_BASELINE":
        raise KYGateError(
            "baseline.classification must be NORMALIZED_VALIDATION_BASELINE"
        )

    source_refs = _require_mapping(baseline.get("source_refs"), "baseline.source_refs")
    _require_exact_keys(
        source_refs,
        {"authority_ref", "policy_ref", "evidence_refs"},
        "baseline.source_refs",
    )
    _require_string(source_refs.get("authority_ref"), "baseline.source_refs.authority_ref")
    _require_string(source_refs.get("policy_ref"), "baseline.source_refs.policy_ref")
    evidence_refs = source_refs.get("evidence_refs")
    if not isinstance(evidence_refs, list):
        raise KYGateError("baseline.source_refs.evidence_refs must be a list")
    if len(evidence_refs) > 32:
        raise KYGateError("baseline.source_refs.evidence_refs must contain at most 32 refs")
    refs = [
        _require_string(v, f"baseline.source_refs.evidence_refs[{i}]")
        for i, v in enumerate(evidence_refs)
    ]
    if len(refs) != len(set(refs)):
        raise KYGateError("baseline.source_refs.evidence_refs contains duplicates")

    prepared_by = _require_mapping(baseline.get("prepared_by"), "baseline.prepared_by")
    _require_exact_keys(prepared_by, {"type", "identifier"}, "baseline.prepared_by")
    if prepared_by.get("type") not in {"human", "adapter", "workflow"}:
        raise KYGateError(
            "baseline.prepared_by.type must be human, adapter, or workflow"
        )
    _require_string(prepared_by.get("identifier"), "baseline.prepared_by.identifier")
    _require_timestamp(baseline.get("prepared_at"), "baseline.prepared_at")


def _format_action(action: tuple[str, str]) -> str:
    return f"{action[0]}:{action[1]}"


def _format_actions(actions: set[tuple[str, str]]) -> str:
    return ", ".join(_format_action(a) for a in sorted(actions))


def _format_ids(values: set[str]) -> str:
    return ", ".join(sorted(values))


def evaluate_ky_gate(
    declaration: dict[str, Any],
    baseline: dict[str, Any],
) -> KYGateResult:
    declaration = _require_mapping(declaration, "declaration")
    baseline = _require_mapping(baseline, "baseline")

    _validate_declaration_metadata(declaration)
    _validate_baseline_metadata(baseline)

    task_id = _require_string(declaration.get("task_id"), "declaration.task_id")
    baseline_task_id = _require_string(baseline.get("task_id"), "baseline.task_id")
    declaration_id = _require_string(
        declaration.get("declaration_id"), "declaration.declaration_id"
    )
    baseline_id = _require_string(baseline.get("baseline_id"), "baseline.baseline_id")

    intended = _action(declaration.get("intended_action"), "declaration.intended_action")
    worker_allowed = _action_set(
        declaration.get("understood_allowed_scope"),
        "declaration.understood_allowed_scope",
        require_non_empty=True,
    )
    worker_forbidden = _action_set(
        declaration.get("understood_forbidden_scope"),
        "declaration.understood_forbidden_scope",
        require_non_empty=True,
    )

    worker_hazards = _ky_ids(
        declaration.get("recognized_hazards"), "declaration.recognized_hazards"
    )
    worker_controls = _ky_ids(
        declaration.get("planned_controls"), "declaration.planned_controls"
    )
    worker_stops = _ky_ids(
        declaration.get("stop_conditions"), "declaration.stop_conditions"
    )

    allowed = _action_set(
        baseline.get("allowed_actions"), "baseline.allowed_actions", require_non_empty=True
    )
    forbidden = _action_set(
        baseline.get("forbidden_actions"),
        "baseline.forbidden_actions",
        require_non_empty=False,
    )
    required_hazards = _required_ids(
        baseline.get("required_hazard_ids"), "baseline.required_hazard_ids"
    )
    required_controls = _required_ids(
        baseline.get("required_control_ids"), "baseline.required_control_ids"
    )
    required_stops = _required_ids(
        baseline.get("required_stop_condition_ids"),
        "baseline.required_stop_condition_ids",
    )

    if allowed & forbidden:
        raise KYGateError(
            "baseline allowed_actions and forbidden_actions must not overlap"
        )

    findings: list[KYGateFinding] = []

    def add(code: str, effect: str, detail: str) -> None:
        findings.append(KYGateFinding(code=code, effect=effect, detail=detail))

    if task_id != baseline_task_id:
        add(
            "TASK_ID_MISMATCH",
            "BLOCK",
            f"declaration task {task_id!r} does not match baseline task {baseline_task_id!r}",
        )

    if intended not in worker_allowed:
        add(
            "INTENT_NOT_IN_WORKER_ALLOWED_SCOPE",
            "BLOCK",
            f"intended action {_format_action(intended)} is not in the Worker's declared allowed scope",
        )

    if intended in worker_forbidden:
        add(
            "INTENT_IN_WORKER_FORBIDDEN_SCOPE",
            "BLOCK",
            f"intended action {_format_action(intended)} is also declared forbidden by the Worker",
        )

    if intended not in allowed:
        add(
            "INTENDED_ACTION_NOT_ALLOWED",
            "BLOCK",
            f"intended action {_format_action(intended)} is not allowed by the normalized baseline",
        )

    if intended in forbidden:
        add(
            "INTENDED_ACTION_FORBIDDEN",
            "BLOCK",
            f"intended action {_format_action(intended)} is explicitly forbidden by the normalized baseline",
        )

    worker_scope_excess = worker_allowed - allowed
    if worker_scope_excess:
        add(
            "WORKER_SCOPE_EXCEEDS_BASELINE",
            "BLOCK",
            "Worker claims allowed actions outside the normalized baseline: "
            + _format_actions(worker_scope_excess),
        )

    worker_scope_conflict = worker_allowed & worker_forbidden
    if worker_scope_conflict:
        add(
            "WORKER_SCOPE_SELF_CONTRADICTION",
            "BLOCK",
            "Worker declares the same action both allowed and forbidden: "
            + _format_actions(worker_scope_conflict),
        )

    unrecognized_forbidden = forbidden - worker_forbidden
    if unrecognized_forbidden:
        add(
            "FORBIDDEN_SCOPE_NOT_RECOGNIZED",
            "REVIEW",
            "Worker did not recognize baseline-forbidden actions: "
            + _format_actions(unrecognized_forbidden),
        )

    missing_hazards = required_hazards - worker_hazards
    if missing_hazards:
        add(
            "REQUIRED_HAZARD_NOT_RECOGNIZED",
            "REVIEW",
            "Worker did not recognize required hazards: " + _format_ids(missing_hazards),
        )

    missing_controls = required_controls - worker_controls
    if missing_controls:
        add(
            "REQUIRED_CONTROL_NOT_DECLARED",
            "REVIEW",
            "Worker did not declare required controls: " + _format_ids(missing_controls),
        )

    missing_stops = required_stops - worker_stops
    if missing_stops:
        add(
            "REQUIRED_STOP_CONDITION_NOT_DECLARED",
            "REVIEW",
            "Worker did not declare required stop conditions: " + _format_ids(missing_stops),
        )

    outcome = "PASS"
    if any(f.effect == "BLOCK" for f in findings):
        outcome = "BLOCK"
    elif findings:
        outcome = "REVIEW"

    return KYGateResult(
        schema_version="0.1",
        task_id=task_id,
        declaration_id=declaration_id,
        baseline_id=baseline_id,
        declaration_fingerprint=stable_hash(declaration),
        baseline_fingerprint=stable_hash(baseline),
        outcome=outcome,
        findings=[asdict(f) for f in findings],
        authority_granted=False,
    )
