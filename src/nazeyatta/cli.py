from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .evaluator import EVIDENCE_LANES, evaluate, load_yaml

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


def default_policy_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "generic_rules.yaml"


def _prepare_stdout() -> None:
    # Windows consoles frequently use a legacy code page (e.g. cp932). Without this the
    # emoji in the receipt raise UnicodeEncodeError before any finding is printed.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(errors="replace")
        except (ValueError, OSError):
            pass


def print_receipt(receipt) -> None:
    print("NAZEYATTA")
    print("👈😽 PRE-FLIGHT KY")
    print()
    print(f"{EMOJI[receipt.outcome]} {receipt.outcome}")
    print()
    if not receipt.findings:
        print("No blocking or cautionary finding under this policy bundle.")
    for f in receipt.findings:
        print(f"{f['rule_id']}  {f['title']}")
        print(f"  hazard: {f['hazard']}")
        if f["evidence_key"]:
            print(f"  evidence: {f['evidence_key']} = {f['evidence_state']}")
        print(f"  effect: {f['effect']}")
        print(f"  reason: {f['reason']}")
        print()
    print("EXECUTION AUTHORITY: NOT GRANTED BY NAZEYATTA")
    print(f"evidence_lane: {receipt.evidence_lane}")
    print(f"task_fingerprint: {receipt.task_fingerprint}")
    print(f"policy_bundle_fingerprint: {receipt.policy_bundle_fingerprint}")


def cmd_check(args: argparse.Namespace) -> int:
    try:
        task = load_yaml(args.task)
        policies = load_yaml(args.policy)
        receipt = evaluate(task, policies)
    except (ValueError, OSError) as exc:
        # Malformed task/policy is not a PASS and not a policy finding either: report it
        # distinctly instead of a traceback, and keep the exit status non-zero.
        print(f"NAZEYATTA\n🚫😾 INVALID INPUT\n\n{type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    if args.require_lane and receipt.evidence_lane != args.require_lane:
        print(
            f"NAZEYATTA\n✋😾 LANE MISMATCH\n\nrequired evidence_lane {args.require_lane!r}, "
            f"task resolved to {receipt.evidence_lane!r} (legacy scalar evidence is not provenance-qualified)",
            file=sys.stderr,
        )
        return EXIT_NOT_PASS
    if args.json:
        print(json.dumps(receipt.__dict__, ensure_ascii=False, indent=2))
    else:
        print_receipt(receipt)
    return EXIT_PASS if receipt.outcome == "PASS" else EXIT_NOT_PASS


def cmd_debrief_template(args: argparse.Namespace) -> int:
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
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("check", help="run deterministic preflight KY")
    c.add_argument("task")
    c.add_argument("--policy", default=str(default_policy_path()))
    c.add_argument("--json", action="store_true")
    c.add_argument(
        "--require-lane",
        choices=EVIDENCE_LANES,
        default=None,
        help="fail (exit 2) unless the task resolves to this evidence lane; "
        "use provenance-v0.2 to reject legacy scalar evidence",
    )
    c.set_defaults(func=cmd_check)

    d = sub.add_parser("debrief-template", help="emit a structured violation debrief template")
    d.add_argument("rule_id")
    d.set_defaults(func=cmd_debrief_template)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
