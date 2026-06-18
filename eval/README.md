# Eval harness for the `catch-up` skill

A small, runnable rig that measures whether the skill actually helps —
by scoring its output against a known answer key and comparing it to a
**baseline** (a plain "explain these changes" with no skill). Usefulness is
the *delta* between the two; a number on its own means nothing.

## Run it

From the repo root (no dependencies, no API key):

```bash
python eval/run_eval.py
```

You'll get a per-case and averaged table plus the catch-up-vs-baseline delta.
The shipped sample case is rigged so a good catch-up clearly beats the baseline —
that's just to show the harness working; the real signal comes from *your* cases
and *your* outputs.

## What it measures (offline, deterministic)

| Metric | Tests | How |
|---|---|---|
| **citation** | annotated tour / not hallucinating | % of `file:line` cites that resolve to a real, in-range line in the case's `repo/` snapshot |
| **risk** | "surface risks unasked" | % of planted issues mentioned (keyword match from the gold key) |

These are heuristics — citation accuracy can't tell if a *real* line is the
*right* line, and risk recall is keyword-based so it can be gamed. They're cheap,
hard to fool by accident, and good for catching regressions when you edit the
skill. The richer judgments (did the human actually understand? did it invent a
rationale?) need an LLM judge — see "Hooks" below.

## How outputs are produced

Two ways, set in `runners.py`:

- **Offline (default):** the harness reads `cases/<name>/outputs/catch_up.md` and
  `.../baseline.md`. The intended workflow: run a real catch-up inside Claude Code
  on the case's `changes.diff`, paste the result into `catch_up.md`, and score it.
- **`--api`:** generate outputs live via the Anthropic API (`pip install anthropic`,
  set `ANTHROPIC_API_KEY`). Uses `SKILL.md` as the system prompt for the treatment.

## Add a case

Copy `cases/ratelimit/` and edit:

```
cases/<name>/
  changes.diff          # the change set (what Claude did)
  repo/                 # snapshot of the files AFTER the change (for citation checks)
  gold.json             # intent, blast_radius, planted_issues[], key_locations[]
  outputs/
    catch_up.md         # the skill's output (paste from Claude Code, or --api)
    baseline.md         # a no-skill "explain these changes" output
```

`gold.json` → `planted_issues[].detect_any` is the list of substrings that count
as "this risk was surfaced". Plant 2–3 real, subtle issues per case (a fail-open,
a scaling limit, an untested edge) and keep the keywords specific.

## Hooks left for later (LLM-judged)

The highest-value metrics need a model in the loop and are intentionally **not**
implemented yet:

- **comprehension** — feed the catch-up to a fresh "student" agent that hasn't
  seen the code, have it answer a quiz from `gold.json`, score correctness.
- **hallucinated-why** — judge flags any stated rationale unsupported by the diff.
- **downstream task** — student attempts a small modification; pass/fail.

`runners.py` already shows the API-call shape; extending it to a student/judge
loop is the natural next step.
