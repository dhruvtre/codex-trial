"""Tool definitions for the barebones Claude agent.

This module exposes a helper for constructing an in-process MCP server that
bundles all built-in tools. The server can be referenced from the agent's
configuration, and new tools can be added here without touching the core agent
loop.
"""
from __future__ import annotations

from typing import Iterable

from claude_agent_sdk import SdkMcpTool, create_sdk_mcp_server, tool

__all__ = [
    "TOOLS",
    "TOOL_SERVER_NAME",
    "get_tool_server",
]


@tool("echo", "Echo text back to the caller", {"text": str})
async def echo(args: dict[str, str]) -> dict:
    """Return the provided text as-is.

    This tool is intentionally simple: it proves out that the agent can execute
    a tool call through the Claude Agent SDK. The response format matches the
    expectations of the SDK's MCP bridge (a mapping with a ``content`` list).
    """

    text = args.get("text", "")
    return {"content": [{"type": "text", "text": text}]}


TOOLS: tuple[SdkMcpTool, ...] = (echo,)
"""The collection of statically defined tools shipped with the starter agent."""

TOOL_SERVER_NAME = "starter-tools"
"""Name used for the SDK MCP server that hosts the built-in tools."""


def get_tool_server(tools: Iterable[SdkMcpTool] | None = None):
    """Create the SDK MCP server that exposes the provided tools.

    Parameters
    ----------
    tools:
        Optional iterable of tools to register. When omitted, the function
        falls back to the default :data:`TOOLS` tuple which contains the
        starter utilities bundled with the project.

    Returns
    -------
    McpSdkServerConfig
        A configuration object that can be plugged directly into
        :class:`claude_agent_sdk.types.ClaudeAgentOptions`.
    """

    tool_collection = tuple(TOOLS if tools is None else tools)
    return create_sdk_mcp_server(name=TOOL_SERVER_NAME, tools=list(tool_collection))
