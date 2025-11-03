"""Async LLM client abstractions used by the MCP-style agent.

This module encapsulates multiple logical clients that talk to the OpenAI
Chat Completions API. Each client focuses on a different task (main reply,
emotion analysis, system variable extraction) but reuses the same
``AsyncOpenAI`` connection under the hood.

The module intentionally keeps the payloads small and provides structured
return values to make it easier for the agent layer to aggregate results.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LLMResult:
    """Normalized result returned by each logical client."""

    name: str
    content: str
    usage: Dict[str, Any]


class BaseLLMClient:
    """Base helper that calls the OpenAI Chat Completions API asynchronously."""

    def __init__(
        self,
        model: str,
        system_prompt: str,
        name: str,
        client: Optional[AsyncOpenAI] = None,
    ) -> None:
        self._client = client or AsyncOpenAI()
        self._model = model
        self._system_prompt = system_prompt
        self._name = name

    async def _create_completion(self, message: str) -> LLMResult:
        """Call the OpenAI Chat Completions API asynchronously."""
        logger.debug("%s: creating completion", self._name)
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content if response.choices else ""
        usage = {
            "prompt_tokens": getattr(response.usage, "prompt_tokens", None),
            "completion_tokens": getattr(response.usage, "completion_tokens", None),
            "total_tokens": getattr(response.usage, "total_tokens", None),
        }
        logger.debug("%s: received completion", self._name)
        return LLMResult(name=self._name, content=content or "", usage=usage)

    async def run(self, message: str) -> LLMResult:
        return await self._create_completion(message)


class MainReplyClient(BaseLLMClient):
    """Produces a conversational reply to the user."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        client: Optional[AsyncOpenAI] = None,
    ) -> None:
        super().__init__(
            model=model,
            system_prompt=(
                "You are the primary conversational agent. Provide helpful, "
                "detailed responses and reference the analyses coming from the "
                "supporting tools when appropriate."
            ),
            name="main_response",
            client=client,
        )


class EmotionAnalysisClient(BaseLLMClient):
    """Identifies the dominant emotion expressed by the user."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        client: Optional[AsyncOpenAI] = None,
    ) -> None:
        super().__init__(
            model=model,
            system_prompt=(
                "You are an affective computing assistant. Identify the single "
                "dominant emotion the user is expressing and explain it "
                "briefly. Respond in JSON with keys 'emotion' and 'explanation'."
            ),
            name="emotion_analysis",
            client=client,
        )


class SystemVariableClient(BaseLLMClient):
    """Extracts structured variables useful for downstream automation."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        client: Optional[AsyncOpenAI] = None,
    ) -> None:
        super().__init__(
            model=model,
            system_prompt=(
                "You extract system variables from user input. Provide a JSON "
                "object with keys 'intent', 'priority', and 'entities' (array)."
            ),
            name="system_variables",
            client=client,
        )


async def warm_up_clients(timeout: float = 2.0) -> None:
    """Run a very small prompt to ensure the clients are ready.

    This is optional but helps expose authentication issues early.
    """

    async def _ping(client: BaseLLMClient) -> None:
        try:
            await asyncio.wait_for(client.run("ping"), timeout=timeout)
        except Exception as exc:  # noqa: BLE001 - log and continue
            logger.warning("Warm-up for %s failed: %s", client._name, exc)

    clients = [MainReplyClient(), EmotionAnalysisClient(), SystemVariableClient()]
    await asyncio.gather(*(_ping(client) for client in clients))


__all__ = [
    "LLMResult",
    "MainReplyClient",
    "EmotionAnalysisClient",
    "SystemVariableClient",
    "warm_up_clients",
]
