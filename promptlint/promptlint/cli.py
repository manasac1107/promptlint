"""Command-line interface for promptlint."""

from __future__ import annotations

import argparse
import json
import sys

from .rubric import DIMENSIONS
from .scorer import DEFAULT_MODEL, ScoreResult, score_prompt

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

    _HAS_RICH = True
except ImportError:  # pragma: no cover - rich is a listed dependency, this is a safety net
    _HAS_RICH = False


def _read_prompt(args: argparse.Namespace) -> str:
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            return f.read()
    if args.prompt:
        return args.prompt
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("No prompt given. Pass text, --file <path>, or pipe via stdin.")


def _print_plain(result: ScoreResult) -> None:
    print(f"\npromptlint — overall score: {result.overall} / 5  (model: {result.model})\n")
    label_by_key = {d.key: d.label for d in DIMENSIONS}
    for key, score in result.scores.items():
        print(f"  [{score}/5] {label_by_key.get(key, key)}")
        print(f"          {result.feedback.get(key, '')}")
    if result.top_fixes:
        print("\nTop fixes:")
        for i, fix in enumerate(result.top_fixes, 1):
            print(f"  {i}. {fix}")
    if result.clarifying_questions:
        print("\nQuestions worth answering before you send this:")
        for i, q in enumerate(result.clarifying_questions, 1):
            print(f"  {i}. {q}")
    if result.rewrite:
        print("\nSuggested rewrite:\n")
        print(result.rewrite)
    print()


def _print_rich(result: ScoreResult) -> None:
    console = Console()
    label_by_key = {d.key: d.label for d in DIMENSIONS}

    table = Table(title=f"promptlint — overall {result.overall} / 5", show_lines=True)
    table.add_column("Dimension", style="bold")
    table.add_column("Score", justify="center", width=6)
    table.add_column("Feedback")

    def score_color(score: int) -> str:
        if score >= 4:
            return "green"
        if score == 3:
            return "yellow"
        return "red"

    for key, score in result.scores.items():
        color = score_color(score)
        table.add_row(
            label_by_key.get(key, key),
            f"[{color}]{score}/5[/{color}]",
            result.feedback.get(key, ""),
        )

    console.print(table)

    if result.top_fixes:
        fixes_text = "\n".join(f"{i}. {fix}" for i, fix in enumerate(result.top_fixes, 1))
        console.print(Panel(fixes_text, title="Top fixes", border_style="cyan"))

    if result.clarifying_questions:
        questions_text = "\n".join(f"{i}. {q}" for i, q in enumerate(result.clarifying_questions, 1))
        console.print(Panel(questions_text, title="Questions worth answering before you send this", border_style="yellow"))

    if result.rewrite:
        console.print(Panel(result.rewrite, title="Suggested rewrite", border_style="magenta"))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="promptlint",
        description="Score a prompt against a fixed rubric before you send it.",
    )
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("prompt", nargs="?", help="The prompt text to score.")
    input_group.add_argument("--file", "-f", help="Read the prompt from a file instead.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of a formatted report.")
    parser.add_argument("--no-color", action="store_true", help="Disable rich formatting even if available.")

    args = parser.parse_args(argv)
    prompt_text = _read_prompt(args)

    result = score_prompt(prompt_text, model=args.model)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return

    if _HAS_RICH and not args.no_color:
        _print_rich(result)
    else:
        _print_plain(result)


if __name__ == "__main__":
    main()
