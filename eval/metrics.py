"""Deterministic, offline metrics for scoring a catch-up output.

No API key, no network. These are heuristics, not ground truth:
  - citation_accuracy checks that cited file:line locations *exist*.
  - risk_recall checks whether planted issues are *mentioned* (keyword match).
Both can be fooled, so treat them as fast signal, not proof. They are,
however, hard to game accidentally and cheap to run on every skill edit.
"""
from __future__ import annotations

import re

# Matches things like  src/middleware/rateLimit.ts:15
CITE_RE = re.compile(r"([A-Za-z0-9_][\w./-]*\.[A-Za-z]\w*):(\d+)")


def find_citations(text):
    """Return a list of (path, line) tuples cited in the text."""
    return [(m.group(1), int(m.group(2))) for m in CITE_RE.finditer(text)]


def citation_accuracy(text, repo_dir):
    """Fraction of file:line citations that resolve to a real, in-range line.

    Returns (score, valid, total). With zero citations the score is 0.0 --
    grounding in specific locations is part of what the skill is supposed to
    do, so "no citations at all" should not look like a pass.
    """
    cites = find_citations(text)
    total = len(cites)
    if total == 0:
        return 0.0, 0, 0
    valid = 0
    for path, line in cites:
        f = repo_dir / path
        if f.is_file():
            n = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            if 1 <= line <= n:
                valid += 1
    return valid / total, valid, total


def risk_recall(text, planted_issues):
    """Fraction of planted issues surfaced in the text (keyword match).

    Each planted issue lists `detect_any`: if any of those substrings appears
    (case-insensitive), the issue counts as caught.
    Returns (score, caught, total).
    """
    total = len(planted_issues)
    if total == 0:
        return 1.0, 0, 0
    low = text.lower()
    caught = sum(
        1 for issue in planted_issues
        if any(kw.lower() in low for kw in issue["detect_any"])
    )
    return caught / total, caught, total
