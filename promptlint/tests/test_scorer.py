"""Tests for promptlint.scorer — mocks the Anthropic client so these run with no API key."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from promptlint.rubric import DIMENSION_KEYS  # noqa: E402
from promptlint.scorer import ScoreResult, score_prompt  # noqa: E402


def _fake_tool_use_response(scores: dict, feedback: dict, top_fixes: list, rewrite: str, clarifying_questions: list | None = None):
    tool_block = SimpleNamespace(
        type="tool_use",
        input={
            "scores": scores,
            "feedback": feedback,
            "top_fixes": top_fixes,
            "clarifying_questions": clarifying_questions or [],
            "rewrite": rewrite,
        },
    )
    return SimpleNamespace(content=[tool_block])


def test_score_prompt_empty_raises():
    with pytest.raises(ValueError):
        score_prompt("   ", client=MagicMock())


def test_score_prompt_parses_tool_response():
    scores = {k: 3 for k in DIMENSION_KEYS}
    feedback = {k: f"feedback for {k}" for k in DIMENSION_KEYS}
    top_fixes = ["Add audience.", "Specify output format."]
    clarifying_questions = ["What does 'better' mean here — faster, cheaper, or more accurate?"]
    rewrite = "A better version of the prompt."

    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_tool_use_response(
        scores, feedback, top_fixes, rewrite, clarifying_questions
    )

    result = score_prompt("Write something.", client=fake_client)

    assert isinstance(result, ScoreResult)
    assert result.scores == scores
    assert result.overall == 3.0
    assert result.top_fixes == top_fixes
    assert result.clarifying_questions == clarifying_questions
    assert result.rewrite == rewrite
    fake_client.messages.create.assert_called_once()


def test_overall_is_average_of_scores():
    scores = {k: 5 for k in DIMENSION_KEYS}
    result = ScoreResult(prompt="x", scores=scores)
    assert result.overall == 5.0


def test_overall_with_no_scores_is_zero():
    result = ScoreResult(prompt="x")
    assert result.overall == 0.0


def test_to_dict_roundtrip_keys():
    scores = {k: 4 for k in DIMENSION_KEYS}
    result = ScoreResult(prompt="x", scores=scores, feedback={k: "" for k in DIMENSION_KEYS})
    d = result.to_dict()
    assert set(
        ["prompt", "model", "overall", "scores", "feedback", "top_fixes", "clarifying_questions", "rewrite"]
    ).issubset(d.keys())
