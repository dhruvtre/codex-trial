"""Entry point for running the barebones Claude agent from the terminal."""

from __future__ import annotations

import argparse
import logging
import os
from typing import Any, Mapping

from dotenv import load_dotenv

from claude_agent_demo import AgentConfig, ClaudeAgentBackend, ToolRegistry

LOGGER = logging.getLogger(__name__)


def build_default_tools() -> ToolRegistry:
    """Create a registry populated with a single demonstration tool."""

    registry = ToolRegistry()

    def echo_tool(payload: Mapping[str, Any]) -> str:
        message = payload.get("text", "")
        return f"Echo: {message}" if message else "Echo tool received no text."

    registry.add(
        name="echo",
        description="Return the provided text back to the caller.",
        input_schema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text that should be echoed back.",
                }
            },
            "required": ["text"],
        },
        handler=echo_tool,
    )

    return registry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default=AgentConfig().model,
        help="Claude model identifier used for the agent",
    )
    parser.add_argument(
        "--system-prompt",
        default=AgentConfig().system_prompt,
        help="System prompt that controls the agent's behaviour",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Python logging level (e.g. INFO, DEBUG)",
    )
    parser.add_argument(
        "--no-default-tools",
        action="store_true",
        help="Start the agent without registering the example echo tool.",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if not os.getenv("ANTHROPIC_API_KEY"):
        LOGGER.warning("ANTHROPIC_API_KEY is not set; the agent will not be able to reach Claude.")

    tools = ToolRegistry() if args.no_default_tools else build_default_tools()

    config = AgentConfig(model=args.model, system_prompt=args.system_prompt)
    backend = ClaudeAgentBackend(config=config, tools=tools)
    backend.run_interactive()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
