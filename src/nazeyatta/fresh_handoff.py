from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .evaluator import stable_hash
from .ky_gate import KYGateResult, evaluate_ky_gate


class FreshHandoffError(ValueError):
    """A Fresh Worker handoff cannot be compiled safely."""


@dataclass(frozen=True)
class FreshHandoff:
    schema_version: str
    handoff_id: str
    classification: str
    task_id: str
    intended_action: dict[str, str]
    admitted_actions: list[dict[str, str]]
    forbidden_actions: list[dict[str, str]]
    required_hazard_ids: list[str]
    required_control_ids: list[str]
    required_stop_condition_ids: list[str]
    source_refs: dict[str, Any]
    bindings: dict[str, str]
    validity: dict[str, Any]
    authority_granted: bool


def _action_tuple(value: dict[str, Any]) -> tuple[str, str]:
    return str(value["operation"]), str(value["target"])


def _action_dict(value: tuple[str, str]) -> dict[str, str]:
    return {"operation": value[0], "target": value[1]}


def _action_set(values: list[dict[str, Any]]) -> set[tuple[str, str]]:
    return {_action_tuple(v) for v in values}


def compile_fresh_handoff(
    declaration: dict[str, Any],
    baseline: dict[str, Any],
    gate_result: KYGateResult,
    *,
    handoff_id: str,
) -> FreshHandoff:
    if not isinstance(handoff_id, str) or not handoff_id or len(handoff_id) > 128:
        raise FreshHandoffError("handoff_id must be a non-empty string up to 128 characters")

    # Re-run the deterministic gate so a forged or stale PASS result cannot be used
    # to compile a handoff for different declaration/baseline inputs.
    recomputed = evaluate_ky_gate(declaration, baseline)
    if asdict(recomputed) != asdict(gate_result):
        raise FreshHandoffError(
            "gate_result does not match deterministic evaluation of declaration and baseline"
        )

    if gate_result.outcome != "PASS":
        raise FreshHandoffError("Fresh Worker handoff requires KY Gate PASS")

    if gate_result.authority_granted is not False:
        raise FreshHandoffError("KY Gate result must not grant execution authority")

    declaration_fp = stable_hash(declaration)
    baseline_fp = stable_hash(baseline)
    if gate_result.declaration_fingerprint != declaration_fp:
        raise FreshHandoffError("declaration fingerprint mismatch")
    if gate_result.baseline_fingerprint != baseline_fp:
        raise FreshHandoffError("baseline fingerprint mismatch")

    if gate_result.task_id != declaration["task_id"] or gate_result.task_id != baseline["task_id"]:
        raise FreshHandoffError("task_id binding mismatch")
    if gate_result.declaration_id != declaration["declaration_id"]:
        raise FreshHandoffError("declaration_id binding mismatch")
    if gate_result.baseline_id != baseline["baseline_id"]:
        raise FreshHandoffError("baseline_id binding mismatch")

    worker_allowed = _action_set(declaration["understood_allowed_scope"])
    worker_forbidden = _action_set(declaration["understood_forbidden_scope"])
    baseline_allowed = _action_set(baseline["allowed_actions"])
    baseline_forbidden = _action_set(baseline["forbidden_actions"])

    # v0.1 handoff is deliberately single-action and single-bounce.
    # The gate may have validated a wider understood scope, but the next Worker
    # receives only the immediate intended action.
    intended = _action_tuple(declaration["intended_action"])
    if intended not in worker_allowed or intended not in baseline_allowed:
        raise FreshHandoffError("PASS produced no admitted intended action for handoff")
    admitted = [intended]
    forbidden = sorted(worker_forbidden | baseline_forbidden)

    source_refs = baseline["source_refs"]
    copied_source_refs = {
        "authority_ref": source_refs["authority_ref"],
        "policy_ref": source_refs["policy_ref"],
        "evidence_refs": list(source_refs["evidence_refs"]),
    }

    gate_result_dict = asdict(gate_result)

    return FreshHandoff(
        schema_version="0.1",
        handoff_id=handoff_id,
        classification="KY_VALIDATED_HANDOFF",
        task_id=gate_result.task_id,
        intended_action={
            "operation": declaration["intended_action"]["operation"],
            "target": declaration["intended_action"]["target"],
        },
        admitted_actions=[_action_dict(a) for a in admitted],
        forbidden_actions=[_action_dict(a) for a in forbidden],
        required_hazard_ids=sorted(baseline["required_hazard_ids"]),
        required_control_ids=sorted(baseline["required_control_ids"]),
        required_stop_condition_ids=sorted(baseline["required_stop_condition_ids"]),
        source_refs=copied_source_refs,
        bindings={
            "declaration_id": gate_result.declaration_id,
            "baseline_id": gate_result.baseline_id,
            "declaration_fingerprint": declaration_fp,
            "baseline_fingerprint": baseline_fp,
            "gate_result_fingerprint": stable_hash(gate_result_dict),
        },
        validity={
            "mode": "single_bounce",
            "runtime_state_bound": False,
        },
        authority_granted=False,
    )
