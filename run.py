"""CLI entrypoint that starts the barebones Claude agent."""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

from agent_backend.agent import AgentConfig, run_agentic_loop


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the barebones Claude agent")
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Initial user prompt passed to the agent. If omitted, the prompt is read from stdin.",
    )
    parser.add_argument(
        "--system-prompt",
        dest="system_prompt",
        help="Override the default system prompt used when configuring Claude.",
    )
    parser.add_argument(
        "--model",
        help="Optional Claude model identifier (for example 'claude-3-5-sonnet-20241022').",
    )
    return parser


def load_prompt_from_stdin() -> str:
    if sys.stdin.isatty():
        raise SystemExit("No prompt provided. Pass one on the command line or pipe it via stdin.")
    return sys.stdin.read().strip()


def validate_environment() -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "ANTHROPIC_API_KEY is not set. Export your Claude API key before running the agent."
        )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    validate_environment()

    prompt = args.prompt or load_prompt_from_stdin()
    if not prompt:
        raise SystemExit("Prompt cannot be empty.")

    config = AgentConfig(system_prompt=args.system_prompt, model=args.model)

    try:
        asyncio.run(run_agentic_loop(prompt, config=config))
    except KeyboardInterrupt:
        return 130

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
