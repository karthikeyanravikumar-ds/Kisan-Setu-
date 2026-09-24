"""
Unit test suite for Quality Intelligence Engine.
Tests:
1. Grade meets requirement (A >= A, A >= B)
2. Grade does not meet requirement (B < A, C < B)
3. Missing requirement
4. Missing grade
5. Assessment available
6. Assessment unavailable
"""

import sys
import os
import pytest

# Add repository root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from utils.quality_intelligence import calculate_quality_intelligence


def test_grade_meets_requirement():
    """Test 1: Grade meets or exceeds requirement."""
    # Case A: Exact match (A meets A)
    res_a = calculate_quality_intelligence(quality_grade="A", minimum_quality="A", crop="Onion")
    assert res_a["quality_grade"] == "A"
    assert res_a["required_quality"] == "A"
    assert res_a["quality_requirement_met"] is True
    assert res_a["quality_status"] == "Requirement met"
    assert "meets the buyer's minimum requirement" in res_a["explanation"]

    # Case B: Exceeds requirement (A meets B)
    res_b = calculate_quality_intelligence(quality_grade="A", minimum_quality="B", crop="Tomato")
    assert res_b["quality_requirement_met"] is True
    assert res_b["quality_status"] == "Requirement met"

    # Case C: Exceeds requirement (B meets C)
    res_c = calculate_quality_intelligence(quality_grade="B", minimum_quality="C", crop="Potato")
    assert res_c["quality_requirement_met"] is True
    assert res_c["quality_status"] == "Requirement met"


def test_grade_does_not_meet_requirement():
    """Test 2: Grade is lower than minimum requirement."""
    # Case A: Grade B vs Minimum Grade A
    res_ba = calculate_quality_intelligence(quality_grade="B", minimum_quality="A", crop="Onion")
    assert res_ba["quality_grade"] == "B"
    assert res_ba["required_quality"] == "A"
    assert res_ba["quality_requirement_met"] is False
    assert res_ba["quality_status"] == "Requirement not met"
    assert "does not meet the buyer's minimum requirement" in res_ba["explanation"]

    # Case B: Grade C vs Minimum Grade B
    res_cb = calculate_quality_intelligence(quality_grade="C", minimum_quality="B", crop="Tomato")
    assert res_cb["quality_requirement_met"] is False
    assert res_cb["quality_status"] == "Requirement not met"


def test_missing_requirement():
    """Test 3: Minimum quality requirement is missing or None."""
    res = calculate_quality_intelligence(quality_grade="A", minimum_quality=None, crop="Onion")
    assert res["quality_grade"] == "A"
    assert res["required_quality"] is None
    assert res["quality_requirement_met"] is None
    assert res["quality_status"] == "Requirement unavailable"
    assert "Buyer quality requirement is not specified" in res["explanation"]


def test_missing_grade():
    """Test 4: Farmer quality grade is missing or None."""
    res = calculate_quality_intelligence(quality_grade=None, minimum_quality="A", crop="Tomato")
    assert res["quality_grade"] is None
    assert res["required_quality"] == "A"
    assert res["quality_requirement_met"] is None
    assert res["quality_status"] == "Requirement unavailable"
    assert "Quality grade details are unavailable" in res["explanation"]


def test_assessment_available():
    """Test 5: Preliminary AI assessment is provided."""
    # String assessment
    sample_text = "PRELIMINARY QUALITY: Grade A\n- External skin intact\n- Good uniformity"
    res_str = calculate_quality_intelligence(
        quality_grade="A",
        minimum_quality="A",
        crop="Onion",
        assessment=sample_text
    )
    assert res_str["assessment_available"] is True
    assert res_str["assessment_text"] == sample_text
    assert "Preliminary AI-assisted observation" in res_str["disclaimer"]

    # Dict assessment (as returned by analyze_produce_quality)
    sample_dict = {
        "success": True,
        "source": "Gemini AI (gemini-2.5-flash)",
        "result": sample_text,
    }
    res_dict = calculate_quality_intelligence(
        quality_grade="A",
        minimum_quality="A",
        crop="Onion",
        assessment=sample_dict
    )
    assert res_dict["assessment_available"] is True
    assert res_dict["assessment_text"] == sample_text
    assert res_dict["assessment_source"] == "Gemini AI (gemini-2.5-flash)"


def test_assessment_unavailable():
    """Test 6: Preliminary AI assessment is None or empty."""
    res = calculate_quality_intelligence(quality_grade="A", minimum_quality="A", assessment=None)
    assert res["assessment_available"] is False
    assert res["assessment_text"] is None
    assert res["assessment_source"] == "None"

    # Empty dict
    res_empty = calculate_quality_intelligence(quality_grade="A", minimum_quality="A", assessment={})
    assert res_empty["assessment_available"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
