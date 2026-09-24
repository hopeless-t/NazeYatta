from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path

from . import __version__
from .evaluator import EVIDENCE_LANES, MAX_INPUT_BYTES, evaluate, load_yaml, load_yaml_text
from .receipt_io import write_receipt_json
from .verification import VerificationError, verify_post_action
from .verification_io import write_verification_receipt_json

EMOJI = {
    "PASS": "✅😺",
    "CAUTION": "⚠️😼",
    "REVIEW": "🤔🐈",
    "EVIDENCE_REQUIRED": "📋😾",
    "BLOCK": "✋😾",
}

# Exit statuses. Only PASS is 0. Everything else is non-zero so a caller that forgets to
# inspect the receipt still fails closed.
EXIT_PASS = 0
EXIT_NOT_PASS = 2
EXIT_INVALID_INPUT = 3


EXAMPLE_FILES = {
    "publish-photo": "example_publish_photo.yaml",
    "safe-read": "example_safe_read.yaml",
}

SCHEMA_FILES = {
    "task": "task.schema.json",
    "evidence": "evidence.schema.json",
    "receipt": "receipt.schema.json",
    "verification-request": "post-action-verification-request.schema.json",
    "post-action-observation": "post-action-observation.schema.json",
    "verification-receipt": "post-action-verification-receipt.schema.json",
}


def default_policy_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "generic_rules.yaml"


def packaged_example_path(name: str) -> Path:
    return Path(__file__).resolve().parent / "data" / EXAMPLE_FILES[name]


def packaged_schema_path(name: str) -> Path:
    return Path(__file__).resolve().parent / "schemas" / SCHEMA_FILES[name]


def _prepare_stdout() -> None:
    # Windows consoles frequently use a legacy code page (e.g. cp932). Without this the
    # emoji in the receipt raise UnicodeEncodeError before any finding is printed.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(errors="replace")
        except (ValueError, OSError):
            pass


# C0 controls, DEL, C1 controls, and the Unicode line/paragraph separators.
_CONTROL = re.compile("[\x00-\x1f\x7f-\x9f  ]")
MAX_FIELD_CHARS = 400


def safe_text(value: object, limit: int = MAX_FIELD_CHARS) -> str:
    """Make policy/task-supplied text safe to print in the human-readable receipt.

    Rule titles, hazards and reasons come from files the worker may control. Without this a
    title containing a newline could forge extra receipt lines ("PASS", "AUTHORITY GRANTED")
    and an ESC sequence could rewrite the terminal. Control characters (C0, DEL, C1) and the
    Unicode line/paragraph separators are replaced by U+FFFD; over-long text is truncated.
    The JSON receipt is unaffected (json escapes these characters itself).
    """
    text = _CONTROL.sub("�", str(value))
    return text if len(text) <= limit else text[:limit] + "…[truncated]"


def _load_task_input(path: str):
    if path != "-":
        return load_yaml(path)

    stream = getattr(sys.stdin, "buffer", None)
    if stream is None:
        text = sys.stdin.read(MAX_INPUT_BYTES + 1)
        return load_yaml_text(text, "<stdin>")

    raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError(f"<stdin>: input larger than {MAX_INPUT_BYTES} bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("<stdin>: input is not valid UTF-8") from exc
    return load_yaml_text(text, "<stdin>")


def print_receipt(receipt) -> None:
    print("NAZEYATTA")
    print("👈😽 PRE-FLIGHT KY")
    print()
    print(f"{EMOJI[receipt.outcome]} {receipt.outcome}")
    print()
    if not receipt.findings:
        print("No blocking or cautionary finding under this policy bundle.")
    for f in receipt.findings:
        print(f"{safe_text(f['rule_id'], 80)}  {safe_text(f['title'])}")
        print(f"  hazard: {safe_text(f['hazard'])}")
        if f["evidence_key"]:
            print(f"  evidence: {safe_text(f['evidence_key'], 120)} = {safe_text(f['evidence_state'], 40)}")
        print(f"  effect: {f['effect']}")
        print(f"  reason: {safe_text(f['reason'])}")
        print()
    print("EXECUTION AUTHORITY: NOT GRANTED BY NAZEYATTA")
    print(f"evidence_lane: {receipt.evidence_lane}")
    print(f"task_fingerprint: {receipt.task_fingerprint}")
    print(f"policy_bundle_fingerprint: {receipt.policy_bundle_fingerprint}")


def cmd_check(args: argparse.Namespace) -> int:
    try:
        if args.policy == "-":
            raise ValueError("--policy - is not supported; only the Task positional argument may read stdin")
        task = _load_task_input(args.task)
        policies = load_yaml(args.policy)
        receipt = evaluate(task, policies)
    except (ValueError, OSError) as exc:
        # Malformed task/policy is not a PASS and not a policy finding either: report it
        # distinctly instead of a traceback, and keep the exit status non-zero.
        print(f"NAZEYATTA\n🚫😾 INVALID INPUT\n\n{type(exc).__name__}: {safe_text(exc)}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    if args.require_lane and receipt.evidence_lane != args.require_lane:
        print(
            f"NAZEYATTA\n✋😾 LANE MISMATCH\n\nrequired evidence_lane {args.require_lane!r}, "
            f"task resolved to {receipt.evidence_lane!r} (legacy scalar evidence is not provenance-qualified)",
            file=sys.stderr,
        )
        return EXIT_NOT_PASS
    if args.receipt_out:
        try:
            write_receipt_json(receipt, args.receipt_out)
        except OSError as exc:
            print(
                f"NAZEYATTA\n🚫😾 RECEIPT WRITE FAILED\n\n{type(exc).__name__}: {safe_text(exc)}",
                file=sys.stderr,
            )
            return EXIT_INVALID_INPUT
    if args.json:
        print(json.dumps(receipt.__dict__, ensure_ascii=False, indent=2))
    else:
        print_receipt(receipt)
    return EXIT_PASS if receipt.outcome == "PASS" else EXIT_NOT_PASS


def _display_scalar(value: object) -> str:
    return safe_text(json.dumps(value, ensure_ascii=False, sort_keys=True), limit=MAX_FIELD_CHARS)


def print_verification_receipt(receipt) -> None:
    print("NAZEYATTA")
    print("👈😽 POST-FLIGHT VERIFY")
    print()

    icon = {
        "VERIFIED_SUCCESS": "✅😺",
        "VERIFIED_FAILURE": "🙀😿",
        "UNKNOWN": "🔎😿",
    }[receipt.outcome]
    print(f"{icon} {receipt.outcome}")
    print()

    if receipt.outcome == "VERIFIED_SUCCESS":
        print("Expected and observed facts matched exactly.")
    elif receipt.outcome == "VERIFIED_FAILURE":
        print("🙀 NAZE YATTA?")
        print("Observed facts contradicted one or more expected postconditions.")
    else:
        print("Required postcondition facts were not fully observed.")

    for reason in receipt.reasons:
        print()
        print(safe_text(reason["fact_id"], 80))
        print(f"  expected: {_display_scalar(reason['expected'])}")
        if reason["observation_state"] == "UNKNOWN":
            print("  observed: UNKNOWN")
        else:
            print(f"  observed: {_display_scalar(reason['observed'])}")
        print(f"  reason: {safe_text(reason['code'], 80)}")

    print()
    print("EXECUTION AUTHORITY: NOT GRANTED BY NAZEYATTA")
    print("RETRY AUTHORITY: NOT GRANTED BY NAZEYATTA")
    print(f"request_fingerprint: {receipt.request_fingerprint}")
    print(f"observation_fingerprint: {receipt.observation_fingerprint}")


def cmd_verify(args: argparse.Namespace) -> int:
    try:
        request = load_yaml(args.request)
        observation = load_yaml(args.observation)
        receipt = verify_post_action(request, observation)
    except (VerificationError, ValueError, OSError) as exc:
        print(
            f"NAZEYATTA\n🚫😾 INVALID VERIFICATION INPUT\n\n{type(exc).__name__}: {safe_text(exc)}",
            file=sys.stderr,
        )
        return EXIT_INVALID_INPUT

    if args.receipt_out:
        try:
            write_verification_receipt_json(receipt, args.receipt_out)
        except OSError as exc:
            print(
                f"NAZEYATTA\n🚫😾 RECEIPT WRITE FAILED\n\n{type(exc).__name__}: {safe_text(exc)}",
                file=sys.stderr,
            )
            return EXIT_INVALID_INPUT

    if args.json:
        print(json.dumps(asdict(receipt), ensure_ascii=False, indent=2))
    else:
        print_verification_receipt(receipt)

    return EXIT_PASS if receipt.outcome == "VERIFIED_SUCCESS" else EXIT_NOT_PASS


def cmd_example(args: argparse.Namespace) -> int:
    """Print one packaged task example without evaluating it."""
    try:
        text = packaged_example_path(args.name).read_text(encoding="utf-8")
    except OSError as exc:
        print(
            f"NAZEYATTA\n🚫😾 EXAMPLE READ FAILED\n\n{type(exc).__name__}: {safe_text(exc)}",
            file=sys.stderr,
        )
        return EXIT_INVALID_INPUT
    sys.stdout.write(text)
    if text and not text.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def cmd_schema(args: argparse.Namespace) -> int:
    """Print one packaged core JSON Schema without interpreting it."""
    try:
        text = packaged_schema_path(args.name).read_text(encoding="utf-8")
    except OSError as exc:
        print(
            f"NAZEYATTA\n🚫😾 SCHEMA READ FAILED\n\n{type(exc).__name__}: {safe_text(exc)}",
            file=sys.stderr,
        )
        return EXIT_INVALID_INPUT
    sys.stdout.write(text)
    if text and not text.endswith("\n"):
        sys.stdout.write("\n")
    return 0


RULE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def cmd_debrief_template(args: argparse.Namespace) -> int:
    if not RULE_ID.match(args.rule_id):
        print("NAZEYATTA\n🚫😾 INVALID INPUT\n\nrule_id must match [A-Za-z0-9][A-Za-z0-9._-]{0,63}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    template = {
        "schema_version": "0.1",
        "rule_id": args.rule_id,
        "classification": "WORKER_SELF_REPORT",
        "intended_goal": "",
        "understood_rule": "",
        "actual_action": "",
        "decision_point": "",
        "why_action_seemed_acceptable": "",
        "ignored_or_overridden_signal": "",
        "pressure_or_goal_conflict": "",
        "safer_alternative": "",
        "proposed_prevention": "",
        "root_cause_status": "UNRESOLVED",
    }
    print(json.dumps(template, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    _prepare_stdout()
    p = argparse.ArgumentParser(prog="nazeyatta")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("check", help="run deterministic preflight KY")
    c.add_argument("task", help="Task YAML path, or '-' to read one UTF-8 Task from stdin")
    c.add_argument("--policy", default=str(default_policy_path()), help="policy YAML path; stdin is not supported")
    c.add_argument("--json", action="store_true")
    c.add_argument(
        "--receipt-out",
        default=None,
        metavar="PATH",
        help="write the evaluated Receipt as deterministic UTF-8 JSON; refuses to overwrite PATH",
    )
    c.add_argument(
        "--require-lane",
        choices=EVIDENCE_LANES,
        default=None,
        help="fail (exit 2) unless the task resolves to this evidence lane; "
        "use provenance-v0.2 to reject legacy scalar evidence",
    )
    c.set_defaults(func=cmd_check)

    v = sub.add_parser(
        "verify",
        help="verify exact post-action facts without executing or retrying the action",
    )
    v.add_argument("request", help="VerificationRequest YAML path")
    v.add_argument("observation", help="PostActionObservation YAML path")
    v.add_argument("--json", action="store_true")
    v.add_argument(
        "--receipt-out",
        default=None,
        metavar="PATH",
        help="write the VerificationReceipt as deterministic UTF-8 JSON; refuses to overwrite PATH",
    )
    v.set_defaults(func=cmd_verify)

    e = sub.add_parser(
        "example",
        help="print a packaged task example without evaluating it",
    )
    e.add_argument("name", choices=sorted(EXAMPLE_FILES))
    e.set_defaults(func=cmd_example)

    s = sub.add_parser(
        "schema",
        help="print a packaged core JSON Schema without validating input",
    )
    s.add_argument("name", choices=sorted(SCHEMA_FILES))
    s.set_defaults(func=cmd_schema)

    d = sub.add_parser("debrief-template", help="emit a structured violation debrief template")
    d.add_argument("rule_id")
    d.set_defaults(func=cmd_debrief_template)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
