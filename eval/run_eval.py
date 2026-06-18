#!/usr/bin/env python3
"""Catch-up skill eval harness.

Scores catch-up outputs against gold keys and compares them to a baseline
(a plain "explain these changes" with no skill). A positive delta means the
skill helps on that metric.

Usage (from the repo root):
    python eval/run_eval.py          # offline: score saved outputs/
    python eval/run_eval.py --api    # generate outputs live via Anthropic

Metrics (deterministic, offline):
    citation  fraction of file:line cites that resolve to a real line
    risk      fraction of planted issues surfaced (keyword match)

LLM-judged metrics (comprehension quiz, hallucinated-why) are left as hooks;
see eval/README.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from metrics import citation_accuracy, risk_recall
from runners import get_output

EVAL_DIR = Path(__file__).resolve().parent
CASES_DIR = EVAL_DIR / "cases"
CONDITIONS = ["catch_up", "baseline"]


def score(text, case_dir, gold):
    repo = case_dir / "repo"
    cite_score, cite_valid, cite_total = citation_accuracy(text, repo)
    risk_score, risk_caught, risk_total = risk_recall(text, gold["planted_issues"])
    return {
        "citation": cite_score,
        "citation_detail": f"{cite_valid}/{cite_total}",
        "risk": risk_score,
        "risk_detail": f"{risk_caught}/{risk_total}",
    }


def avg(xs):
    return sum(xs) / len(xs) if xs else 0.0


def main():
    ap = argparse.ArgumentParser(description="Score catch-up outputs vs a baseline.")
    ap.add_argument("--api", action="store_true",
                    help="generate outputs live via the Anthropic API")
    args = ap.parse_args()

    cases = sorted(p for p in CASES_DIR.iterdir() if p.is_dir())
    if not cases:
        raise SystemExit(f"No cases found under {CASES_DIR}")

    agg = {c: {"citation": [], "risk": []} for c in CONDITIONS}

    print(f"\nCatch-up eval — {len(cases)} case(s)\n" + "=" * 60)
    for case_dir in cases:
        gold = json.loads((case_dir / "gold.json").read_text())
        print(f"\n[{case_dir.name}]  {gold.get('intent', '')}")
        print(f"  {'condition':<10}{'citation':>16}{'risk':>16}")
        for cond in CONDITIONS:
            text = get_output(case_dir, cond, use_api=args.api)
            s = score(text, case_dir, gold)
            agg[cond]["citation"].append(s["citation"])
            agg[cond]["risk"].append(s["risk"])
            print(f"  {cond:<10}"
                  f"{s['citation']:>7.0%} ({s['citation_detail']:>4})"
                  f"{s['risk']:>9.0%} ({s['risk_detail']:>4})")

    print("\n" + "=" * 60)
    print("AVERAGES")
    print(f"  {'condition':<10}{'citation':>12}{'risk':>12}")
    for cond in CONDITIONS:
        print(f"  {cond:<10}{avg(agg[cond]['citation']):>12.0%}{avg(agg[cond]['risk']):>12.0%}")

    dc = avg(agg["catch_up"]["citation"]) - avg(agg["baseline"]["citation"])
    dr = avg(agg["catch_up"]["risk"]) - avg(agg["baseline"]["risk"])
    print("\nDELTA (catch_up - baseline)")
    print(f"  citation: {dc:+.0%}    risk: {dr:+.0%}")
    print("\nPositive delta = the skill helps on that metric.\n")


if __name__ == "__main__":
    main()
