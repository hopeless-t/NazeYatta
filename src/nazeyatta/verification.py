from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime
import re
from typing import Any

from .evaluator import stable_hash


VERIFICATION_OUTCOMES = {
    "VERIFIED_SUCCESS",
    "VERIFIED_FAILURE",
    "UNKNOWN",
}
OBSERVATION_STATES = {"OBSERVED", "UNKNOWN"}
OBSERVER_TYPES = {"human", "adapter", "workflow"}

REQUEST_KEYS = {
    "schema_version",
    "classification",
    "verification_id",
    "task_id",
    "preflight_receipt_fingerprint",
    "task_fingerprint",
    "action_fingerprint",
    "target_binding",
    "expected_facts",
    "authority_granted",
}
OBSERVATION_KEYS = {
    "schema_version",
    "classification",
    "observation_id",
    "verification_id",
    "task_id",
    "preflight_receipt_fingerprint",
    "task_fingerprint",
    "action_fingerprint",
    "target_binding",
    "observed_facts",
    "observed_by",
    "observed_at",
    "authority_granted",
}

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
TOKEN_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
TARGET_KIND_RE = re.compile(r"^[a-z0-9][a-z0-9._:/-]{0,127}$")

MAX_FACTS = 64
MAX_TEXT = 1024


class VerificationError(ValueError):
    """Post-action artifacts cannot be verified safely."""


@dataclass(frozen=True)
class VerificationReason:
    code: str
    fact_id: str
    expected: str | bool | int
    observation_state: str
    observed: str | bool | int | None


@dataclass(frozen=True)
class VerificationReceipt:
    schema_version: str
    classification: str
    verification_id: str
    task_id: str
    request_fingerprint: str
    observation_fingerprint: str
    preflight_receipt_fingerprint: str
    task_fingerprint: str
    action_fingerprint: str
    target_binding_fingerprint: str
    outcome: str
    reasons: list[dict[str, Any]]
    authority_granted: bool
    retry_authorized: bool


def _mapping(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise VerificationError(f"{where} must be a mapping")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    missing = expected - actual
    extra = actual - expected
    if missing:
        raise VerificationError(f"{where} is missing required keys: {sorted(missing)!r}")
    if extra:
        raise VerificationError(f"{where} has unsupported keys: {sorted(extra)!r}")


def _string(value: Any, where: str, *, max_len: int = 256) -> str:
    if not isinstance(value, str) or not value:
        raise VerificationError(f"{where} must be a non-empty string")
    if len(value) > max_len:
        raise VerificationError(f"{where} must be at most {max_len} characters")
    return value


def _fingerprint(value: Any, where: str) -> str:
    raw = _string(value, where, max_len=71)
    if not SHA256_RE.fullmatch(raw):
        raise VerificationError(f"{where} must be a sha256: fingerprint")
    return raw


def _fact_id(value: Any, where: str) -> str:
    raw = _string(value, where, max_len=64)
    if not TOKEN_RE.fullmatch(raw):
        raise VerificationError(
            f"{where} must match [a-z][a-z0-9_.-]{{0,63}}"
        )
    return raw


def _scalar(value: Any, where: str) -> str | bool | int:
    if type(value) not in (str, bool, int):
        raise VerificationError(
            f"{where} must be a string, boolean, or integer"
        )
    if isinstance(value, str) and len(value) > MAX_TEXT:
        raise VerificationError(f"{where} must be at most {MAX_TEXT} characters")
    return value


def _target_binding(value: Any, where: str) -> dict[str, str]:
    item = _mapping(value, where)
    _exact_keys(item, {"kind", "identifier", "identity_fingerprint"}, where)

    kind = _string(item.get("kind"), f"{where}.kind", max_len=128)
    if not TARGET_KIND_RE.fullmatch(kind):
        raise VerificationError(f"{where}.kind must be a normalized lowercase token")

    identifier = _string(item.get("identifier"), f"{where}.identifier")
    identity_fingerprint = _fingerprint(
        item.get("identity_fingerprint"), f"{where}.identity_fingerprint"
    )
    return {
        "kind": kind,
        "identifier": identifier,
        "identity_fingerprint": identity_fingerprint,
    }


def _expected_facts(value: Any, where: str) -> dict[str, str | bool | int]:
    facts = _mapping(value, where)
    if not facts:
        raise VerificationError(f"{where} must contain at least one fact")
    if len(facts) > MAX_FACTS:
        raise VerificationError(f"{where} must contain at most {MAX_FACTS} facts")

    out: dict[str, str | bool | int] = {}
    for raw_id, raw_value in facts.items():
        fact_id = _fact_id(raw_id, f"{where} fact id")
        if fact_id in out:
            raise VerificationError(f"{where} contains duplicate fact id {fact_id!r}")
        out[fact_id] = _scalar(raw_value, f"{where}.{fact_id}")
    return out


def _observed_fact(value: Any, where: str) -> dict[str, Any]:
    item = _mapping(value, where)
    _exact_keys(item, {"observation_state", "value"}, where)
    state = _string(item.get("observation_state"), f"{where}.observation_state", max_len=16)
    if state not in OBSERVATION_STATES:
        raise VerificationError(
            f"{where}.observation_state must be OBSERVED or UNKNOWN"
        )

    raw_value = item.get("value")
    if state == "UNKNOWN":
        if raw_value is not None:
            raise VerificationError(f"{where}.value must be null when state is UNKNOWN")
        return {"observation_state": state, "value": None}

    if raw_value is None:
        raise VerificationError(f"{where}.value must be present when state is OBSERVED")
    return {
        "observation_state": state,
        "value": _scalar(raw_value, f"{where}.value"),
    }


def _observed_facts(value: Any, where: str) -> dict[str, dict[str, Any]]:
    facts = _mapping(value, where)
    if len(facts) > MAX_FACTS:
        raise VerificationError(f"{where} must contain at most {MAX_FACTS} facts")

    out: dict[str, dict[str, Any]] = {}
    for raw_id, raw_value in facts.items():
        fact_id = _fact_id(raw_id, f"{where} fact id")
        if fact_id in out:
            raise VerificationError(f"{where} contains duplicate fact id {fact_id!r}")
        out[fact_id] = _observed_fact(raw_value, f"{where}.{fact_id}")
    return out


def _observer(value: Any, where: str) -> dict[str, str]:
    item = _mapping(value, where)
    _exact_keys(item, {"type", "identifier"}, where)
    observer_type = _string(item.get("type"), f"{where}.type", max_len=32)
    if observer_type not in OBSERVER_TYPES:
        raise VerificationError(
            f"{where}.type must be one of {sorted(OBSERVER_TYPES)!r}"
        )
    return {
        "type": observer_type,
        "identifier": _string(item.get("identifier"), f"{where}.identifier", max_len=128),
    }


def _timestamp(value: Any, where: str) -> str:
    raw = _string(value, where)
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise VerificationError(f"{where} must be an ISO-8601 date-time") from exc
    if parsed.tzinfo is None:
        raise VerificationError(f"{where} must include a timezone")
    return raw


def validate_verification_request(value: dict[str, Any]) -> dict[str, Any]:
    request = _mapping(value, "request")
    _exact_keys(request, REQUEST_KEYS, "request")

    if request.get("schema_version") != "0.1":
        raise VerificationError("request.schema_version must be '0.1'")
    if request.get("classification") != "POST_ACTION_VERIFICATION_REQUEST":
        raise VerificationError(
            "request.classification must be POST_ACTION_VERIFICATION_REQUEST"
        )
    if request.get("authority_granted") is not False:
        raise VerificationError("request.authority_granted must be false")

    checked = {
        "schema_version": "0.1",
        "classification": "POST_ACTION_VERIFICATION_REQUEST",
        "verification_id": _string(request.get("verification_id"), "request.verification_id", max_len=128),
        "task_id": _string(request.get("task_id"), "request.task_id", max_len=128),
        "preflight_receipt_fingerprint": _fingerprint(
            request.get("preflight_receipt_fingerprint"),
            "request.preflight_receipt_fingerprint",
        ),
        "task_fingerprint": _fingerprint(
            request.get("task_fingerprint"), "request.task_fingerprint"
        ),
        "action_fingerprint": _fingerprint(
            request.get("action_fingerprint"), "request.action_fingerprint"
        ),
        "target_binding": _target_binding(request.get("target_binding"), "request.target_binding"),
        "expected_facts": _expected_facts(request.get("expected_facts"), "request.expected_facts"),
        "authority_granted": False,
    }
    return deepcopy(checked)


def validate_post_action_observation(value: dict[str, Any]) -> dict[str, Any]:
    observation = _mapping(value, "observation")
    _exact_keys(observation, OBSERVATION_KEYS, "observation")

    if observation.get("schema_version") != "0.1":
        raise VerificationError("observation.schema_version must be '0.1'")
    if observation.get("classification") != "POST_ACTION_OBSERVATION":
        raise VerificationError(
            "observation.classification must be POST_ACTION_OBSERVATION"
        )
    if observation.get("authority_granted") is not False:
        raise VerificationError("observation.authority_granted must be false")

    checked = {
        "schema_version": "0.1",
        "classification": "POST_ACTION_OBSERVATION",
        "observation_id": _string(
            observation.get("observation_id"), "observation.observation_id", max_len=128
        ),
        "verification_id": _string(
            observation.get("verification_id"), "observation.verification_id", max_len=128
        ),
        "task_id": _string(observation.get("task_id"), "observation.task_id", max_len=128),
        "preflight_receipt_fingerprint": _fingerprint(
            observation.get("preflight_receipt_fingerprint"),
            "observation.preflight_receipt_fingerprint",
        ),
        "task_fingerprint": _fingerprint(
            observation.get("task_fingerprint"), "observation.task_fingerprint"
        ),
        "action_fingerprint": _fingerprint(
            observation.get("action_fingerprint"), "observation.action_fingerprint"
        ),
        "target_binding": _target_binding(
            observation.get("target_binding"), "observation.target_binding"
        ),
        "observed_facts": _observed_facts(
            observation.get("observed_facts"), "observation.observed_facts"
        ),
        "observed_by": _observer(observation.get("observed_by"), "observation.observed_by"),
        "observed_at": _timestamp(observation.get("observed_at"), "observation.observed_at"),
        "authority_granted": False,
    }
    return deepcopy(checked)


def _assert_exact_binding(request: dict[str, Any], observation: dict[str, Any]) -> None:
    for key in (
        "verification_id",
        "task_id",
        "preflight_receipt_fingerprint",
        "task_fingerprint",
        "action_fingerprint",
    ):
        if request[key] != observation[key]:
            raise VerificationError(f"observation.{key} does not bind to request")

    if request["target_binding"] != observation["target_binding"]:
        raise VerificationError("observation.target_binding does not bind to request")


def verify_post_action(
    request: dict[str, Any],
    observation: dict[str, Any],
) -> VerificationReceipt:
    checked_request = validate_verification_request(request)
    checked_observation = validate_post_action_observation(observation)
    _assert_exact_binding(checked_request, checked_observation)

    reasons: list[VerificationReason] = []
    contradiction = False
    unknown = False

    observed = checked_observation["observed_facts"]
    for fact_id in sorted(checked_request["expected_facts"]):
        expected = checked_request["expected_facts"][fact_id]
        item = observed.get(fact_id)

        if item is None:
            unknown = True
            reasons.append(
                VerificationReason(
                    code="FACT_NOT_OBSERVED",
                    fact_id=fact_id,
                    expected=expected,
                    observation_state="UNKNOWN",
                    observed=None,
                )
            )
            continue

        if item["observation_state"] == "UNKNOWN":
            unknown = True
            reasons.append(
                VerificationReason(
                    code="FACT_UNKNOWN",
                    fact_id=fact_id,
                    expected=expected,
                    observation_state="UNKNOWN",
                    observed=None,
                )
            )
            continue

        if item["value"] != expected:
            contradiction = True
            reasons.append(
                VerificationReason(
                    code="FACT_MISMATCH",
                    fact_id=fact_id,
                    expected=expected,
                    observation_state="OBSERVED",
                    observed=item["value"],
                )
            )

    if contradiction:
        outcome = "VERIFIED_FAILURE"
    elif unknown:
        outcome = "UNKNOWN"
    else:
        outcome = "VERIFIED_SUCCESS"

    return VerificationReceipt(
        schema_version="0.1",
        classification="POST_ACTION_VERIFICATION_RECEIPT",
        verification_id=checked_request["verification_id"],
        task_id=checked_request["task_id"],
        request_fingerprint=stable_hash(checked_request),
        observation_fingerprint=stable_hash(checked_observation),
        preflight_receipt_fingerprint=checked_request["preflight_receipt_fingerprint"],
        task_fingerprint=checked_request["task_fingerprint"],
        action_fingerprint=checked_request["action_fingerprint"],
        target_binding_fingerprint=stable_hash(checked_request["target_binding"]),
        outcome=outcome,
        reasons=[asdict(reason) for reason in reasons],
        authority_granted=False,
        retry_authorized=False,
    )
