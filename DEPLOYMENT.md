# Agent Workstation - 部署指南

## 📋 前置要求

### 必需软件

1. **Python 3.10+**
2. **Node.js 18+**
3. **PostgreSQL 14+**
4. **Redis 6+**
5. **Ollama**（用于运行 Qwen 模型）

---

## 🚀 完整部署流程

### 步骤 1: 克隆项目

```bash
git clone <your-repo-url>
cd AgentFramework
```

### 步骤 2: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
# 配置数据库连接、Redis、LLM 等参数
```

**重要配置项：**

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agent_workstation
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM (Qwen via Ollama)
LLM_BASE_URL=http://localhost:11434
LLM_MODEL_NAME=qwen2.5:latest
```

### 步骤 3: 安装后端依赖

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 步骤 4: 安装前端依赖

```bash
cd ../frontend
npm install
```

### 步骤 5: 启动 PostgreSQL

**Windows:**
```bash
# 使用 PostgreSQL 安装目录的 pg_ctl
pg_ctl -D "C:\Program Files\PostgreSQL\14\data" start

# 创建数据库
createdb -U postgres agent_workstation
```

**Linux/Mac:**
```bash
# 启动 PostgreSQL
sudo systemctl start postgresql

# 创建数据库
createdb agent_workstation
```

### 步骤 6: 启动 Redis

**Windows:**
```bash
# 使用 Redis Windows 版本
redis-server
```

**Linux/Mac:**
```bash
sudo systemctl start redis
# 或
redis-server
```

### 步骤 7: 启动 Ollama 和下载 Qwen 模型

```bash
# 启动 Ollama 服务
ollama serve

# 新开一个终端，下载 Qwen 模型
ollama pull qwen2.5:latest

# 测试模型
ollama run qwen2.5:latest "你好"
```

### 步骤 8: 初始化数据库

数据库表会在首次启动后端时自动创建。

### 步骤 9: 启动后端服务

```bash
cd backend

# 方式 1: 直接运行
python -m backend.api.main

# 方式 2: 使用 uvicorn
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 `http://localhost:8000` 启动。

访问 API 文档: `http://localhost:8000/docs`

### 步骤 10: 启动前端服务

```bash
cd frontend
npm run dev
```

前端服务将在 `http://localhost:5173` 启动。

---

## 📝 验证部署

### 1. 检查后端健康状态

```bash
curl http://localhost:8000/health
```

应返回:
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected"
}
```

### 2. 检查前端

访问 `http://localhost:5173`，应该看到 Agent Workstation 界面。

### 3. 测试 WebSocket 连接

在浏览器控制台查看是否有 "WebSocket connected" 日志。

### 4. 测试完整流程

1. 在前端输入框输入：`帮我计算 123 + 456`
2. 观察右侧 TODO 列表是否显示任务步骤
3. 查看步骤状态是否实时更新

---

## 🔧 常见问题

### 问题 1: PostgreSQL 连接失败

**症状:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解决方案:**
1. 检查 PostgreSQL 是否启动
2. 验证 `.env` 中的数据库配置
3. 确认数据库已创建：`createdb agent_workstation`

### 问题 2: Ollama 无法连接

**症状:**
```
Failed to connect to LLM: Connection refused
```

**解决方案:**
1. 启动 Ollama: `ollama serve`
2. 检查模型是否已下载: `ollama list`
3. 测试模型: `ollama run qwen2.5:latest "test"`

### 问题 3: Redis 连接失败

**症状:**
```
redis.exceptions.ConnectionError
```

**解决方案:**
1. 启动 Redis: `redis-server`
2. 测试连接: `redis-cli ping` (应返回 PONG)

### 问题 4: 前端无法连接后端

**症状:**
前端显示 "Disconnected"

**解决方案:**
1. 检查后端是否启动: `curl http://localhost:8000/health`
2. 检查 CORS 配置（已默认允许所有来源）
3. 查看浏览器控制台错误

### 问题 5: WebSocket 连接失败

**症状:**
```
WebSocket connection failed
```

**解决方案:**
1. 确认后端正常运行
2. 检查防火墙设置
3. 使用浏览器开发工具的 Network 标签查看 WebSocket 连接

---

## 🐳 Docker 部署（可选）

### 创建 Dockerfile（后端）

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: agent_workstation
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      POSTGRES_HOST: postgres
      REDIS_HOST: redis

  frontend:
    image: node:18
    working_dir: /app
    volumes:
      - ./frontend:/app
    command: sh -c "npm install && npm run dev"
    ports:
      - "5173:5173"

volumes:
  postgres_data:
```

启动:
```bash
docker-compose up -d
```

---

## 📊 性能优化建议

### 1. 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_tasks_conversation_id ON tasks(conversation_id);
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
```

### 2. Redis 缓存

- 缓存热点任务状态
- 缓存用户会话
- TTL 设置合理（默认 1 小时）

### 3. LLM 优化

- 使用量化模型（如 qwen2.5:7b-instruct-q4_K_M）
- 调整 Token 限制
- 启用流式输出

### 4. 并发处理

```bash
# 使用 Gunicorn + Uvicorn workers
gunicorn backend.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

---

## 🔐 生产环境安全

### 1. 环境变量

```env
DEBUG=False
```

### 2. CORS 配置

编辑 `backend/api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 限制域名
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 3. HTTPS

使用 Nginx 反向代理 + Let's Encrypt SSL:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location /api/ {
        proxy_pass http://localhost:8000/api/;
    }

    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        proxy_pass http://localhost:5173/;
    }
}
```

---

## 📈 监控与日志

### 1. 日志配置

后端日志自动输出到 stdout，生产环境可重定向到文件:

```bash
uvicorn backend.api.main:app --log-config logging.conf
```

### 2. 监控指标

- 任务成功率
- 平均响应时间
- WebSocket 连接数
- LLM Token 使用量

---

## 🎯 下一步

1. 添加用户认证（OAuth 2.0）
2. 实现 Tool 权限管理
3. 添加任务历史回放功能
4. 集成更多 LLM 模型
5. 优化前端 UI/UX

---

## 💬 获取帮助

- 查看 README.md
- 检查 GitHub Issues
- 联系项目维护者
