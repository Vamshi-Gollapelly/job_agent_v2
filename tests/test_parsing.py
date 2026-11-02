from ai.parsing import parse_analysis, failed_analysis


def test_parses_plain_json():
    result = parse_analysis('{"fit_score": 72, "fit_reason": "Good", "recommendation": "apply",'
                            ' "key_requirements": ["Java"], "matching_skills": ["Java"], "missing_skills": []}')
    assert result["fit_score"] == 72
    assert result["recommendation"] == "apply"
    assert result["matching_skills"] == ["Java"]


def test_strips_markdown_fences_and_surrounding_text():
    text = 'Here you go:\n```json\n{"fit_score": 55, "recommendation": "consider"}\n```'
    result = parse_analysis(text)
    assert result["fit_score"] == 55
    assert result["recommendation"] == "consider"


def test_clamps_out_of_range_scores():
    assert parse_analysis('{"fit_score": 140}')["fit_score"] == 100
    assert parse_analysis('{"fit_score": -5}')["fit_score"] == 0


def test_non_numeric_score_becomes_zero():
    assert parse_analysis('{"fit_score": "high"}')["fit_score"] == 0


def test_unknown_recommendation_defaults_to_skip():
    assert parse_analysis('{"fit_score": 80, "recommendation": "definitely"}')["recommendation"] == "skip"


def test_list_fields_are_always_lists():
    result = parse_analysis('{"fit_score": 60, "matching_skills": "Java, SQL"}')
    assert result["matching_skills"] == []
    assert result["missing_skills"] == []


def test_invalid_json_returns_safe_default():
    result = parse_analysis("{not valid json}")
    assert result["fit_score"] == 0
    assert result["recommendation"] == "skip"
    assert result["fit_reason"].startswith("Analysis failed")


def test_empty_response_returns_safe_default():
    assert parse_analysis("")["fit_score"] == 0
    assert parse_analysis(None)["recommendation"] == "skip"


def test_failed_analysis_shape():
    result = failed_analysis("timeout")
    assert set(result) == {"fit_score", "fit_reason", "recommendation",
                           "key_requirements", "matching_skills", "missing_skills"}
