"""Backend utilities for running a Claude agent.

This module wires together a Claude Agent session using the Agent SDK.
It intentionally keeps the logic small and readable so that it can be used
as a starting point for experimenting with additional tools or prompting
strategies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List, Mapping, Sequence

from anthropic import Anthropic

from .tools import ToolRegistry

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class AgentConfig:
    """Configuration for the Claude agent backend."""

    model: str = "claude-3-5-sonnet-20240620"
    system_prompt: str = (
        "You are a helpful coding assistant. Keep responses concise unless "
        "additional detail is explicitly requested."
    )
    name: str = "Barebones Claude Agent"
    max_tokens: int = 1024
    temperature: float = 0.2


class ClaudeAgentBackend:
    """Tiny convenience wrapper around the Claude Agent SDK."""

    def __init__(
        self,
        *,
        client: Anthropic | None = None,
        config: AgentConfig | None = None,
        tools: ToolRegistry | None = None,
    ) -> None:
        self.client = client or Anthropic()
        self.config = config or AgentConfig()
        self.tools = tools or ToolRegistry()

        # Lazily created handles once the agent is bootstrapped.
        self._agent_id: str | None = None
        self._session_id: str | None = None

        # Resolve the Agent SDK entry points dynamically so that the code
        # fails fast with a helpful message when the installed SDK is too old.
        try:
            self._agents_resource = self.client.beta.agents
        except AttributeError as exc:  # pragma: no cover - defensive branch
            raise RuntimeError(
                "The installed `anthropic` package does not expose the Agent SDK. "
                "Upgrade to a version that includes the Claude Agent SDK."
            ) from exc

        for attr in ("sessions", "messages"):
            if not hasattr(self._agents_resource, attr):  # pragma: no cover
                raise RuntimeError(
                    "The Claude Agent SDK seems incomplete. Expected the agents "
                    f"resource to provide `{attr}`."
                )

        message_resource = self._agents_resource.messages
        for method in ("create", "respond", "poll"):
            if not hasattr(message_resource, method):  # pragma: no cover
                raise RuntimeError(
                    "The Claude Agent SDK messages resource is missing the "
                    f"`{method}` operation."
                )

    # ------------------------------------------------------------------
    # Bootstrapping helpers
    # ------------------------------------------------------------------
    def _ensure_agent_created(self) -> str:
        if self._agent_id is not None:
            return self._agent_id

        LOGGER.debug("Creating Claude agent using model %s", self.config.model)
        agent = self._agents_resource.create(
            model=self.config.model,
            name=self.config.name,
            instructions=self.config.system_prompt,
            tools=self.tools.schemas(),
        )
        self._agent_id = agent["id"] if isinstance(agent, Mapping) else agent.id
        return self._agent_id

    def _ensure_session_created(self) -> str:
        if self._session_id is not None:
            return self._session_id

        agent_id = self._ensure_agent_created()
        sessions_resource = self._agents_resource.sessions
        session = sessions_resource.create(agent_id=agent_id)
        self._session_id = (
            session["id"] if isinstance(session, Mapping) else session.id
        )
        return self._session_id

    # ------------------------------------------------------------------
    # Conversation handling
    # ------------------------------------------------------------------
    def run_interactive(self) -> None:
        """Start an interactive REPL loop with the Claude agent."""

        session_id = self._ensure_session_created()
        print("Type 'exit' or Ctrl+C to stop.\n")
        while True:
            try:
                user_message = input("You: ")
            except (EOFError, KeyboardInterrupt):  # pragma: no cover - CLI guard
                print("\nStopping agent session.")
                break

            if user_message.strip().lower() in {"exit", "quit"}:
                print("Stopping agent session.")
                break

            agent_reply = self.send_message(session_id, user_message)
            if agent_reply:
                print(f"Claude: {agent_reply}\n")

    def send_message(self, session_id: str, content: str) -> str:
        """Send a user message to the Claude agent and return its response."""

        messages_resource = self._agents_resource.messages
        response = messages_resource.create(
            session_id=session_id,
            content=[{"type": "text", "text": content}],
        )
        return self._collect_response_text(response)

    # ------------------------------------------------------------------
    # Response handling utilities
    # ------------------------------------------------------------------
    def _collect_response_text(self, response: Any) -> str:
        """Extract textual content from an agent message response."""

        content: Sequence[Mapping[str, Any]]
        if hasattr(response, "content"):
            content = response.content  # type: ignore[assignment]
        elif isinstance(response, Mapping):  # pragma: no cover - fallback path
            content = response.get("content", [])
        else:  # pragma: no cover - defensive guard
            raise TypeError("Unsupported response object returned by SDK")

        text_parts: List[str] = []
        tool_calls: List[Mapping[str, Any]] = []
        for item in content:
            match item.get("type"):
                case "text":
                    text_parts.append(item.get("text", ""))
                case "tool_use":
                    tool_calls.append(item)
                case _:
                    LOGGER.debug("Ignoring response block of type %s", item.get("type"))

        # Execute tool calls sequentially.  The basic loop posts results back
        # using the Agent SDK which will in turn yield a follow-up assistant
        # response once all tools have been satisfied.
        for call in tool_calls:
            result_text = self._execute_tool_call(call)
            messages_resource = self._agents_resource.messages
            messages_resource.respond(
                session_id=self._ensure_session_created(),
                tool_result={
                    "tool_use_id": call.get("id"),
                    "output": result_text,
                },
            )

        # If we executed tool calls we expect the agent to send a follow-up
        # message that contains the actual assistant content.
        if tool_calls:
            follow_up = self._agents_resource.messages.poll(
                session_id=self._ensure_session_created()
            )
            return self._collect_response_text(follow_up)

        return "\n".join(part for part in text_parts if part)

    def _execute_tool_call(self, call: Mapping[str, Any]) -> str:
        tool_name = call.get("name")
        if not tool_name:
            raise ValueError("Tool call is missing a name field")

        handlers = self.tools.handlers()
        if tool_name not in handlers:
            raise KeyError(f"No handler registered for tool '{tool_name}'")

        handler = handlers[tool_name]
        arguments = call.get("input", {})
        LOGGER.debug("Running tool '%s' with %s", tool_name, arguments)
        result = handler(arguments)
        return str(result)
