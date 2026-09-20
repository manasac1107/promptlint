# Sample runs

A worked log of `promptlint` — the judge's output against real cases, chosen to show what it catches beyond "you forgot to mention the audience." The interesting failures aren't missing fields, they're prompts that *look* complete and have a hidden contradiction, or a specification that's individually fine in every part but doesn't cohere as a whole. That's the judge's actual job: catching what a quick skim would miss.

**These are hand-authored to show the expected shape of a review** — written by working through the rubric by hand, the same reasoning the LLM judge automates. They are not a substitute for `examples/validation_report.md`, which is the real, reproducible output from an actual run (see the README's Validation section). Treat this file as "here's what a review looks like and why," and the validation report as "here's the evidence it actually behaves this way."

---

## Pair 1 — competitive intelligence brief

This pair shows the same request before and after acting on the judge's clarifying questions. The "before" version isn't sloppy — it names the market, the competitors, the research dimensions, the audience, and a length limit. It still has three real gaps, and none of them are things a `top_fixes`-style checklist would catch by pattern-matching for missing fields.

### Before

**Input:**
```
You're a market analyst for a pharma company evaluating entry into the GLP-1
obesity drug market. Research what our top 3 competitors (Novo Nordisk, Eli
Lilly, Pfizer) are doing with their GLP-1 pipelines. Summarize their clinical
trial progress, pricing strategy, and market positioning in a 2-page brief
for our executive team, citing PubMed and recent SEC filings as sources.
```

**Output:**
```
promptlint — overall 3.4 / 5

  Context completeness   [4/5]  Market, competitors, research dimensions, and source
                                 types are all named — genuinely strong context.
  Output-format clarity  [4/5]  Length (2 pages) and audience are set; no section
                                 breakdown, but a "brief" implies enough structure.
  Constraint specificity [2/5]  "Recent" SEC filings and PubMed sources have no defined
                                 window — clinical data six months old and six years old
                                 would both technically qualify.
  Audience fit           [3/5]  "Executive team" is named, but the prompt doesn't say
                                 whether they want a recommendation or a neutral summary —
                                 and those produce structurally different documents.
  Clarity                 [3/5]  "Market positioning" bundles pricing tier, target
                                 patient population, and distribution strategy into one
                                 undefined term — three different analysts would fill
                                 it in three different ways.

Top fixes:
  1. Define the recency window for sources explicitly (e.g. "published or filed in the
     last 12 months").
  2. State whether the brief should end in a recommendation or stay descriptive.
  3. Unpack "market positioning" into its actual components, or name which one matters most.

Questions worth answering before you send this:
  1. When two sources disagree — say, a company's investor-day claim versus an
     independent analyst estimate — should the brief pick one, present both, or
     flag the disagreement itself as a finding?
  2. Does "clinical trial progress" mean all phases, or only the phases that are
     actually decision-relevant for a market-entry call (Phase 2+)? Including Phase 1
     noise could bury the signal an exec actually needs.
  3. If this brief has to fit in 2 pages and cover 3 competitors across 3 dimensions,
     is the goal exhaustive coverage or the single most decision-relevant fact per cell?
     Those need very different research strategies.

Suggested rewrite: see "After" below — it resolves these by making each answer explicit
rather than leaving it to the analyst's judgment mid-research.
```

### After

**Input:**
```
You're a market analyst for a pharma company evaluating entry into the GLP-1
obesity drug market. Research what our top 3 competitors (Novo Nordisk, Eli
Lilly, Pfizer) are doing with their GLP-1 pipelines. For each, summarize
clinical trial progress (Phase 2 and later only, published or presented in
the last 12 months), pricing strategy, and target patient population. Write
a 2-page brief for our executive team that ends with an explicit go/no-go
recommendation on market entry, not just a factual summary. Cite only
peer-reviewed PubMed sources and SEC filings; if a claim comes from a company
investor-day presentation rather than an independent source, label it as
company-reported rather than treating it as verified. If two sources
disagree on a material fact, flag the disagreement explicitly rather than
picking one.
```

**Output:**
```
promptlint — overall 4.8 / 5

  Context completeness   [5/5]  Market, competitors, phase scope, and time window are
                                 all explicit.
  Output-format clarity  [5/5]  Length, structure (ends in a recommendation), and the
                                 three comparison dimensions are all specified.
  Constraint specificity [5/5]  Recency window, source-tier labeling, and a disagreement
                                 protocol are all stated — this is doing real editorial
                                 work up front instead of leaving it to the analyst.
  Audience fit           [5/5]  Explicit go/no-go recommendation matches what an exec
                                 audience actually wants from competitive intelligence.
  Clarity                 [4/5]  "Target patient population" replaces the vaguer "market
                                 positioning," though "pricing strategy" is still a
                                 slightly bundled term (list price vs. net price vs.
                                 rebate structure) — a very minor residual gap.

Top fixes:
  1. (Minor) Specify whether "pricing strategy" means list price, net price after
     rebates, or both — pharma pricing is rarely one number.

Suggested rewrite: not needed — the remaining gap is small enough that the current
prompt will produce a usable brief either way.
```

---

## Pair 2 — formulary memo with a contradiction baked in

This is the sharpest catch in the set: a prompt whose parts are each reasonable on their own, but that contradict each other once combined. This is the kind of thing a fixed checklist ("did you specify length? did you specify audience?") cannot catch by construction, because every individual box is checked — the problem is only visible when you read the whole prompt as one instruction.

### Before

**Input:**
```
Write a formulary recommendation memo for our Pharmacy and Therapeutics
committee on whether to add semaglutide to our preferred drug list. Keep it
under one page, but make sure you cover the full clinical evidence base,
cost-effectiveness analysis, and utilization management considerations.
Format as a formal memo.
```

**Output:**
```
promptlint — overall 2.6 / 5

  Context completeness   [4/5]  Drug, committee, and decision type are all clear.
  Output-format clarity  [3/5]  "Formal memo" and "one page" are both stated, but three
                                 substantial content areas are also required — the format
                                 spec and the content spec don't agree with each other.
  Constraint specificity [1/5]  This is a direct contradiction, not a gap: "under one
                                 page" and "full clinical evidence base, cost-effectiveness
                                 analysis, and utilization management" cannot both be
                                 true for a P&T-committee-grade memo. One of these has to
                                 give, and the prompt doesn't say which.
  Audience fit           [4/5]  P&T committee is a specific, well-understood audience in
                                 pharma with known expectations for this document type.
  Clarity                 [1/5]  "Full" evidence base is doing a lot of unstated work —
                                 does it mean exhaustive, or a curated top-line summary?
                                 The contradiction above makes this ambiguity load-bearing
                                 rather than cosmetic.

Top fixes:
  1. Resolve the length-vs-comprehensiveness conflict directly: either extend the page
     limit, or explicitly scope "full" down to a fixed number of studies/figures per
     section.
  2. Decide whether supporting detail belongs in the one-page body or in an appendix
     that isn't subject to the limit.

Questions worth answering before you send this:
  1. When you wrote "full clinical evidence base" inside a one-page limit, did you
     actually mean a comprehensive review, or a curated summary of the 2-3 studies
     that actually drive the recommendation? Those produce very different memos, and
     right now the model has to guess which one you meant.
  2. Would the P&T committee accept the cost-effectiveness analysis as a linked
     appendix, so the memo body stays a genuine one-pager instead of being
     compressed to the point of losing the analysis that justifies the recommendation?

Suggested rewrite: see "After" below.
```

### After

**Input:**
```
Write a formulary recommendation memo for our Pharmacy and Therapeutics
committee on whether to add semaglutide to our preferred drug list. The memo
body must fit on one page: a recommendation up front, then a 2-3 sentence
summary of each of clinical evidence, cost-effectiveness, and utilization
management, citing only the single most decision-relevant study or figure
per section. Put full supporting detail for each section in a labeled
appendix, which is not subject to the one-page limit. Format as a formal
memo with a clear Recommendation, Summary, and Appendix structure.
```

**Output:**
```
promptlint — overall 4.8 / 5

  Context completeness   [5/5]  Drug, committee, decision, and document structure are
                                 all explicit.
  Output-format clarity  [5/5]  Body length, section structure, and the appendix
                                 exemption are all stated precisely.
  Constraint specificity [5/5]  "Single most decision-relevant study or figure per
                                 section" resolves the earlier contradiction directly —
                                 the length and content constraints now agree with
                                 each other.
  Audience fit           [5/5]  Recommendation-first structure matches how a P&T
                                 committee actually consumes these memos.
  Clarity                 [4/5]  Effectively unambiguous; the only residual softness is
                                 that "most decision-relevant" still requires judgment
                                 to apply, which is appropriate — not everything should
                                 be mechanically specified.

Top fixes: none of real significance.

Suggested rewrite: not needed.
```

---

## Single case — a spec that's internally fine but doesn't fit its own audience

Not a before/after pair — this one is included because the failure mode is different from the first two. Nothing here is missing, and nothing contradicts anything else. The output format is precisely specified. The problem only shows up when you check the format against who's actually supposed to use it.

**Input:**
```
Analyze our churn data from the last 2 quarters and identify the top
drivers. Output as a JSON object with driver names, statistical
significance, and effect sizes, so our customer success team can act on it.
```

**Output:**
```
promptlint — overall 3.6 / 5

  Context completeness   [4/5]  Data source and time window are clear.
  Output-format clarity  [5/5]  The JSON schema (driver names, statistical significance,
                                 effect sizes) is genuinely precise — no ambiguity here.
  Constraint specificity [3/5]  No threshold for what counts as a "top" driver — top 3?
                                 Every statistically significant one? Unbounded otherwise.
  Audience fit           [2/5]  This is the real issue: a customer success team is very
                                 unlikely to be able to act on raw JSON containing
                                 statistical-significance values and effect sizes
                                 directly. The output format and the stated audience
                                 don't match, even though each is individually clear.
  Clarity                 [4/5]  The request itself is unambiguous; only the
                                 format-audience mismatch above creates real risk.

Top fixes:
  1. Either change the output to something the customer success team can use directly —
     a short table with plain-language driver descriptions and a suggested action per
     driver — or make explicit that this JSON is an intermediate artifact for an
     analyst or dashboard, not the final deliverable handed to CS.

Questions worth answering before you send this:
  1. Does the customer success team read this JSON directly, or is there a person or
     dashboard between this output and them that translates it? If it's the raw team,
     "statistical significance" and "effect size" aren't decision-usable without
     translation, and the prompt should either ask for that translation or route the
     output somewhere else first.

Suggested rewrite:
  "Analyze our churn data from the last 2 quarters and identify the top 5 drivers
  ranked by effect size. Output as a short table for the customer success team:
  driver, plain-language description, and one suggested action per driver — no
  statistical terminology in the customer-facing version. If you also want the
  underlying statistics for an analyst to review separately, include them as a
  second, clearly labeled JSON block."
```

---

## What this shows

The rubric doesn't just detect absence — it's built to catch three genuinely different failure shapes: a missing field (the basic case, easy to pattern-match), an internal contradiction between two individually-reasonable requirements (the formulary example — no single field is "wrong," but the prompt asks for something impossible), and a coherence mismatch between two correct specifications that don't fit together (the churn example — the format is right, the audience is right, they just don't go together). Only the first kind is something a simple checklist would ever catch. The other two are why this is framed as an LLM-as-judge problem rather than a linter in the traditional static-analysis sense — see the README's "Why LLM-as-judge" section for what that distinction is actually doing here.
