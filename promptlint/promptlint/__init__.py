"""promptlint — score a prompt against a fixed rubric before you send it."""

from .scorer import score_prompt, ScoreResult

__all__ = ["score_prompt", "ScoreResult"]
__version__ = "0.1.0"
