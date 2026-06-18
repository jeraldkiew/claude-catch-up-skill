"""How to obtain a catch-up / baseline output for a case.

Offline (default): read a pre-generated file from the case's outputs/ dir.
The intended workflow is: run a real catch-up inside Claude Code on the
case's diff, paste the result into outputs/catch_up.md, then score it here.
No API key needed.

Optional (--api): generate the output live via the Anthropic API, using the
skill's SKILL.md as the system prompt for the treatment condition.
"""
from __future__ import annotations

from pathlib import Path


def get_output(case_dir, condition, use_api=False):
    if use_api:
        return _generate_via_api(case_dir, condition)
    f = case_dir / "outputs" / f"{condition}.md"
    if not f.is_file():
        raise FileNotFoundError(
            f"No saved output at {f}.\n"
            f"Either paste an output there, or re-run with --api to generate one."
        )
    return f.read_text(encoding="utf-8")


def _generate_via_api(case_dir, condition):
    """Optional live generation.

    Requires `pip install anthropic` and ANTHROPIC_API_KEY in the environment.
    This is a starting point -- tune the model and prompts for your setup.
    """
    import os

    from anthropic import Anthropic  # type: ignore

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    diff = (case_dir / "changes.diff").read_text(encoding="utf-8")
    skill = (Path(__file__).resolve().parent.parent / "SKILL.md").read_text()

    if condition == "catch_up":
        system = skill  # the skill under test
        user = f"Catch me up on the following change set.\n\n```diff\n{diff}\n```"
    else:  # baseline: a plain assistant, no skill
        system = "You are a helpful coding assistant."
        user = f"Explain the following changes.\n\n```diff\n{diff}\n```"

    msg = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")
