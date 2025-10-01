"""Helpers for defining Claude Agent SDK tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from claude_agent_sdk import SdkMcpTool, create_sdk_mcp_server, tool


@dataclass(slots=True)
class ToolLibrary:
    """Maintain a collection of SDK MCP tools under a single server name."""

    name: str = "demo"
    version: str = "1.0.0"
    tools: Dict[str, SdkMcpTool[Any]] = field(default_factory=dict)

    def register(self, sdk_tool: SdkMcpTool[Any]) -> None:
        """Register ``sdk_tool`` with the library."""

        if sdk_tool.name in self.tools:
            raise ValueError(f"A tool named '{sdk_tool.name}' is already registered")
        self.tools[sdk_tool.name] = sdk_tool

    def extend(self, sdk_tools: Iterable[SdkMcpTool[Any]]) -> None:
        """Register multiple tools at once."""

        for sdk_tool in sdk_tools:
            self.register(sdk_tool)

    def as_mcp_server(self) -> Dict[str, Any]:
        """Return an MCP server config that exposes the registered tools."""

        return create_sdk_mcp_server(
            name=self.name,
            version=self.version,
            tools=list(self.tools.values()),
        )

    def allowed_tool_names(self) -> List[str]:
        """Return fully-qualified tool names recognised by Claude."""

        prefix = f"mcp__{self.name}__"
        return [f"{prefix}{tool.name}" for tool in self.tools.values()]


@tool("echo", "Echo the provided text", {"text": str})
async def echo_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal sample tool that mirrors the input text back to the caller."""

    text = payload.get("text", "")
    if not isinstance(text, str):
        text = str(text)
    message = text or "Echo tool received no text."
    return {
        "content": [
            {
                "type": "text",
                "text": message,
            }
        ]
    }


def default_tool_library() -> ToolLibrary:
    """Create a :class:`ToolLibrary` seeded with the ``echo`` tool."""

    library = ToolLibrary(name="demo")
    library.register(echo_tool)
    return library
