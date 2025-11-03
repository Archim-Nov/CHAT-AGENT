# 异步 MCP 聚合 Agent 项目简介

本项目实现了一个可运行的异步多模型聚合 Agent，遵循 MCP 的事件分发思路，提供完整的后端服务与前端界面：

- **后端：** 使用 Python、FastAPI 与 asyncio 组合，负责接收请求、并行调度多个 LLM 调用并聚合结果。
- **前端：** 采用原生 HTML、JavaScript 与 CSS 构建，提供聊天输入、结果展示以及 OpenAI 格式 API 设置面板。

## 功能概览

1. **多模型并行调用**：针对用户输入，后端通过 `MCPAgent` 同时触发三个 LLM 任务：
   - `llm_main`：生成主回复。
   - `llm_emotion`：执行情感分析。
   - `llm_system`：提取系统变量。
2. **运行时配置**：前端允许用户输入自定义的 OpenAI API Base URL、API Key 以及模型名称，设置会随每次请求发送到后端。
3. **结果聚合展示**：前端将后端返回的主回复、情绪标签和变量列表分别呈现，形成完整的对话反馈。

## 核心实现

- `server/main.py`：定义 FastAPI 应用，暴露 `/chat` 接口并处理跨域访问，端口默认 8850。
- `server/agent.py`：实现 `MCPAgent`，负责组合 MCP 事件总线与各类 LLM 客户端，提供统一的 `run_dialogue` 接口。
- `server/mcp_bus.py`：模拟 MCP 事件分发机制，按照不同的事件类型调度处理器并收集结果。
- `server/llm_clients.py`：封装 OpenAI Chat Completions 的异步客户端，按任务类型构造提示词与请求参数。
- `web/index.html`、`web/app.js`、`web/style.css`：提供页面结构、交互逻辑与样式，内置 LLM API 设置面板，并通过 `fetch` 与后端交互。

## 运行流程

1. 用户访问 `web/index.html`，在设置面板中填写（或沿用默认）OpenAI 兼容 API 信息。
2. 用户在输入框中输入消息并点击发送，前端将消息与 API 设置通过 `POST /chat` 请求发送到后端。
3. 后端 `MCPAgent` 并行调用三个 LLM 客户端获取主回复、情绪与系统变量，并通过 MCP 总线聚合结果。
4. 聚合结果以 JSON 返回给前端，前端解析后将不同类型的响应渲染到界面上。

## 快速开始

1. 安装依赖：`pip install -r requirements.txt`
2. 启动后端：`uvicorn server.main:app --reload --port 8850`
3. 通过浏览器打开 `web/index.html`，配置 API 信息后即可开始对话体验。

通过以上流程，即可体验完整的异步多模型聚合 Agent。祝使用愉快！
