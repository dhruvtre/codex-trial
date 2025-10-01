"""Utility classes for defining and managing Claude agent tools.

This module exposes a very small registry abstraction that mirrors the
expectations of the Claude Agent SDK.  It allows you to declare tool
metadata in one place and access both the tool schemas that should be
sent to Claude as well as the Python callables that implement them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping


ToolCallable = Callable[[Mapping[str, Any]], Any]


@dataclass(slots=True)
class ToolSpec:
    """Description of a tool that can be exposed to the Claude Agent SDK."""

    name: str
    description: str
    input_schema: Mapping[str, Any]
    handler: ToolCallable
    metadata: Mapping[str, Any] | None = None

    def as_agent_dict(self) -> Dict[str, Any]:
        """Serialize the tool definition into the shape expected by the SDK."""

        tool_dict: Dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "input_schema": dict(self.input_schema),
        }
        if self.metadata:
            tool_dict["metadata"] = dict(self.metadata)
        return tool_dict


@dataclass(slots=True)
class ToolRegistry:
    """Container that keeps track of registered tools.

    The registry exposes convenience helpers for registering tools and
    retrieving either their schema definition or their callables at runtime.
    """

    tools: Dict[str, ToolSpec] = field(default_factory=dict)

    def register(self, spec: ToolSpec) -> None:
        """Register a new tool spec with the registry."""

        if spec.name in self.tools:
            raise ValueError(f"A tool named '{spec.name}' is already registered")
        self.tools[spec.name] = spec

    def add(
        self,
        *,
        name: str,
        description: str,
        input_schema: Mapping[str, Any],
        handler: ToolCallable,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Convenience wrapper around :meth:`register` using keyword args."""

        self.register(
            ToolSpec(
                name=name,
                description=description,
                input_schema=input_schema,
                handler=handler,
                metadata=metadata,
            )
        )

    def schemas(self) -> List[Dict[str, Any]]:
        """Return the SDK schema representation for all registered tools."""

        return [spec.as_agent_dict() for spec in self.tools.values()]

    def handlers(self) -> Dict[str, ToolCallable]:
        """Return a mapping of tool name to implementation callable."""

        return {name: spec.handler for name, spec in self.tools.items()}

    def __iter__(self) -> Iterable[ToolSpec]:
        return iter(self.tools.values())

    def __contains__(self, name: str) -> bool:  # pragma: no cover - simple proxy
        return name in self.tools

    def __len__(self) -> int:  # pragma: no cover - simple proxy
        return len(self.tools)
