from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evaluator import evaluate, load_yaml

EMOJI = {
    "PASS": "✅😺",
    "CAUTION": "⚠️😼",
    "REVIEW": "🤔🐈",
    "EVIDENCE_REQUIRED": "📋😾",
    "BLOCK": "✋😾",
}


def default_policy_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "generic_rules.yaml"


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
    print(f"task_fingerprint: {receipt.task_fingerprint}")
    print(f"policy_bundle_fingerprint: {receipt.policy_bundle_fingerprint}")


def cmd_check(args: argparse.Namespace) -> int:
    task = load_yaml(args.task)
    policies = load_yaml(args.policy)
    receipt = evaluate(task, policies)
    if args.json:
        print(json.dumps(receipt.__dict__, ensure_ascii=False, indent=2))
    else:
        print_receipt(receipt)
    return 0 if receipt.outcome == "PASS" else 2


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
    p = argparse.ArgumentParser(prog="nazeyatta")
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("check", help="run deterministic preflight KY")
    c.add_argument("task")
    c.add_argument("--policy", default=str(default_policy_path()))
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_check)

    d = sub.add_parser("debrief-template", help="emit a structured violation debrief template")
    d.add_argument("rule_id")
    d.set_defaults(func=cmd_debrief_template)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
