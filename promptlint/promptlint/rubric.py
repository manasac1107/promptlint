"""The fixed scoring rubric promptlint judges every prompt against.

Five dimensions, each scored 1 (missing/poor) to 5 (fully addressed).
Keeping this list short and fixed is deliberate: a rubric that grows without
bound stops being comparable across runs, which is the whole point of
linting rather than just asking an LLM "is this a good prompt?" in prose.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Dimension:
    key: str
    label: str
    description: str


DIMENSIONS: list[Dimension] = [
    Dimension(
        key="context_completeness",
        label="Context completeness",
        description=(
            "Does the prompt supply the background the task actually needs — "
            "the product/system it concerns, relevant data or documents, prior "
            "decisions — rather than assuming the model already knows it?"
        ),
    ),
    Dimension(
        key="output_format_clarity",
        label="Output-format clarity",
        description=(
            "Is the shape of the desired response specified — length, structure, "
            "sections, a table vs. prose, a specific schema — or is the model left "
            "to guess the format?"
        ),
    ),
    Dimension(
        key="constraint_specificity",
        label="Constraint specificity",
        description=(
            "Are the hard requirements and boundaries stated — must/must-not, tone, "
            "scope limits, what to exclude — rather than left implicit?"
        ),
    ),
    Dimension(
        key="audience_fit",
        label="Audience fit",
        description=(
            "Does the prompt say who the output is actually for, so tone, depth, "
            "and vocabulary can be calibrated (e.g. a C-suite reader vs. an "
            "engineer vs. a customer)?"
        ),
    ),
    Dimension(
        key="clarity",
        label="Clarity (inverse of ambiguity)",
        description=(
            "Is the ask itself unambiguous — a single reasonable interpretation — "
            "or does it contain vague terms, undefined success criteria, or "
            "instructions that could be read multiple ways?"
        ),
    ),
]

DIMENSION_KEYS = [d.key for d in DIMENSIONS]
