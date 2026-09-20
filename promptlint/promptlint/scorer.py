"""Core scoring logic: send a prompt to Claude, get back a structured score.

Uses forced tool-use (not free-text parsing) so the result is always valid,
predictable JSON rather than something regex'd out of a markdown block.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import anthropic

from .rubric import DIMENSIONS, DIMENSION_KEYS

DEFAULT_MODEL = os.environ.get("PROMPTLINT_MODEL", "claude-sonnet-4-5")

_TOOL_NAME = "submit_prompt_score"

_TOOL_SCHEMA = {
    "name": _TOOL_NAME,
    "description": "Submit the rubric score and feedback for the prompt being reviewed.",
    "input_schema": {
        "type": "object",
        "properties": {
            "scores": {
                "type": "object",
                "description": "Score 1-5 for each rubric dimension.",
                "properties": {key: {"type": "integer", "minimum": 1, "maximum": 5} for key in DIMENSION_KEYS},
                "required": DIMENSION_KEYS,
            },
            "feedback": {
                "type": "object",
                "description": "One or two concrete sentences per dimension explaining the score.",
                "properties": {key: {"type": "string"} for key in DIMENSION_KEYS},
                "required": DIMENSION_KEYS,
            },
            "top_fixes": {
                "type": "array",
                "description": "The 2-3 changes that would raise the score the most, most impactful first.",
                "items": {"type": "string"},
            },
            "clarifying_questions": {
                "type": "array",
                "description": (
                    "2-4 sharp questions aimed at the person who wrote the prompt, not at the "
                    "reader of its output — each one should force a decision the prompt is "
                    "currently ducking (an undefined success metric, an unresolved scope "
                    "boundary, a tension between two stated goals). These should provoke the "
                    "author into scoping the problem more precisely, not just restate what's "
                    "missing — that's what top_fixes is for."
                ),
                "items": {"type": "string"},
            },
            "rewrite": {
                "type": "string",
                "description": "A rewritten version of the prompt that addresses the top fixes.",
            },
        },
        "required": ["scores", "feedback", "top_fixes", "clarifying_questions", "rewrite"],
    },
}

_SYSTEM_PROMPT = """You are a strict prompt-quality reviewer. You score a single prompt \
against a fixed five-dimension rubric — you do not answer the prompt, execute it, or \
role-play as its recipient. Score honestly: most first-draft prompts should NOT score 5s \
across the board. A 5 means the dimension is fully and explicitly addressed; a 3 means it's \
partially there or implied but not stated; a 1 means it's essentially absent. Be specific in \
the feedback — cite what is missing, not just that something is missing, and prefer a subtle, \
genuinely non-obvious gap over a generic one when the prompt is already mostly complete. The \
clarifying_questions are the most important part of your output when the prompt is already \
decent: don't just re-list what's missing, ask the question that would force the author to \
actually decide it — e.g. not "what's the success metric?" but "does 'improve retention' mean \
30-day retention, 90-day, or something else, and does a paused account count as retained?". \
The rewrite should be a genuinely improved version of the prompt, not a trivial rephrasing; if \
the prompt is already strong, say so and make only the one change that matters."""


@dataclass
class ScoreResult:
    prompt: str
    scores: dict[str, int] = field(default_factory=dict)
    feedback: dict[str, str] = field(default_factory=dict)
    top_fixes: list[str] = field(default_factory=list)
    clarifying_questions: list[str] = field(default_factory=list)
    rewrite: str = ""
    model: str = DEFAULT_MODEL

    @property
    def overall(self) -> float:
        if not self.scores:
            return 0.0
        return round(sum(self.scores.values()) / len(self.scores), 2)

    def to_dict(self) -> dict:
        return {
            "prompt": self.prompt,
            "model": self.model,
            "overall": self.overall,
            "scores": self.scores,
            "feedback": self.feedback,
            "top_fixes": self.top_fixes,
            "clarifying_questions": self.clarifying_questions,
            "rewrite": self.rewrite,
        }


def score_prompt(
    prompt_text: str,
    *,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    client: anthropic.Anthropic | None = None,
) -> ScoreResult:
    """Score `prompt_text` against the fixed rubric and return a ScoreResult.

    Raises anthropic.APIError subclasses on API failure, and ValueError if the
    model declines to call the scoring tool (should not happen with
    tool_choice forced, but checked defensively).
    """
    if not prompt_text or not prompt_text.strip():
        raise ValueError("prompt_text is empty — nothing to score.")

    client = client or anthropic.Anthropic(api_key=api_key)

    dimension_list = "\n".join(f"- {d.key}: {d.label} — {d.description}" for d in DIMENSIONS)

    message = client.messages.create(
        model=model,
        max_tokens=1500,
        system=_SYSTEM_PROMPT,
        tools=[_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": _TOOL_NAME},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Rubric dimensions:\n{dimension_list}\n\n"
                    f"Prompt to review (delimited by triple quotes):\n\"\"\"\n{prompt_text}\n\"\"\""
                ),
            }
        ],
    )

    tool_use_block = next((b for b in message.content if b.type == "tool_use"), None)
    if tool_use_block is None:
        raise ValueError("Model did not return a structured score — try again.")

    payload = tool_use_block.input
    return ScoreResult(
        prompt=prompt_text,
        scores=payload["scores"],
        feedback=payload["feedback"],
        top_fixes=payload.get("top_fixes", []),
        clarifying_questions=payload.get("clarifying_questions", []),
        rewrite=payload.get("rewrite", ""),
        model=model,
    )
