"""Evidence-first PR recommendation gate. Stdlib only; never invent evidence."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

FIELDS = ("problem", "reproduction", "code_location", "expected_impact", "maintainer_signal")
WEIGHTS = {"reach": 30, "reproducibility": 25, "maintainer": 20, "feasibility": 15, "no_overlap": 10}

def valid_url(value):
    if not isinstance(value, str):
        return False
    p = urlparse(value)
    return p.scheme == "https" and bool(p.netloc) and not p.username and not p.password

def evaluate(candidate):
    if not isinstance(candidate, dict) or not isinstance(candidate.get("title"), str):
        raise ValueError("Candidate must have a title")
    evidence = candidate.get("evidence", {})
    if not isinstance(evidence, dict):
        raise ValueError("Evidence must be an object")
    missing = [field for field in FIELDS if not evidence.get(field)]
    invalid = [field for field in FIELDS if field in evidence and evidence[field] and not valid_url(evidence[field])]
    if invalid:
        raise ValueError("Evidence must be HTTPS URLs: " + ", ".join(invalid))
    scores = candidate.get("scores", {})
    if not isinstance(scores, dict):
        raise ValueError("Scores must be an object")
    invalid_scores = [k for k, v in scores.items() if k not in WEIGHTS or type(v) not in (int, float) or not 0 <= v <= 3]
    if invalid_scores:
        raise ValueError("Invalid scores: " + ", ".join(invalid_scores))
    weighted = sum(WEIGHTS[k] * scores[k] / 3 for k in scores)
    coverage = sum(WEIGHTS[k] for k in scores)
    blockers = list(missing)
    if candidate.get("existing_pr") is True:
        blockers.append("existing_pr")
    if candidate.get("requires_private_resources") is True:
        blockers.append("private_resources")
    if candidate.get("maintainer_approved") is not True:
        blockers.append("maintainer_approval")
    return {
        "title": candidate["title"],
        "status": "ready_for_pr" if not blockers and len(scores) == len(WEIGHTS) else "investigate",
        "blockers": blockers,
        "score_lower_bound": round(weighted, 2),
        "score_coverage_percent": coverage,
        "note": "Scores are subjective screening estimates, not demonstrated impact.",
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("candidates", help="JSON array of PR candidates")
    args = p.parse_args()
    data = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        p.error("Expected JSON array")
    print(json.dumps([evaluate(x) for x in data], indent=2))

if __name__ == "__main__":
    main()
