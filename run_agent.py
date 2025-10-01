"""Terminal entry point for the barebones Claude Agent SDK demo."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv

from claude_agent_demo import AgentSettings, ClaudeAgentBackend, ToolLibrary, default_tool_library

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Optional prompt to send immediately without starting the REPL.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Claude model identifier (defaults to SDK value when omitted)",
    )
    parser.add_argument(
        "--system-prompt",
        default=None,
        help="Custom system prompt for the agent session.",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Python logging level (e.g. INFO, DEBUG)",
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="Start the agent without registering the sample echo tool.",
    )
    parser.add_argument(
        "--permission-mode",
        default=None,
        help="Optional permission mode (e.g. acceptEdits, bypassPermissions).",
    )
    return parser.parse_args()


async def interactive_loop(backend: ClaudeAgentBackend) -> None:
    """Simple REPL loop that keeps forwarding prompts to Claude."""

    print("Type 'exit' or press Ctrl+C to end the session.\n")
    while True:
        try:
            prompt = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nStopping agent session.")
            break

        if prompt.strip().lower() in {"exit", "quit"}:
            print("Stopping agent session.")
            break

        response = await backend.ask(prompt)
        if response:
            print(f"Claude: {response}\n")


async def run() -> None:
    load_dotenv()
    args = parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if not os.getenv("ANTHROPIC_API_KEY"):
        LOGGER.warning("ANTHROPIC_API_KEY is not set; Claude will reject requests.")

    tool_library: Optional[ToolLibrary] = None if args.no_tools else default_tool_library()

    settings = AgentSettings(
        model=args.model,
        system_prompt=args.system_prompt,
        permission_mode=args.permission_mode,
    )

    if tool_library:
        settings.allowed_tools = tool_library.allowed_tool_names()
        settings.mcp_servers = {tool_library.name: tool_library.as_mcp_server()}

    async with ClaudeAgentBackend(settings=settings) as backend:
        if args.prompt:
            print(await backend.ask(args.prompt))
        else:
            await interactive_loop(backend)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
