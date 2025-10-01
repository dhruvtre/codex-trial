"""Core orchestration logic for the barebones Claude agent.

The module exposes :class:`BarebonesAgent`, a convenience wrapper around the
Claude Agent SDK's :class:`~claude_agent_sdk.client.ClaudeSDKClient`. The class
creates a minimal configuration that wires the SDK up to the tools defined in
:mod:`agent_backend.tools` and provides a simple async interface for running a
conversation round-trip from the terminal.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import AsyncIterator, Iterable, Iterator, Sequence

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ContentBlock,
    Message,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
)
from claude_agent_sdk.client import ClaudeSDKClient

from .tools import TOOLS, TOOL_SERVER_NAME, get_tool_server

DEFAULT_AGENT_NAME = "barebones"
DEFAULT_SYSTEM_PROMPT = (
    "You are a lightweight assistant that runs in a developer's terminal. "
    "Answer concisely and call tools when it will help the user."
)


@dataclass(slots=True)
class AgentConfig:
    """Configuration bundle used by :class:`BarebonesAgent`.

    Parameters
    ----------
    system_prompt:
        Optional override for the system prompt shared with Claude. When not
        provided the agent falls back to :data:`DEFAULT_SYSTEM_PROMPT`.
    agent_name:
        Name of the agent definition that will be registered with the SDK.
    model:
        Optional Claude model identifier. ``None`` lets the SDK choose a
        sensible default.
    tools:
        Collection of tools to expose. Defaults to the tools exported from
        :mod:`agent_backend.tools`.
    """

    system_prompt: str | None = None
    agent_name: str = DEFAULT_AGENT_NAME
    model: str | None = None
    tools: Sequence[str] | None = None


class BarebonesAgent:
    """Small helper around :class:`ClaudeSDKClient` with a streaming interface."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        if config is None:
            config = AgentConfig()

        self._config = config
        self._tool_objects = TOOLS
        self._tool_names = [tool.name for tool in self._tool_objects]
        if config.tools is not None:
            # allow narrowing the exposed tool set without mutating the defaults
            self._tool_names = [name for name in self._tool_names if name in config.tools]

        agent_prompt = config.system_prompt or DEFAULT_SYSTEM_PROMPT
        selected_tools = [tool for tool in self._tool_objects if tool.name in self._tool_names]
        server_config = get_tool_server(selected_tools)

        self._options = ClaudeAgentOptions(
            system_prompt=agent_prompt,
            allowed_tools=self._tool_names,
            mcp_servers={TOOL_SERVER_NAME: server_config},
            agents={
                config.agent_name: AgentDefinition(
                    description="Barebones agent built with the Claude Agent SDK",
                    prompt=agent_prompt,
                    tools=self._tool_names,
                    model="inherit",
                )
            },
            model=config.model,
        )

    async def run_session(self, prompt: str, *, session_id: str = "default") -> AsyncIterator[str]:
        """Execute one conversation turn and stream Claude's replies.

        The coroutine yields printable chunks so callers can surface partial
        responses as soon as they are available. Tool invocations and their
        results are rendered as structured messages to keep terminal output
        informative.
        """

        async with ClaudeSDKClient(options=self._options) as client:
            await client.query(prompt, session_id=session_id)

            async for message in client.receive_response():
                for line in self._render_message(message):
                    yield line

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _render_message(self, message: Message) -> Iterator[str]:
        """Turn a Claude SDK message into a human-readable stream of lines."""

        if isinstance(message, AssistantMessage):
            yield from self._render_assistant_message(message.content)
            return

        if isinstance(message, ResultMessage):
            cost_fragment = (
                f" | cost: ${message.total_cost_usd:.4f}" if message.total_cost_usd is not None else ""
            )
            yield f"[session complete in {message.duration_ms}ms{cost_fragment}]"
            return

        # Other message types (system, user, events) are not displayed in the
        # default loop but the method is intentionally tolerant so it can be
        # extended later without having to touch the public API.
        return

    def _render_assistant_message(self, blocks: Iterable[ContentBlock]) -> Iterator[str]:
        for block in blocks:
            if isinstance(block, TextBlock):
                yield block.text
            elif isinstance(block, ToolUseBlock):
                payload = json.dumps(block.input, ensure_ascii=False)
                yield f"[tool request] {block.name} -> {payload}"
            elif isinstance(block, ToolResultBlock):
                yield self._format_tool_result(block)

    @staticmethod
    def _format_tool_result(block: ToolResultBlock) -> str:
        """Render a :class:`ToolResultBlock` into a log-friendly string."""

        prefix = "[tool result]"
        status = "error" if block.is_error else "ok"
        if isinstance(block.content, str):
            payload = block.content
        elif isinstance(block.content, list):
            payload = json.dumps(block.content, ensure_ascii=False)
        else:
            payload = ""
        return f"{prefix} {status} ({block.tool_use_id}) {payload}".strip()


async def run_agentic_loop(prompt: str, config: AgentConfig | None = None) -> None:
    """Helper used by ``run.py`` to execute the agent from the command line."""

    agent = BarebonesAgent(config)
    async for line in agent.run_session(prompt):
        print(line)


def run_sync(prompt: str, config: AgentConfig | None = None) -> None:
    """Synchronous convenience wrapper around :func:`run_agentic_loop`."""

    asyncio.run(run_agentic_loop(prompt, config=config))
