"""Simple asynchronous message bus to simulate MCP routing."""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Awaitable, Callable, Dict, List, Protocol, Any


class MCPEventHandler(Protocol):
    async def __call__(self, payload: Any) -> Any:  # pragma: no cover - protocol
        ...


class MCPBus:
    """A minimal in-memory pub/sub bus for the MCP-inspired architecture."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[MCPEventHandler]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, topic: str, handler: MCPEventHandler) -> None:
        async with self._lock:
            self._handlers[topic].append(handler)

    async def publish(self, topic: str, payload: Any) -> List[Any]:
        async with self._lock:
            handlers = list(self._handlers.get(topic, []))
        if not handlers:
            return []
        tasks: List[Awaitable[Any]] = [handler(payload) for handler in handlers]
        return await asyncio.gather(*tasks)


__all__ = ["MCPBus", "MCPEventHandler"]
