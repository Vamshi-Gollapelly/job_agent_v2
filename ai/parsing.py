"""Pure helpers for turning model output into a safe, validated analysis dict.

Kept separate from analyser.py so they can be unit-tested without an API key.
"""
import json
import re

VALID_RECOMMENDATIONS = {"apply", "consider", "skip"}
LIST_FIELDS = ("key_requirements", "matching_skills", "missing_skills")


def failed_analysis(reason):
    """Default result used whenever the model output cannot be trusted."""
    return {
        "fit_score": 0,
        "fit_reason": f"Analysis failed: {reason}",
        "recommendation": "skip",
        "key_requirements": [],
        "matching_skills": [],
        "missing_skills": [],
    }


def parse_analysis(text):
    """Parse the model's JSON reply, tolerating markdown fences and bad values.

    - strips ```json fences and any text around the JSON object
    - clamps fit_score to 0-100
    - forces recommendation to apply/consider/skip
    - guarantees the list fields are lists of strings
    """
    if not text or not text.strip():
        return failed_analysis("empty response")

    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    match = re.search(r"\{.*\}", cleaned, re.S)
    if not match:
        return failed_analysis("no JSON object in response")

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        return failed_analysis(f"invalid JSON ({e.msg})")
    if not isinstance(data, dict):
        return failed_analysis("response was not a JSON object")

    try:
        score = int(round(float(data.get("fit_score", 0))))
    except (TypeError, ValueError):
        score = 0
    data["fit_score"] = max(0, min(100, score))

    rec = str(data.get("recommendation", "skip")).strip().lower()
    data["recommendation"] = rec if rec in VALID_RECOMMENDATIONS else "skip"

    data["fit_reason"] = str(data.get("fit_reason", ""))
    for field in LIST_FIELDS:
        value = data.get(field, [])
        data[field] = [str(v) for v in value] if isinstance(value, list) else []

    return data
