"""
Tool Registry - 工具注册中心
支持动态注册、加载和调用 Tools
"""
from typing import Dict, Any, Callable, List, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool
from loguru import logger
import inspect


class ToolSchema(BaseModel):
    """Tool 定义 Schema"""
    name: str = Field(description="Tool 名称")
    description: str = Field(description="Tool 功能描述（用于 LLM 选择）")
    parameters: Dict[str, Any] = Field(description="参数 Schema (OpenAPI format)")
    returns: Dict[str, Any] = Field(description="返回值 Schema")
    requires_auth: bool = Field(default=False, description="是否需要授权")
    requires_user_config: bool = Field(default=False, description="是否需要用户配置")
    config_schema: Optional[Dict[str, Any]] = Field(default=None, description="配置表单 Schema")
    timeout: int = Field(default=60, description="超时时间（秒）")
    tags: List[str] = Field(default_factory=list, description="标签（用于分类）")


class ToolRegistry:
    """Tool 注册中心（单例模式）"""

    _instance = None
    _tools: Dict[str, BaseTool] = {}
    _schemas: Dict[str, ToolSchema] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register_tool(
        self,
        name: str,
        func: Callable,
        schema: ToolSchema
    ) -> None:
        """
        注册一个 Tool

        Args:
            name: Tool 名称
            func: Tool 执行函数
            schema: Tool Schema 定义
        """
        try:
            # 验证函数签名
            sig = inspect.signature(func)
            logger.info(f"Registering tool: {name} with signature: {sig}")

            # 创建 LangChain Tool
            tool = StructuredTool.from_function(
                func=func,
                name=name,
                description=schema.description,
                # args_schema 会从函数签名自动推断
            )

            self._tools[name] = tool
            self._schemas[name] = schema

            logger.success(f"Tool registered: {name}")

        except Exception as e:
            logger.error(f"Failed to register tool {name}: {e}")
            raise

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取 Tool"""
        return self._tools.get(name)

    def get_schema(self, name: str) -> Optional[ToolSchema]:
        """获取 Tool Schema"""
        return self._schemas.get(name)

    def get_all_tools(self) -> List[BaseTool]:
        """获取所有已注册的 Tools"""
        return list(self._tools.values())

    def get_all_schemas(self) -> Dict[str, ToolSchema]:
        """获取所有 Tool Schemas"""
        return self._schemas.copy()

    def list_tool_names(self) -> List[str]:
        """列出所有 Tool 名称"""
        return list(self._tools.keys())

    def search_tools_by_tag(self, tag: str) -> List[str]:
        """根据标签搜索 Tools"""
        return [
            name for name, schema in self._schemas.items()
            if tag in schema.tags
        ]

    def unregister_tool(self, name: str) -> bool:
        """注销一个 Tool"""
        if name in self._tools:
            del self._tools[name]
            del self._schemas[name]
            logger.info(f"Tool unregistered: {name}")
            return True
        return False


# 全局注册中心实例
tool_registry = ToolRegistry()


# ============ Decorator for easy registration ============

def register_tool(schema: ToolSchema):
    """
    装饰器：快速注册 Tool

    用法:
    @register_tool(ToolSchema(
        name="my_tool",
        description="My tool description",
        parameters={...},
        returns={...}
    ))
    def my_tool_func(param1: str, param2: int):
        # Tool logic
        return result
    """
    def decorator(func: Callable):
        tool_registry.register_tool(
            name=schema.name,
            func=func,
            schema=schema
        )
        return func
    return decorator
