"""FastAPI application exposing the MCP agent."""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agent import LLMRuntimeConfig, MCPAgent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Async MCP Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    api_key: str | None = None
    api_base: str | None = None
    main_model: str | None = None
    emotion_model: str | None = None
    system_model: str | None = None


class ChatResponse(BaseModel):
    reply: str
    emotion: str
    variables: str
    raw: Dict[str, Any]


agent = MCPAgent()


@app.on_event("startup")
async def _startup() -> None:
    logger.info("Setting up MCP agent")
    await agent.setup()


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    try:
        runtime_config = LLMRuntimeConfig(
            api_key=request.api_key,
            api_base=request.api_base,
            main_model=request.main_model,
            emotion_model=request.emotion_model,
            system_model=request.system_model,
        )
        result = await agent.run(request.message, config=runtime_config)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Agent execution failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(
        reply=result.reply,
        emotion=result.emotion,
        variables=result.variables,
        raw=result.raw,
    )


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "MCP Agent backend is running."}
