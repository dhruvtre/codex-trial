"""Async backend powered by the Claude Agent SDK."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    Message,
    ResultMessage,
    TextBlock,
)

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class AgentSettings:
    """High-level configuration for the Claude agent session."""

    model: Optional[str] = None
    system_prompt: Optional[str] = None
    allowed_tools: List[str] = field(default_factory=list)
    mcp_servers: dict[str, object] = field(default_factory=dict)
    permission_mode: Optional[str] = None

    def to_options(self) -> ClaudeAgentOptions:
        """Convert the settings into :class:`ClaudeAgentOptions`."""

        return ClaudeAgentOptions(
            model=self.model,
            system_prompt=self.system_prompt,
            allowed_tools=list(self.allowed_tools),
            mcp_servers=dict(self.mcp_servers) if self.mcp_servers else {},
            permission_mode=self.permission_mode,
        )


class ClaudeAgentBackend:
    """Thin convenience wrapper around :class:`ClaudeSDKClient`."""

    def __init__(self, settings: AgentSettings | None = None) -> None:
        self.settings = settings or AgentSettings()
        self._client: ClaudeSDKClient | None = None
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "ClaudeAgentBackend":
        await self.ensure_client()
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        if self._client is not None:
            await self._client.disconnect()
        self._client = None

    async def ensure_client(self) -> ClaudeSDKClient:
        """Initialise the SDK client if needed and return it."""

        if self._client is not None:
            return self._client

        async with self._lock:
            if self._client is not None:
                return self._client

            options = self.settings.to_options()
            self._client = ClaudeSDKClient(options=options)
            await self._client.connect()
            LOGGER.debug("Claude SDK client connected with model %s", options.model)
            return self._client

    async def ask(self, prompt: str) -> str:
        """Send ``prompt`` to Claude and return the assistant's textual reply."""

        client = await self.ensure_client()
        await client.query(prompt)

        text_segments: List[str] = []
        async for message in client.receive_response():
            text_segments.extend(self._extract_text_blocks(message))
        return "\n".join(segment for segment in text_segments if segment)

    @staticmethod
    def _extract_text_blocks(message: Message) -> Iterable[str]:
        """Yield text content from Claude SDK message objects."""

        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    yield block.text
        elif isinstance(message, ResultMessage):
            LOGGER.debug(
                "Received result message: turns=%s cost_usd=%s",
                message.num_turns,
                message.total_cost_usd,
            )
