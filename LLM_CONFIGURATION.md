# LLM 配置指南

Agent Workstation 支持多个主流 LLM 平台，本文档将介绍如何配置和使用不同的 LLM 服务。

---

## 📋 支持的 LLM 平台

| 平台 | 提供商 | 说明 |
|------|--------|------|
| **阿里百炼** | DashScope | 阿里云大模型服务，支持通义千问系列 |
| **OpenAI** | OpenAI | GPT 系列模型 |
| **Azure OpenAI** | Microsoft | 微软 Azure 平台的 OpenAI 服务 |
| **智谱AI** | GLM | ChatGLM 系列模型 |
| **火山引擎** | ByteDance | 豆包大模型 |
| **Ollama** | Local | 本地部署的开源模型 |

---

## 🚀 快速配置

### 方法 1: 通过 Web 界面配置（推荐）

1. 启动应用后，点击右上角的 **"LLM 设置"** 按钮
2. 选择你要使用的 LLM 提供商
3. 填写必要的配置信息（API Key、模型名称等）
4. 调整参数（Temperature、Max Tokens）
5. 点击 **"保存配置"**
6. 点击 **"测试连接"** 验证配置是否正确

### 方法 2: 通过环境变量配置

编辑 `.env` 文件：

```bash
# 选择提供商
LLM_PROVIDER=dashscope  # 或 openai, zhipuai, ollama 等

# 根据提供商填写对应配置（见下文）
```

---

## 🔧 各平台配置详解

### 1. 阿里百炼 (DashScope)

**获取 API Key:**
1. 访问 [阿里云百炼平台](https://dashscope.aliyun.com/)
2. 注册/登录账号
3. 进入控制台，获取 API Key

**配置方式:**

**环境变量:**
```bash
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxx
DASHSCOPE_MODEL=qwen-max  # 可选: qwen-max, qwen-plus, qwen-turbo
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
```

**Web 界面:**
- 选择 "阿里百炼 (DashScope)"
- 填写 API Key
- 选择模型（推荐 qwen-max）
- 调整参数

**可用模型:**
- `qwen-max` - 最强性能，适合复杂任务
- `qwen-plus` - 平衡性能与成本
- `qwen-turbo` - 快速响应，成本较低

---

### 2. OpenAI

**获取 API Key:**
1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册/登录账号
3. 进入 API Keys 页面，创建新的 API Key

**配置方式:**

**环境变量:**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
OPENAI_MODEL=gpt-4  # 可选: gpt-4, gpt-3.5-turbo
OPENAI_BASE_URL=  # 可选，用于代理
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
```

**使用代理（国内用户）:**
```bash
# 使用第三方代理服务
OPENAI_BASE_URL=https://your-proxy-url.com/v1
```

**可用模型:**
- `gpt-4` - 最强推理能力
- `gpt-4-turbo` - 更快更便宜
- `gpt-3.5-turbo` - 性价比高

---

### 3. Azure OpenAI

**获取配置信息:**
1. 访问 [Azure Portal](https://portal.azure.com/)
2. 创建 Azure OpenAI 资源
3. 获取 Endpoint 和 API Key
4. 创建模型部署

**配置方式:**

**环境变量:**
```bash
LLM_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=xxxxxxxxxxxxx
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=your-deployment-name  # 你创建的部署名称
AZURE_OPENAI_MODEL=gpt-4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
```

**注意:**
- `AZURE_OPENAI_DEPLOYMENT` 是你在 Azure 中创建的部署名称，不是模型名称
- Endpoint 需要包含完整的 URL

---

### 4. 智谱AI (GLM)

**获取 API Key:**
1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册/登录账号
3. 获取 API Key

**配置方式:**

**环境变量:**
```bash
LLM_PROVIDER=zhipuai
ZHIPUAI_API_KEY=xxxxxxxxxxxxx
ZHIPUAI_MODEL=glm-4  # 可选: glm-4, glm-3-turbo
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
```

**可用模型:**
- `glm-4` - 最新版本
- `glm-3-turbo` - 快速版本

---

### 5. 火山引擎（豆包）

**获取配置信息:**
1. 访问 [火山引擎](https://www.volcengine.com/)
2. 开通大模型服务
3. 获取 API Key 和 Endpoint ID

**配置方式:**

**环境变量:**
```bash
LLM_PROVIDER=volcengine
VOLCENGINE_API_KEY=xxxxxxxxxxxxx
VOLCENGINE_ENDPOINT_ID=your-endpoint-id
VOLCENGINE_MODEL=doubao-pro  # 可选: doubao-pro, doubao-lite
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
```

---

### 6. Ollama (本地部署)

**安装 Ollama:**
1. 访问 [Ollama官网](https://ollama.com/)
2. 下载并安装 Ollama
3. 下载模型：`ollama pull qwen2.5:latest`

**启动 Ollama:**
```bash
ollama serve
```

**配置方式:**

**环境变量:**
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:latest  # 或其他已下载的模型
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
```

**可用模型（需先下载）:**
```bash
# 下载模型
ollama pull qwen2.5:latest
ollama pull llama3
ollama pull mistral

# 查看已下载的模型
ollama list
```

**推荐模型:**
- `qwen2.5:latest` - 通义千问，中文表现优秀
- `llama3` - Meta 开源模型
- `mistral` - 高效开源模型

---

## 📊 参数说明

### Temperature（温度）

控制输出的随机性：

- **0.0 - 0.3**: 确定性输出，适合需要精确答案的场景（数学、代码等）
- **0.4 - 0.7**: 平衡创造性和准确性（推荐）
- **0.8 - 2.0**: 高创造性，输出多样化（文学创作等）

### Max Tokens

控制最大输出长度：

- **512 - 1024**: 简短回答
- **2048**: 标准长度（推荐）
- **4096+**: 长文本生成

---

## 🔄 切换 LLM

### 在运行时切换

1. 点击 **"LLM 设置"**
2. 选择新的提供商
3. 填写配置
4. 保存并测试

配置会立即生效，所有新任务都会使用新的 LLM。

### 注意事项

- 切换 LLM 不会影响正在执行的任务
- 新配置会应用到所有 Agent（Planner、Executor、Validator）
- 建议在切换后点击 "测试连接" 验证配置

---

## 🧪 测试 LLM 配置

### 方法 1: Web 界面测试

在 LLM 设置页面点击 **"测试连接"** 按钮。

### 方法 2: API 测试

```bash
curl -X POST http://localhost:8000/api/v1/llm/test
```

### 方法 3: 实际任务测试

在聊天界面输入简单任务：
```
帮我计算 1+1
```

观察 LLM 是否正常响应。

---

## 💡 最佳实践

### 1. 模型选择

| 场景 | 推荐模型 |
|------|----------|
| **中文任务** | 阿里百炼 qwen-max、智谱AI glm-4 |
| **英文任务** | OpenAI gpt-4 |
| **预算有限** | 阿里百炼 qwen-turbo、Ollama 本地 |
| **隐私要求高** | Ollama 本地部署 |
| **快速响应** | qwen-turbo、gpt-3.5-turbo |

### 2. 参数调优

```bash
# 代码生成、数学计算
LLM_TEMPERATURE=0.2

# 通用任务
LLM_TEMPERATURE=0.7

# 创意写作
LLM_TEMPERATURE=1.2
```

### 3. 成本控制

- 开发测试：使用 Ollama 本地模型
- 生产环境：根据预算选择云服务
- 监控 Token 使用量

---

## ❓ 常见问题

### 1. API Key 无效

**症状:** 测试连接失败，提示 "Invalid API Key"

**解决方案:**
- 检查 API Key 是否正确复制
- 确认 API Key 是否已激活
- 检查账户余额是否充足

### 2. 连接超时

**症状:** 请求超时，无响应

**解决方案:**
- 检查网络连接
- 对于国际服务（OpenAI），尝试使用代理
- 增加超时时间（在代码中调整）

### 3. Ollama 无法连接

**症状:** "Connection refused" 错误

**解决方案:**
```bash
# 确认 Ollama 正在运行
ollama serve

# 测试连接
curl http://localhost:11434/api/tags

# 检查端口
netstat -an | grep 11434
```

### 4. 模型响应质量差

**解决方案:**
- 尝试更强大的模型（如 qwen-max、gpt-4）
- 调整 Temperature 参数
- 优化 Prompt（在 Agent 代码中）

---

## 🔐 安全建议

1. **不要将 API Key 提交到代码仓库**
   - 使用 `.env` 文件（已在 `.gitignore` 中）
   - 使用环境变量或密钥管理服务

2. **API Key 轮换**
   - 定期更换 API Key
   - 使用具有最小权限的 Key

3. **监控使用量**
   - 设置费用告警
   - 定期检查 Token 使用量

4. **生产环境**
   - 使用独立的 API Key
   - 限制 IP 白名单（如果支持）

---

## 📚 相关文档

- [阿里百炼文档](https://help.aliyun.com/zh/dashscope/)
- [OpenAI API文档](https://platform.openai.com/docs)
- [智谱AI文档](https://open.bigmodel.cn/dev/api)
- [Ollama文档](https://ollama.com/docs)

---

## 🆘 获取帮助

如果遇到配置问题：

1. 查看应用日志（后端控制台）
2. 使用浏览器开发者工具检查网络请求
3. 参考本文档的常见问题部分
4. 提交 GitHub Issue

---

**祝你使用愉快！** 🎉
