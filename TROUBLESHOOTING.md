# 常见问题解决指南

## 问题 1: PostgreSQL 连接失败

**错误信息:**
```
Database initialization failed: (psycopg2.OperationalError)
```

### 解决方案：

#### 方案 A: 使用 SQLite（推荐用于开发测试）

如果你只是想快速测试，可以先跳过 PostgreSQL，使用 SQLite：

1. 修改 `backend/state/persistence.py`，注释掉 PostgreSQL 相关代码
2. 或者暂时跳过数据库持久化功能

#### 方案 B: 正确配置 PostgreSQL

**步骤 1: 检查 PostgreSQL 是否运行**

```bash
# Windows - 检查服务
sc query postgresql-x64-14

# 或者在任务管理器中查看 postgres.exe 进程
```

**步骤 2: 启动 PostgreSQL**

```bash
# Windows - 使用 pg_ctl
"C:\Program Files\PostgreSQL\14\bin\pg_ctl.exe" -D "C:\Program Files\PostgreSQL\14\data" start

# 或者启动服务
net start postgresql-x64-14
```

**步骤 3: 创建数据库**

```bash
# 使用 psql 连接
psql -U postgres

# 在 psql 中执行
CREATE DATABASE agent_workstation;
\q
```

**步骤 4: 验证连接**

```bash
# 测试连接
psql -U postgres -d agent_workstation -c "SELECT 1;"
```

**步骤 5: 检查 .env 配置**

确保你的 `.env` 文件中配置正确：

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agent_workstation
POSTGRES_USER=postgres
POSTGRES_PASSWORD=你的密码
```

---

## 问题 2: 如果不想使用 PostgreSQL

### 临时方案：使用 SQLite

修改 `backend/api/main.py`，注释掉数据库初始化：

```python
# 初始化数据库
try:
    # db_manager.create_tables()  # 临时注释
    logger.success("Database initialization skipped (using SQLite for checkpoints)")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
```

这样应用仍然可以运行，只是不会保存对话历史到 PostgreSQL。

---

## 问题 3: Redis 连接失败

**错误:** `redis.exceptions.ConnectionError`

**解决方案:**

```bash
# Windows - 启动 Redis
redis-server

# 或者修改 .env，暂时禁用 Redis
# 在代码中捕获 Redis 连接错误
```

---

## 问题 4: LLM 连接失败

**阿里百炼错误:** `Invalid API Key`

**解决方案:**
1. 检查 API Key 是否正确
2. 确认账户余额充足
3. 检查网络连接

**Ollama 错误:** `Connection refused`

**解决方案:**
```bash
# 启动 Ollama
ollama serve

# 在新终端下载模型
ollama pull qwen2.5:latest
```

---

## 快速启动（最小依赖）

如果你只想快速测试核心功能，可以：

1. **只使用 Ollama（不需要 PostgreSQL 和 Redis）**
2. **临时注释数据库相关代码**
3. **使用内存状态管理**

我可以帮你创建一个简化版的启动配置。
