# Agent Workstation - 通用 Agent 工作台

> 基于 LangGraph 的企业级智能任务编排平台

## 📋 项目简介

**Agent Workstation** 是一个面向企业用户的智能任务编排平台，通过自然语言交互，将用户意图转化为可执行的多步骤任务，并提供完整的任务可视化与状态追踪能力。

### 核心特性

- ✅ **Multi-Agent 协作架构**：基于 LangGraph 实现 Supervisor + Planner + Executor + Validator 协同工作
- ✅ **多平台 LLM 支持**：支持阿里百炼、OpenAI、Azure、智谱AI、火山引擎、Ollama 等
- ✅ **RAG 知识检索**：集成 Chroma 向量数据库，支持领域知识辅助决策
- ✅ **动态 TODO 可视化**：实时展示任务步骤状态（待执行/执行中/已完成/失败）
- ✅ **Human-in-the-Loop**：支持任务暂停、用户配置输入、恢复执行
- ✅ **Tool 动态注册**：标准化 Tool 接入规范，快速扩展业务能力
- ✅ **实时通信**：基于 WebSocket 的状态实时推送
- ✅ **Neo-Swiss 设计**：简洁、专业的现代化界面

---

## 🏗️ 技术架构

### 后端技术栈

| 技术 | 说明 |
|------|------|
| **LangChain** | Agent 框架基础 |
| **LangGraph** | Multi-Agent 工作流编排 |
| **FastAPI** | 高性能 API 服务 |
| **Chroma** | 向量数据库（RAG） |
| **PostgreSQL** | 状态持久化 |
| **Redis** | 缓存与会话管理 |
| **Qwen** | 本地部署的 LLM |

### 前端技术栈

| 技术 | 说明 |
|------|------|
| **React** | UI 框架 |
| **TypeScript** | 类型安全 |
| **TailwindCSS** | 样式框架 |
| **Shadcn/ui** | 组件库 |

---

## 📁 项目结构

```
AgentFramework/
├── backend/
│   ├── agents/              # Agent 定义
│   │   ├── supervisor.py    # 协调 Agent
│   │   ├── planner.py       # 规划 Agent
│   │   ├── executor.py      # 执行 Agent
│   │   └── validator.py     # 校验 Agent
│   ├── graph/
│   │   └── workflow.py      # LangGraph 工作流
│   ├── tools/
│   │   ├── registry.py      # Tool 注册中心
│   │   └── examples.py      # 示例 Tools
│   ├── rag/
│   │   └── vectorstore.py   # Chroma 集成
│   ├── state/
│   │   ├── models.py        # 状态模型
│   │   └── persistence.py   # 数据库持久化
│   ├── api/
│   │   ├── main.py          # FastAPI 主应用
│   │   ├── routes.py        # REST API
│   │   └── websocket.py     # WebSocket 处理
│   └── config/
│       └── settings.py      # 配置管理
├── frontend/                # React 前端应用
├── data/                    # 数据目录（Chroma、Checkpoints）
├── .env                     # 环境变量
├── requirements.txt         # Python 依赖
└── README.md
```

---

## 🚀 快速开始

### 1. 环境准备

**必需组件：**

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Ollama（运行 Qwen 模型）

### 2. 安装依赖

#### 后端

```bash
cd backend
pip install -r requirements.txt
```

#### 前端

```bash
cd frontend
npm install
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库、Redis、LLM 等
```

### 4. 配置 LLM

**默认使用 Ollama (推荐用于开发):**

```bash
ollama pull qwen2.5:latest
ollama serve
```

**或使用其他 LLM 平台:**

编辑 `.env` 文件，选择你的 LLM 提供商：

```bash
# 使用阿里百炼
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=your_api_key
DASHSCOPE_MODEL=qwen-max

# 使用 OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4

# ... 更多配置见 LLM_CONFIGURATION.md
```

**或在 Web 界面中配置:**
启动应用后，点击右上角 "LLM 设置" 按钮进行配置。

**详细配置指南:** 参见 [LLM_CONFIGURATION.md](LLM_CONFIGURATION.md)

### 5. 初始化数据库

```bash
# PostgreSQL 创建数据库
createdb agent_workstation

# 自动创建表（启动时会自动执行）
```

### 6. 启动后端服务

```bash
cd backend
python -m backend.api.main

# 或使用 uvicorn
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. 启动前端应用

```bash
cd frontend
npm run dev
```

### 8. 访问应用

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

---

## 📖 使用指南

### 创建对话并启动任务

1. **连接 WebSocket**
   ```javascript
   const ws = new WebSocket('ws://localhost:8000/ws/{conversation_id}');
   ```

2. **发送任务请求**
   ```javascript
   ws.send(JSON.stringify({
     type: 'start_task',
     user_input: '帮我查询北京的天气并发送邮件给 test@example.com',
     user_id: 'user_123'
   }));
   ```

3. **接收状态更新**
   ```javascript
   ws.onmessage = (event) => {
     const data = JSON.parse(event.data);
     if (data.type === 'state_update') {
       // 更新 UI：TODO 列表、进度条等
       console.log(data.data.todo_list);
     }
   };
   ```

### 注册自定义 Tool

```python
from backend.tools.registry import register_tool, ToolSchema

@register_tool(ToolSchema(
    name="my_custom_tool",
    description="我的自定义工具",
    parameters={
        "type": "object",
        "required": ["param1"],
        "properties": {
            "param1": {"type": "string", "description": "参数1"}
        }
    },
    returns={
        "type": "object",
        "properties": {
            "result": {"type": "string"}
        }
    },
    tags=["custom"]
))
def my_custom_tool(param1: str) -> dict:
    # 工具逻辑
    return {"result": f"Processed: {param1}"}
```

### 上传知识库文档

```bash
curl -X POST http://localhost:8000/api/v1/knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "title": "产品手册",
    "content": "这是产品的详细说明...",
    "metadata": {"category": "documentation"}
  }'
```

---

## 🎯 核心功能说明

### 1. Multi-Agent 工作流

```
用户输入 → Planner（任务拆解）→ Executor（逐步执行）→ Validator（结果校验）→ 返回结果
                ↑                                                        ↓
                └────────────── Supervisor（协调路由）────────────────────┘
```

### 2. TODO 列表状态

- **pending** ⏸️ 待执行
- **running** 🔄 执行中
- **completed** ✅ 已完成
- **failed** ❌ 失败

### 3. Human-in-the-Loop

当任务需要用户输入配置时：

1. Agent 暂停执行
2. 前端弹出配置表单
3. 用户填写配置
4. 通过 WebSocket 恢复任务

---

## 🧪 测试示例

### 示例 1：简单计算任务

**用户输入：**
```
帮我计算 (123 + 456) * 2 的结果
```

**生成的 TODO 列表：**
1. ✅ 理解用户意图
2. ✅ 调用计算器工具
3. ✅ 返回计算结果

### 示例 2：复杂业务流程

**用户输入：**
```
查询北京的天气，如果温度高于30度，就发邮件通知我
```

**生成的 TODO 列表：**
1. ✅ 查询北京天气
2. ✅ 判断温度条件
3. ⏸️ 获取邮件配置（需要用户输入）
4. ⏸️ 发送邮件通知

---

## 🔧 配置说明

### LLM 配置

支持任何兼容 OpenAI API 的模型：

```python
# .env
LLM_BASE_URL=http://localhost:11434  # Ollama
LLM_MODEL_NAME=qwen2.5:latest

# 或使用 OpenAI
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4
```

### Agent 限制配置

```python
MAX_TASK_STEPS=20        # 单任务最大步骤数
MAX_NESTING_DEPTH=3      # 嵌套深度
MAX_RETRY_COUNT=3        # 重试次数
TOOL_TIMEOUT=60          # Tool 超时（秒）
```

---

## 📊 性能优化

### Token 压缩策略

- Tool 消息：规则裁剪（保留关键结果）
- LLM 回复：智能摘要压缩
- 用户消息：保留原文

### 缓存策略

- Redis 缓存任务状态（TTL: 1小时）
- LangGraph Checkpoint 持久化（SQLite）
- 向量检索结果缓存

---

## 🛠️ 开发指南

### 添加新 Agent

1. 在 `backend/agents/` 创建新文件
2. 继承基础 Agent 类
3. 在 `workflow.py` 中注册

### 扩展前端组件

参考 `neo-swiss-agent-workstation` demo：

- `TodoTaskList.tsx`：TODO 列表组件
- `ConfigFormDialog.tsx`：配置表单
- `TaskProgressPanel.tsx`：任务进度面板

---

## 📝 API 文档

完整 API 文档请访问：http://localhost:8000/docs

### 主要端点

- `POST /api/v1/conversations`：创建对话
- `POST /api/v1/tasks`：创建任务
- `GET /api/v1/tasks/{task_id}`：查询任务状态
- `POST /api/v1/tasks/resume`：恢复暂停的任务
- `GET /api/v1/tools`：列出所有 Tools
- `POST /api/v1/knowledge`：上传知识库文档
- `WS /ws/{conversation_id}`：WebSocket 连接

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

---

## 📄 License

MIT License

---

## 👥 作者

由 Claude Sonnet 4.5 与人类协作开发
