"""Optional subjective assessment of an evidence-backed PR brief.

Usage: python deepeval_pr_opportunity.py brief.json
Requires: pip install deepeval and a configured judge model.
Judge output NEVER overrides the deterministic evidence gate.
"""
import argparse
import json
from pathlib import Path
from pr_opportunity_gate import evaluate

def assess(brief):
    gate = evaluate(brief)
    if gate["status"] != "ready_for_pr":
        return {"gate": gate, "judge": "skipped_missing_evidence"}
    from deepeval.metrics import GEval
    from deepeval.test_case import LLMTestCase, SingleTurnParams
    metric = GEval(
        name="PR proposal usefulness",
        criteria=("Assess whether the proposed PR is narrow, testable, and plausibly useful "
                  "given only the supplied evidence. Penalize unsupported impact claims. "
                  "Do not treat linked URLs as verified by this metric."),
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        threshold=0.7,
    )
    case = LLMTestCase(
        input=json.dumps({"title": brief["title"], "evidence": brief["evidence"]}),
        actual_output=brief.get("proposal", ""),
    )
    metric.measure(case)
    return {"gate": gate, "judge": {"score": metric.score, "reason": metric.reason}}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("brief")
    args = p.parse_args()
    print(json.dumps(assess(json.loads(Path(args.brief).read_text(encoding="utf-8"))), indent=2))
