# Async MCP Aggregation Agent

A minimal MCP-inspired multi-model aggregation agent with a FastAPI backend and a vanilla HTML/JS frontend. The agent fan-outs user prompts to three OpenAI Chat Completion tasks (main reply, emotion analysis, and system variable extraction) and aggregates the results for display.

👉 想阅读中文简介？请查看 [README_zh.md](README_zh.md)。

## Project Structure

```
.
├── requirements.txt
├── server
│   ├── agent.py
│   ├── llm_clients.py
│   ├── main.py
│   └── mcp_bus.py
└── web
    ├── app.js
    ├── index.html
    └── style.css
```

## Prerequisites

- Python 3.10+
- An OpenAI-compatible API endpoint and key (defaults assume OpenAI `gpt-4o-mini`)

Export your API key before running the server if you are using environment defaults:

```bash
export OPENAI_API_KEY="sk-your-key"
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Project

1. Start the FastAPI backend (the project uses port **8850** by default):

   ```bash
   uvicorn server.main:app --reload --port 8850
   ```

   The API will be available at http://localhost:8850.

2. Open the frontend by navigating to `web/index.html` in your browser (e.g. using a static server or the browser's file:// protocol). When served from a different origin, ensure CORS allows access.

3. In the **LLM API Settings** panel, configure the API base URL, API key, and optional model overrides. These settings are saved to `sessionStorage` for convenience and are sent with each request so you can use any OpenAI-format API gateway.

4. Enter a message, send it, and view the aggregated results.

## Notes

- The backend performs asynchronous calls to the OpenAI API and aggregates the responses.
- `server/llm_clients.py` contains helper classes for the different logical tasks.
- `server/mcp_bus.py` simulates an MCP event bus for decoupled handler execution.

## Development Tips

- Adjust prompts or models in `server/llm_clients.py` as needed, or override the models per request from the frontend settings panel.
- You can optionally warm up the clients by invoking `warm_up_clients()` on startup if you want to pre-flight the configuration.

Enjoy exploring multi-model aggregation!
