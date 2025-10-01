"""Barebones Claude agent demo package."""

from .backend import ClaudeAgentBackend, AgentConfig
from .tools import ToolRegistry, ToolSpec

__all__ = [
    "ClaudeAgentBackend",
    "AgentConfig",
    "ToolRegistry",
    "ToolSpec",
]
