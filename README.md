# promptlint

An LLM-as-judge review of a prompt, run *before* you send it — instead of finding out it was underspecified from a bad response.

## The premise

A prompt is a stand-in for a decision. Before "write a PRD" or "summarize this feedback" ever reaches a model, someone has to have already worked out who it's for, what's actually in scope, what a good outcome looks like, and which parts of the ambiguity are genuinely fine to leave open. Handing off a vague prompt doesn't skip that decision — it just moves it downstream, onto the model, which will make the call anyway, quietly, and not necessarily the way you would have.

So before asking whether a prompt is *written* well, this project asks an earlier, less comfortable question: have we actually thought it through ourselves? Not "is this phrased clearly," but "do I know what I want here — and, just as importantly, what I don't want?" A lot of what looks like a prompting problem is really a scoping problem wearing a prompting costume: the prompt reads vague because the thinking underneath it is still vague, and no amount of better phrasing fixes that on its own.

That's also, honestly, where the case for human judgment actually gets made rather than just asserted. It isn't that a person writes a better sentence than a model can. It's that a person is the one who gets to decide what the goalposts are, which tradeoffs are acceptable, and what "good" means for this specific situation — and none of that shows up unless someone pauses to work it out before hitting send. This tool doesn't replace that pause. It's a small, genuine attempt to make it a little more structured: to ask, out loud and on paper, the questions a careful person would already be asking themselves — so the scoping happens on purpose, not by accident.

## Why this exists

Most prompt failures aren't the model's fault — they're missing context, an unspecified output format, no stated audience, or an ambiguous ask that could reasonably be read three different ways. Experienced prompt-writers catch these by instinct. Everyone else finds out after the fact, on the third re-prompt.

`promptlint` is a small, single-purpose tool built around one technique: use a second LLM call as a *judge* of the prompt itself, before the prompt ever reaches the model that would act on it. Give it a prompt, the judge scores it (not the eventual response — the prompt, in isolation) against five fixed dimensions, tells you specifically what's missing, asks the questions you'd need to answer to close the real gaps, and — only when there's nothing left worth thinking through — rewrites it. See [`SAMPLE_RUNS.md`](SAMPLE_RUNS.md) for what the judge actually catches: not just missing fields, but internal contradictions and audience/format mismatches that only show up when you read a whole prompt as one instruction, not a checklist.

The questions matter more than the rewrite for anything beyond a throwaway prompt — a rewrite hands you an answer, a question makes you actually scope the problem you were vague about. If a prompt says "improve retention," the useful output isn't a nicer sentence, it's "over what window, and does a paused account count?"

It does one thing on purpose. It is not an agent, it does not loop, it does not remember anything between runs — it's a linter, in the same sense `eslint` is a linter: a fast, deterministic-feeling check you run before you ship the thing, not a system you hand the task to.

## Why LLM-as-judge

"LLM-as-judge" — using a model call to evaluate an artifact against criteria, instead of a human or a hand-coded rule — covers two standard configurations in the evals literature: *pairwise* (show the judge two candidate responses, ask which is better — how a lot of RLHF preference data and leaderboards work) and *pointwise* (show it one artifact alone, score it against a fixed rubric, no comparison — the configuration benchmarks like MT-Bench also use to grade a single response). This tool uses the pointwise configuration, applied to a prompt before it's ever run, rather than to a model's output after the fact — the mechanism is the standard one, the artifact being judged is just earlier in the pipeline than usual.

Pointwise judging comes with known failure modes regardless of what it's scoring. This tool is structured around mitigating the specific ways a judge call tends to go wrong:

- **Leniency bias** — judges tend to rate things more favorably than a careful human would, especially when there's nothing to compare against. Mitigated by an explicit system-prompt instruction that most first-draft prompts should *not* score 5s across the board, and by asking for the single most non-obvious gap rather than a generic one when a prompt is already mostly complete — see the "looks complete, isn't" examples in `SAMPLE_RUNS.md`.
- **Verbosity / format bias** — judges can reward answers that merely *look* thorough (long, well-formatted) over answers that are actually correct. Mitigated by forcing structured tool-use output against a fixed schema rather than free-text scoring, so there's no surface area for the judge to pad.
- **Position/self-preference bias** — well-documented in *pairwise* judge setups (comparing response A vs. response B), where a judge favors whichever position or style it prefers regardless of quality. This tool sidesteps that class of bias by construction: it never compares two things, it scores one prompt against a fixed, independent rubric.
- **Inconsistency across runs** — the same prompt can get a somewhat different score on different calls, since the judge is itself a model with sampling variance. Not fully solved in v0.1 (see Future Directions below); the fixed rubric and forced schema narrow the variance but don't eliminate it.

Naming these explicitly, and showing where the design does and doesn't address them, is the difference between "I used an LLM to score things" and actually engaging with why LLM-as-judge is a real, imperfect technique rather than a magic evaluation button.

## The rubric

Every prompt is scored 1–5 on each of:

| Dimension | What it checks |
|---|---|
| **Context completeness** | Does the prompt supply the background the task needs — the product/system, relevant data, prior decisions — rather than assuming the model already knows it? |
| **Output-format clarity** | Is the shape of the response specified (length, structure, table vs. prose, a schema), or is the model left to guess? |
| **Constraint specificity** | Are the hard requirements stated — must/must-not, tone, scope, exclusions — or left implicit? |
| **Audience fit** | Does the prompt say who the output is for, so tone and depth can be calibrated? |
| **Clarity** | Is the ask unambiguous, with a single reasonable interpretation? |

The rubric is intentionally short and fixed rather than configurable per-run — a rubric that changes shape every time stops being comparable across prompts, which defeats the point of scoring at all.

## Install

```bash
pip install -e .
export ANTHROPIC_API_KEY=sk-ant-...
```

(Not yet published to PyPI — clone the repo and install locally.)

## Use

```bash
promptlint "Write a PRD for our new feature."
```

```
promptlint — overall 2.2 / 5

  Context completeness   [1/5]  No product, market, or user context given at all.
  Output-format clarity  [2/5]  "PRD" implies structure but no sections or length are specified.
  Constraint specificity [2/5]  No tone, scope, or length constraints stated.
  Audience fit           [2/5]  No reader specified — engineering lead and exec would need very different PRDs.
  Clarity                [4/5]  The core ask ("write a PRD") is unambiguous even though it's underspecified.

Top fixes:
  1. Name the product and the problem the feature solves.
  2. Specify who will read this PRD and what they'll do with it.
  3. Give a section structure (Problem, Goals, Non-Goals, Success Metrics, Open Questions).

Questions worth answering before you send this:
  1. Who actually reads this — an engineering lead scoping the build, or an exec approving budget? The document changes shape depending on the answer.
  2. What problem is "our new feature" solving, and for whom — is there a metric it's meant to move?

Suggested rewrite:
  [a rewritten, fully-specified version of the prompt]
```

Other ways to run it:

```bash
promptlint --file my_prompt.txt          # score a prompt from a file
echo "my prompt" | promptlint            # score a prompt piped via stdin
promptlint "..." --json                  # machine-readable output for scripting
promptlint "..." --model claude-opus-4-5 # override the default model
```

## Validation

Rather than assert the rubric works, `examples/run_validation.py` runs it against nine example prompts spanning deliberately weak, medium, and strong cases (`examples/example_prompts.json`) and writes the actual scored output to `examples/validation_report.md`. That file is checked into this repo — it's real output from a real run, not hand-written numbers, and it's the reproducibility check for the rubric: weak prompts should score low, strong ones should score high, and the reasoning in the feedback should hold up to a human reading it.

Reproduce it yourself:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python examples/run_validation.py
```

See [`SAMPLE_RUNS.md`](SAMPLE_RUNS.md) for a worked, readable log — including two before/after pairs showing a flawed prompt fixed based on the judge's own clarifying questions — if you want to see the shape of a review before running it yourself.

## Customizing the rubric

The five dimensions aren't hardcoded into the scoring logic — they're a plain list in `promptlint/rubric.py`, and everything else (the tool schema Claude is forced to fill in, the CLI's table labels) is generated from that list. To adapt the rubric to a specific domain:

1. Edit the `DIMENSIONS` list in `rubric.py` — add, remove, or reword a `Dimension(key=..., label=..., description=...)` entry.
2. Nothing else needs to change. `scorer.py` builds the JSON schema from `DIMENSION_KEYS`, and `cli.py` reads labels back off `DIMENSIONS`, so a new dimension shows up in the score table and the JSON output automatically.

This is what a domain-specific fork would actually look like — for example, a pharma or regulated-industry variant might swap in a `regulatory_compliance` dimension in place of (or alongside) `audience_fit`, checking whether the prompt specifies what claims can and can't be made about a drug or device.

## Future directions

Deliberately out of scope for v0.1, in rough order of how much they'd actually change the tool:

- **Iterative refinement (v2 candidate).** The natural next step is closing the loop this version stops short of: draft a prompt, actually run it, score the *output* against success criteria (not just score the prompt in isolation), and revise until the score plateaus. This only pays for itself once a prompt is reused enough times to amortize the extra API calls the loop costs — worth shipping with a break-even calculator alongside it, not just the loop itself.
- **CI integration.** A pre-commit hook or GitHub Action that lints the prompts checked into a repo (e.g. an agent's system prompts) on every pull request, so a prompt regression gets caught the same way a failing test would, instead of surfacing later as a worse model response.
- **Score history / trend tracking.** A lightweight local log (a single JSONL file, not a database) of past runs, so repeat users of the same prompt template can see whether their prompting is actually improving over time rather than judging by feel.
- **Multi-model comparison.** Score the same prompt with two or three different models side by side — useful both for catching rubric-scoring inconsistencies and for the more interesting question of whether "a good prompt" is even model-independent.
- **Domain-specific rubric presets.** Ship a couple of ready-made alternate rubrics (see Customizing above) rather than requiring everyone to hand-edit `rubric.py` — a PM-flavored preset and a regulated-industry preset are the two most obvious first candidates.
- **Judge reliability via self-consistency.** Run the same prompt through the judge N times (or across two different judge models) and report a score range plus agreement level instead of a single number — directly addresses the inconsistency-across-runs limitation named in "Why LLM-as-judge" above, and turns "the judge said 3.4" into "the judge said 3.2–3.6 across 5 runs," which is a meaningfully more honest claim.

## Design notes

- **Questions over answers, where it matters.** The rewrite is genuinely useful for a prompt that's mostly there — but for a prompt with a real, unresolved gap (an undefined success metric, an unstated scope boundary), silently rewriting it papers over a decision the author still needs to make. The clarifying questions are deliberately phrased to force that decision rather than make it for you.
- **Structured output, not text-parsing.** The scorer forces Claude to call a tool with a fixed JSON schema rather than asking for JSON in a markdown block and regexing it out. This is the difference between a score you can trust programmatically and a score you're hoping parses.
- **No loop, on purpose.** An earlier version of this idea was a self-refining agent that drafts, runs, scores, and revises a prompt automatically. Scoped that down deliberately: iteration adds real value for prompts that get reused many times (the loop's own token cost only pays for itself past a break-even reuse count), but for a single review, one honest judge call — score, feedback, clarifying questions, and a rewrite only when nothing's left to decide — is the right amount of machinery. Iteration is a plausible v2, not a requirement for v1.
- **Portable over integrated.** This calls the Anthropic API directly with a user-supplied key rather than running only inside an agent harness, so it works as an installable CLI tool anyone can run, not just inside one particular environment.

## Project status

v0.1 — built as a scoped, single-purpose companion piece to a broader exploration of agentic tools for product management. See the rubric and design notes above for what's deliberately *not* in scope yet.

## License

MIT
