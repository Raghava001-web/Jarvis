"""
jarvis/tools/tool_registry.py
Minimal tool abstraction layer for JARVIS.
"""

from datetime import datetime
import asyncio


class Tool:
    def __init__(self, name: str, description: str, function):
        self.name = name
        self.description = description
        self.function = function


class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self._semaphore = asyncio.Semaphore(2)

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def execute(self, tool_name: str, args: dict) -> str:
        tool = self._tools.get(tool_name)
        if not tool:
            return f"Unknown tool: '{tool_name}'"
        try:
            return tool.function(args)
        except Exception as e:
            return f"Tool '{tool_name}' failed: {e}"

    async def execute_async(self, tool_name: str, args: dict) -> str:
        async with self._semaphore:
            return await asyncio.to_thread(self.execute, tool_name, args)

    def list_tools(self) -> list:
        return list(self._tools.keys())


# ---------------------------------------------------------------------------
# Example tools
# ---------------------------------------------------------------------------

def _get_time(args: dict) -> str:
    fmt = args.get("format", "%I:%M %p on %A, %B %d")
    return f"Current time: {datetime.now().strftime(fmt)}"


def _say_hello(args: dict) -> str:
    name = args.get("name", "sir")
    return f"Hello, {name}. All systems operational."


# ---------------------------------------------------------------------------
# Default registry instance (import this everywhere)
# ---------------------------------------------------------------------------

registry = ToolRegistry()
registry.register(Tool("get_time",   "Returns the current time.",            _get_time))
registry.register(Tool("say_hello",  "Greets a person by name.",             _say_hello))
