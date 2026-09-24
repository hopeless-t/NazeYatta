from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any

from .evaluator import Receipt, evaluate, stable_hash
from .fresh_handoff import FreshHandoff
from .reky_gate import validate_boundary_observation_for_handoff


class PreflightRuntimeCorrelationError(ValueError):
    """Exact preflight/runtime artifacts could not be correlated safely."""


@dataclass(frozen=True)
class PreflightRuntimeCorrelationRecord:
    schema_version: str
    classification: str
    task_id: str
    receipt_fingerprint: str
    task_fingerprint: str
    policy_bundle_fingerprint: str
    handoff_fingerprint: str
    boundary_observation_fingerprint: str
    target_binding: dict[str, str]
    observed_at: str
    correlation_outcome: str
    semantic_equivalence_verified: bool
    freshness_verified: bool
    authority_granted: bool


def build_preflight_runtime_correlation(
    receipt: Receipt,
    task: dict[str, Any],
    policies: dict[str, Any],
    handoff: FreshHandoff,
    observation: dict[str, Any],
) -> PreflightRuntimeCorrelationRecord:
    """Bind exact preflight and runtime artifacts without claiming freshness.

    Exact Receipt recomputation prevents a stale/forged Receipt object from being
    associated with unrelated Task/Policy inputs. Shared task_id correlation and
    handoff-bound observation validation then bind the runtime-side artifacts.

    This does not prove semantic equivalence between the generic preflight Task and
    the KY handoff, and does not prove current freshness.
    """
    if not isinstance(receipt, Receipt):
        raise PreflightRuntimeCorrelationError("receipt must be a Receipt")
    if not isinstance(task, dict):
        raise PreflightRuntimeCorrelationError("task must be a mapping")
    if not isinstance(policies, dict):
        raise PreflightRuntimeCorrelationError("policies must be a mapping")
    if not isinstance(handoff, FreshHandoff):
        raise PreflightRuntimeCorrelationError("handoff must be a FreshHandoff")

    try:
        recomputed = evaluate(
            task,
            policies,
            evaluator_version=receipt.evaluator_version,
        )
    except (TypeError, ValueError) as exc:
        raise PreflightRuntimeCorrelationError(
            f"preflight inputs could not be re-evaluated: {exc}"
        ) from exc

    if asdict(recomputed) != asdict(receipt):
        raise PreflightRuntimeCorrelationError(
            "receipt does not exactly match deterministic evaluation of task and policies"
        )

    task_id = task.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise PreflightRuntimeCorrelationError("task.task_id must be a non-empty string")
    if task_id != handoff.task_id:
        raise PreflightRuntimeCorrelationError(
            "preflight task_id does not correlate with handoff task_id"
        )

    try:
        checked_observation = validate_boundary_observation_for_handoff(
            handoff,
            observation,
        )
    except ValueError as exc:
        raise PreflightRuntimeCorrelationError(
            f"boundary observation does not bind to handoff: {exc}"
        ) from exc

    if checked_observation["task_id"] != task_id:
        raise PreflightRuntimeCorrelationError(
            "boundary observation task_id does not correlate with preflight task_id"
        )

    target_binding = deepcopy(checked_observation["target_binding"])

    return PreflightRuntimeCorrelationRecord(
        schema_version="0.1",
        classification="PREFLIGHT_RUNTIME_CORRELATION",
        task_id=task_id,
        receipt_fingerprint=stable_hash(asdict(receipt)),
        task_fingerprint=receipt.task_fingerprint,
        policy_bundle_fingerprint=receipt.policy_bundle_fingerprint,
        handoff_fingerprint=checked_observation["handoff_fingerprint"],
        boundary_observation_fingerprint=stable_hash(checked_observation),
        target_binding=target_binding,
        observed_at=checked_observation["observed_at"],
        correlation_outcome="EXACT_ARTIFACTS_BOUND",
        semantic_equivalence_verified=False,
        freshness_verified=False,
        authority_granted=False,
    )
