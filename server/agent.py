"""MCP-inspired agent that aggregates responses from multiple LLMs."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List

from openai import AsyncOpenAI

from .llm_clients import (
    EmotionAnalysisClient,
    LLMResult,
    MainReplyClient,
    SystemVariableClient,
)
from .mcp_bus import MCPBus


DEFAULT_MAIN_MODEL = "gpt-4o-mini"
DEFAULT_EMOTION_MODEL = "gpt-4o-mini"
DEFAULT_SYSTEM_MODEL = "gpt-4o-mini"


@dataclass(slots=True)
class MCPAgentResponse:
    """Structured response returned by the agent."""

    reply: str
    emotion: str
    variables: str
    raw: Dict[str, Any]


@dataclass(slots=True)
class LLMRuntimeConfig:
    """Configuration overrides supplied at runtime."""

    api_key: str | None = None
    api_base: str | None = None
    main_model: str | None = None
    emotion_model: str | None = None
    system_model: str | None = None


@dataclass(slots=True)
class LLMRunContext:
    """Per-request context passed through the MCP bus."""

    message: str
    main_client: MainReplyClient
    emotion_client: EmotionAnalysisClient
    system_client: SystemVariableClient


class MCPAgent:
    """Coordinates the LLM calls via an event bus and aggregates the results."""

    def __init__(self, bus: MCPBus | None = None) -> None:
        self.bus = bus or MCPBus()
        self._default_client = AsyncOpenAI()

    async def setup(self) -> None:
        """Register handlers on the bus."""

        await self.bus.subscribe("main", self._handle_main)
        await self.bus.subscribe("emotion", self._handle_emotion)
        await self.bus.subscribe("system", self._handle_system)

    async def _handle_main(self, context: LLMRunContext) -> LLMResult:
        return await context.main_client.run(context.message)

    async def _handle_emotion(self, context: LLMRunContext) -> LLMResult:
        return await context.emotion_client.run(context.message)

    async def _handle_system(self, context: LLMRunContext) -> LLMResult:
        return await context.system_client.run(context.message)

    async def run(
        self,
        message: str,
        config: LLMRuntimeConfig | None = None,
    ) -> MCPAgentResponse:
        """Execute all tasks in parallel and aggregate results."""

        sanitized = self._sanitize_config(config)
        models = self._resolve_models(sanitized)
        client = self._select_client(sanitized)
        context = LLMRunContext(
            message=message,
            main_client=MainReplyClient(model=models["main"], client=client),
            emotion_client=EmotionAnalysisClient(model=models["emotion"], client=client),
            system_client=SystemVariableClient(model=models["system"], client=client),
        )

        topics = ["main", "emotion", "system"]
        publish_tasks = [self.bus.publish(topic, context) for topic in topics]
        results: List[List[LLMResult]] = await asyncio.gather(*publish_tasks)

        flattened: List[LLMResult] = [item for sublist in results for item in sublist]
        response_map: Dict[str, LLMResult] = {result.name: result for result in flattened}

        main_response = response_map.get("main_response")
        emotion_response = response_map.get("emotion_analysis")
        system_response = response_map.get("system_variables")

        return MCPAgentResponse(
            reply=main_response.content if main_response else "",
            emotion=emotion_response.content if emotion_response else "",
            variables=system_response.content if system_response else "",
            raw={name: result.usage for name, result in response_map.items()},
        )

    def _sanitize_config(self, config: LLMRuntimeConfig | None) -> LLMRuntimeConfig:
        """Trim whitespace and normalize empty strings to ``None``."""

        if config is None:
            return LLMRuntimeConfig()

        def _clean(value: str | None) -> str | None:
            if value is None:
                return None
            cleaned = value.strip()
            return cleaned or None

        api_base = _clean(config.api_base)
        if api_base:
            api_base = api_base.rstrip("/")

        return LLMRuntimeConfig(
            api_key=_clean(config.api_key),
            api_base=api_base,
            main_model=_clean(config.main_model),
            emotion_model=_clean(config.emotion_model),
            system_model=_clean(config.system_model),
        )

    def _resolve_models(self, config: LLMRuntimeConfig) -> Dict[str, str]:
        """Merge provided model overrides with defaults."""

        return {
            "main": config.main_model or DEFAULT_MAIN_MODEL,
            "emotion": config.emotion_model or DEFAULT_EMOTION_MODEL,
            "system": config.system_model or DEFAULT_SYSTEM_MODEL,
        }

    def _select_client(self, config: LLMRuntimeConfig) -> AsyncOpenAI:
        """Return an ``AsyncOpenAI`` client honoring runtime overrides."""

        client_kwargs: Dict[str, Any] = {}
        if config.api_key:
            client_kwargs["api_key"] = config.api_key
        if config.api_base:
            client_kwargs["base_url"] = config.api_base

        if client_kwargs:
            return AsyncOpenAI(**client_kwargs)

        return self._default_client


__all__ = ["LLMRuntimeConfig", "MCPAgent", "MCPAgentResponse"]
