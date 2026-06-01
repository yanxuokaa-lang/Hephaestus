from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class ToolRegistryError(ValueError):
    """Raised when tool registration or execution fails."""


ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler
    required_parameters: tuple[str, ...] | None = None

    def to_openai_tool(self) -> dict[str, Any]:
        required = (
            list(self.required_parameters)
            if self.required_parameters is not None
            else list(self.parameters.keys())
        )
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": required,
                    "additionalProperties": False,
                },
            },
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: ToolHandler,
        required_parameters: tuple[str, ...] | None = None,
    ) -> None:
        if not name:
            raise ToolRegistryError("Tool name must be non-empty.")
        if name in self._tools:
            raise ToolRegistryError(f"Tool '{name}' is already registered.")
        if not callable(handler):
            raise ToolRegistryError(f"Tool '{name}' handler must be callable.")
        if required_parameters is not None:
            unknown = sorted(set(required_parameters) - set(parameters.keys()))
            if unknown:
                raise ToolRegistryError(f"Tool '{name}' requires unknown parameters: {unknown}.")
        self._tools[name] = RegisteredTool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            required_parameters=required_parameters,
        )

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            tool = self._tools[name]
        except KeyError as exc:
            raise ToolRegistryError(f"Tool '{name}' is not registered.") from exc
        return tool.handler(arguments)

    def to_openai_tools(self) -> list[dict[str, Any]]:
        return [tool.to_openai_tool() for tool in self._tools.values()]
