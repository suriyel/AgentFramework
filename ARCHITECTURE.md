# Agent Workstation - 架构设计文档

## 📐 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Chat Area    │  │ TODO List    │  │ Config Form  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │ WebSocket + REST API
┌────────────────────────┴────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ REST API     │  │ WebSocket    │  │ Tool Registry│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                  LangGraph Workflow                          │
│  ┌──────────────┐                                           │
│  │  Supervisor  │ (协调路由)                                │
│  └──────┬───────┘                                           │
│         │                                                     │
│    ┌────┼────┬────────────┐                                 │
│    │    │    │            │                                 │
│    ▼    ▼    ▼            ▼                                 │
│  ┌───┐┌───┐┌───┐     ┌────────┐                            │
│  │PLA││EXE││VAL│     │  State │                            │
│  │NER││CUT││IDA│     │ (Graph)│                            │
│  │   ││OR ││TOR│     └────────┘                            │
│  └───┘└───┘└───┘                                           │
└────────────────────────┬───────────────────────────────────┘
                         │
┌────────────────────────┴───────────────────────────────────┐
│                Data & Knowledge Layer                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │PostgreSQL│  │  Redis   │  │  Chroma  │  │  Qwen    │  │
│  │(State DB)│  │ (Cache)  │  │  (RAG)   │  │  (LLM)   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└────────────────────────────────────────────────────────────┘
```

---

## 🧩 核心组件

### 1. Frontend Layer (React + TypeScript)

#### 1.1 AgentWorkstation
**职责:** 主工作台，管理对话、消息、WebSocket 连接

**关键功能:**
- WebSocket 连接管理
- 消息收发
- 任务状态展示

**核心代码:**
```typescript
const ws = new WebSocket(`ws://localhost:8000/ws/${conversationId}`)

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  handleStateUpdate(data)
}
```

#### 1.2 TodoTaskList
**职责:** 可视化展示任务步骤和状态

**关键功能:**
- 实时更新步骤状态
- 进度条展示
- 错误信息展示
- 可折叠/展开

**状态映射:**
```typescript
pending   → ⏸️ 灰色 Clock 图标
running   → 🔄 蓝色旋转 Loader
completed → ✅ 绿色 CheckCircle
failed    → ❌ 红色 AlertCircle
```

---

### 2. Backend Layer (FastAPI + Python)

#### 2.1 REST API (`routes.py`)

**端点列表:**

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/conversations` | POST | 创建对话 |
| `/api/v1/tasks` | POST | 创建任务 |
| `/api/v1/tasks/{id}` | GET | 查询任务状态 |
| `/api/v1/tasks/resume` | POST | 恢复暂停任务 |
| `/api/v1/tools` | GET | 列出所有工具 |
| `/api/v1/knowledge` | POST | 上传知识 |

#### 2.2 WebSocket Handler (`websocket.py`)

**消息协议:**

**客户端 → 服务端:**
```json
{
  "type": "start_task",
  "user_input": "帮我查询天气",
  "user_id": "user_123"
}
```

**服务端 → 客户端:**
```json
{
  "type": "state_update",
  "data": {
    "todo_list": [...],
    "current_step_index": 2,
    "final_status": "running"
  }
}
```

---

### 3. Agent Layer (LangGraph)

#### 3.1 Supervisor Agent (`supervisor.py`)

**职责:** 协调和路由

**路由逻辑:**
```python
def route(state):
    if not state.get("todo_list"):
        return "planner"
    elif current_step < total_steps:
        return "executor"
    elif all_steps_done:
        return "validator"
    else:
        return "end"
```

#### 3.2 Planner Agent (`planner.py`)

**职责:** 意图理解 + 任务拆解

**输入:**
```
用户自然语言: "帮我查询北京天气并发邮件"
```

**输出:**
```json
{
  "intent": {
    "goal": "查询天气并发送邮件",
    "required_tools": ["fetch_weather", "send_email"]
  },
  "steps": [
    {
      "title": "查询北京天气",
      "tool_name": "fetch_weather",
      "description": "获取北京市天气信息"
    },
    {
      "title": "发送邮件通知",
      "tool_name": "send_email",
      "requires_user_input": true
    }
  ]
}
```

**关键技术:**
- RAG 检索相关知识
- LLM 提示工程
- 结构化输出（Pydantic）

#### 3.3 Executor Agent (`executor.py`)

**职责:** 执行任务步骤

**执行流程:**
```
1. 参数填充（LLM 或上下文）
   ↓
2. 调用 Tool (await tool.ainvoke())
   ↓
3. 保存结果到 State
   ↓
4. 移动到下一步
```

**重试机制:**
```python
if failed and retry_count < MAX_RETRY:
    retry()
else:
    mark_as_failed()
```

**Human-in-the-Loop:**
```python
if tool_requires_user_config:
    state["pending_user_input"] = {
        "tool_name": "send_email",
        "missing_params": ["smtp_config"]
    }
    pause_execution()
```

#### 3.4 Validator Agent (`validator.py`)

**职责:** 结果校验和状态判定

**校验逻辑:**
```python
all_completed = all(step.status == "completed" for step in steps)
if all_completed:
    state["final_status"] = "success"
else:
    identify_failed_step()
    state["final_status"] = "failed"
```

---

### 4. Tool Registry (`tools/registry.py`)

**设计模式:** 单例模式

**注册方式:**
```python
@register_tool(ToolSchema(
    name="my_tool",
    description="...",
    parameters={...},
    returns={...}
))
def my_tool(param1: str):
    return {"result": ...}
```

**Tool Schema 结构:**
```python
{
    "name": str,
    "description": str,
    "parameters": dict,  # OpenAPI format
    "returns": dict,
    "requires_auth": bool,
    "requires_user_config": bool,
    "config_schema": dict,
    "timeout": int,
    "tags": list[str]
}
```

---

### 5. RAG Knowledge Base (`rag/vectorstore.py`)

**技术栈:**
- Chroma (向量数据库)
- HuggingFace Embeddings (all-MiniLM-L6-v2)

**工作流程:**
```
1. 文档上传 → 文本分块 (RecursiveCharacterTextSplitter)
   ↓
2. 生成嵌入 → 存储到 Chroma
   ↓
3. 查询时 → 相似度搜索
   ↓
4. 返回 Top-K 文档 → 注入到 Prompt
```

**使用场景:**
- Planner Agent: 检索领域知识辅助规划
- Executor Agent: 参数填充时的上下文补充

---

### 6. State Management

#### 6.1 LangGraph State (`state/models.py`)

**核心字段:**
```python
AgentState = {
    "user_input": str,
    "parsed_intent": ParsedIntent,
    "todo_list": List[TaskStep],
    "current_step_index": int,
    "step_results": List[dict],
    "context": dict,
    "pending_user_input": dict,
    "final_status": str,
    "error_info": str
}
```

**持久化:**
- LangGraph Checkpoint (SQLite)
- 支持任务暂停/恢复

#### 6.2 Database Persistence (`state/persistence.py`)

**数据库表:**
```sql
conversations (id, user_id, title, created_at)
tasks         (id, conversation_id, user_input, status, todo_list)
messages      (id, conversation_id, role, content)
knowledge_docs(id, title, content, vector_id)
```

**缓存策略 (Redis):**
```python
cache_manager.set_task_state(task_id, state, ttl=3600)
```

---

## 🔄 数据流

### 完整任务执行流程

```
1. 用户输入
   ↓
2. WebSocket 发送 {type: "start_task"}
   ↓
3. 创建 Task 记录（DB）
   ↓
4. LangGraph 启动工作流
   ↓
5. Planner: 意图解析 + 任务拆解
   ├─ RAG 检索知识
   ├─ LLM 生成 TODO 列表
   └─ 状态更新 → WebSocket 广播
   ↓
6. Executor: 逐步执行
   ├─ 参数填充
   ├─ Tool 调用
   ├─ 结果保存
   └─ 状态更新 → WebSocket 广播
   ↓
7. (可选) Human-in-the-Loop
   ├─ 暂停执行
   ├─ 前端弹窗收集配置
   ├─ 用户提交 → resume 请求
   └─ 继续执行
   ↓
8. Validator: 结果校验
   ├─ 判定成功/失败
   ├─ 生成状态说明
   └─ 状态更新 → WebSocket 广播
   ↓
9. 任务完成
   ├─ 更新 DB
   ├─ 清理缓存
   └─ 前端展示结果
```

---

## 🛡️ 错误处理

### 1. Agent 层错误

```python
try:
    result = await tool.ainvoke(params)
except ToolExecutionError as e:
    if retry_count < MAX_RETRY:
        retry()
    else:
        state["error_info"] = str(e)
        state["final_status"] = "failed"
```

### 2. WebSocket 断线重连

```typescript
ws.onclose = () => {
  setTimeout(() => reconnect(), 3000)
}
```

### 3. LLM 超时

```python
result = await asyncio.wait_for(
    llm.ainvoke(prompt),
    timeout=60
)
```

---

## 📊 性能优化

### 1. Token 管理

**压缩策略:**
```python
if token_count > MAX_CONTEXT_TOKENS * COMPRESSION_THRESHOLD:
    compress_tool_messages()
    compress_llm_responses()
```

### 2. 并发控制

```python
# FastAPI 异步处理
async def handle_task():
    await asyncio.gather(
        planner.plan(),
        rag.search()
    )
```

### 3. 缓存优化

- Redis 缓存热点任务
- Chroma 向量检索缓存
- LLM 响应缓存（相同 Prompt）

---

## 🔐 安全考虑

### 1. SQL 注入防护

使用 SQLAlchemy ORM，避免拼接 SQL。

### 2. XSS 防护

前端使用 React 自动转义。

### 3. CSRF 防护

WebSocket 使用 Token 认证。

### 4. Tool 权限控制

```python
if tool.requires_auth and not user.has_permission():
    raise PermissionError()
```

---

## 🎯 扩展性设计

### 1. 添加新 Agent

```python
# 1. 创建 Agent 类
class MyCustomAgent:
    async def process(self, state):
        ...

# 2. 注册到 Workflow
workflow.add_node("my_agent", my_agent.process)

# 3. 添加路由规则
workflow.add_edge("planner", "my_agent")
```

### 2. 添加新 Tool

```python
@register_tool(ToolSchema(...))
def new_tool(param1: str):
    return {"result": ...}
```

### 3. 集成新 LLM

```python
# config/settings.py
LLM_BASE_URL="https://api.openai.com/v1"
LLM_MODEL_NAME="gpt-4"
```

---

## 📚 技术选型理由

| 技术 | 选型理由 |
|------|----------|
| **LangGraph** | 状态化工作流、Checkpoint 持久化、易于调试 |
| **FastAPI** | 高性能、异步支持、WebSocket 原生支持、自动 API 文档 |
| **Chroma** | 轻量级向量数据库、易部署、Python 原生支持 |
| **PostgreSQL** | 成熟稳定、JSON 支持、ACID 保证 |
| **Redis** | 高性能缓存、会话管理 |
| **Qwen** | 支持本地部署、中文理解能力强、开源免费 |
| **React** | 组件化、生态丰富、性能优秀 |

---

## 🔮 未来优化方向

1. **多租户支持**: 用户隔离、资源配额
2. **分布式部署**: Celery 任务队列、消息队列解耦
3. **高级 RAG**: GraphRAG、多模态检索
4. **自适应规划**: Agent 自主调整计划
5. **可视化编排**: 低代码 Workflow 设计器
6. **A/B 测试**: Prompt 版本管理和效果对比
