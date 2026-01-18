"""
Example Tools - 示例工具
展示如何注册和使用 Tools
"""
from backend.tools.registry import register_tool, ToolSchema
from loguru import logger
import asyncio


# ============ 示例 Tool 1: 简单计算 ============

@register_tool(ToolSchema(
    name="calculator",
    description="执行基本的数学计算（加减乘除）",
    parameters={
        "type": "object",
        "required": ["expression"],
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式，例如：'2 + 3 * 4'"
            }
        }
    },
    returns={
        "type": "object",
        "properties": {
            "result": {"type": "number"},
            "expression": {"type": "string"}
        }
    },
    tags=["math", "utility"]
))
def calculator(expression: str) -> dict:
    """计算器工具"""
    try:
        # 安全计算（仅支持基本运算）
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            raise ValueError("Invalid expression")

        result = eval(expression)
        logger.info(f"Calculator: {expression} = {result}")

        return {
            "result": result,
            "expression": expression
        }
    except Exception as e:
        raise ValueError(f"Calculation error: {str(e)}")


# ============ 示例 Tool 2: 模拟网络请求 ============

@register_tool(ToolSchema(
    name="fetch_weather",
    description="获取指定城市的天气信息（模拟）",
    parameters={
        "type": "object",
        "required": ["city"],
        "properties": {
            "city": {
                "type": "string",
                "description": "城市名称"
            }
        }
    },
    returns={
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "temperature": {"type": "number"},
            "condition": {"type": "string"}
        }
    },
    timeout=10,
    tags=["weather", "api"]
))
async def fetch_weather(city: str) -> dict:
    """天气查询工具（模拟异步操作）"""
    # 模拟网络延迟
    await asyncio.sleep(1)

    # 模拟返回天气数据
    mock_data = {
        "北京": {"temperature": 25, "condition": "晴天"},
        "上海": {"temperature": 28, "condition": "多云"},
        "深圳": {"temperature": 32, "condition": "阴天"}
    }

    weather = mock_data.get(city, {"temperature": 20, "condition": "未知"})

    logger.info(f"Weather for {city}: {weather}")

    return {
        "city": city,
        **weather
    }


# ============ 示例 Tool 3: 需要用户配置 ============

@register_tool(ToolSchema(
    name="send_email",
    description="发送电子邮件（需要配置 SMTP 服务器）",
    parameters={
        "type": "object",
        "required": ["to", "subject", "body"],
        "properties": {
            "to": {
                "type": "string",
                "description": "收件人邮箱"
            },
            "subject": {
                "type": "string",
                "description": "邮件主题"
            },
            "body": {
                "type": "string",
                "description": "邮件正文"
            }
        }
    },
    returns={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"}
        }
    },
    requires_user_config=True,
    config_schema={
        "type": "object",
        "required": ["smtp_server", "smtp_port", "username", "password"],
        "properties": {
            "smtp_server": {
                "type": "string",
                "description": "SMTP 服务器地址"
            },
            "smtp_port": {
                "type": "integer",
                "description": "SMTP 端口"
            },
            "username": {
                "type": "string",
                "description": "用户名"
            },
            "password": {
                "type": "string",
                "description": "密码",
                "format": "password"
            }
        }
    },
    tags=["email", "communication"]
))
def send_email(to: str, subject: str, body: str, **config) -> dict:
    """发送邮件工具（模拟）"""
    logger.info(f"Sending email to {to}: {subject}")

    # 这里应该使用实际的 SMTP 配置发送邮件
    # smtp_server = config.get("smtp_server")
    # ...

    # 模拟发送成功
    return {
        "success": True,
        "message": f"Email sent to {to}"
    }


# ============ 示例 Tool 4: 数据库查询（需要授权）============

@register_tool(ToolSchema(
    name="query_database",
    description="执行数据库查询（需要授权）",
    parameters={
        "type": "object",
        "required": ["query"],
        "properties": {
            "query": {
                "type": "string",
                "description": "SQL 查询语句"
            }
        }
    },
    returns={
        "type": "object",
        "properties": {
            "rows": {"type": "array"},
            "count": {"type": "integer"}
        }
    },
    requires_auth=True,
    timeout=30,
    tags=["database", "query"]
))
def query_database(query: str) -> dict:
    """数据库查询工具（模拟）"""
    logger.info(f"Executing query: {query}")

    # 模拟查询结果
    mock_results = [
        {"id": 1, "name": "张三", "age": 25},
        {"id": 2, "name": "李四", "age": 30}
    ]

    return {
        "rows": mock_results,
        "count": len(mock_results)
    }


# 初始化时加载所有示例 Tools
logger.info("Example tools loaded")
