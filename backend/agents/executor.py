"""
Executor Agent - 任务执行 Agent
负责：Tool 选择、参数填充、执行调度、重试机制
"""
from typing import Dict, Any, Optional
from langchain.prompts import ChatPromptTemplate
from loguru import logger
from datetime import datetime
import asyncio

from backend.config.settings import settings
from backend.config.llm_config import get_llm
from backend.state.models import AgentState, TaskStep
from backend.tools.registry import tool_registry
from backend.rag.vectorstore import knowledge_base


class ExecutorAgent:
    """Executor Agent - 负责执行任务步骤"""

    def __init__(self):
        """初始化 Executor Agent"""
        # 使用全局LLM管理器
        self.llm = get_llm()

        self.param_filling_prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_param_filling_prompt()),
            ("user", "{task_description}\n\nTool: {tool_name}\nTool Schema: {tool_schema}\n\nContext: {context}")
        ])

        logger.info("Executor Agent initialized")

    def _get_param_filling_prompt(self) -> str:
        """参数填充 Prompt"""
        return """你是一个参数填充专家。你的任务是根据：
1. 任务描述
2. Tool Schema 定义
3. 上下文信息（包括之前步骤的执行结果、用户输入、知识库检索结果）

生成正确的 Tool 调用参数（JSON 格式）。

## 参数填充原则：
- 严格按照 Tool Schema 的参数类型和约束
- 优先使用上下文中的信息
- 如果信息不足，返回 null 并说明需要用户提供哪些信息
- 确保参数的业务语义正确

请返回 JSON 格式的参数字典，例如：
{
  "param1": "value1",
  "param2": 123
}

如果需要用户输入，返回：
{
  "requires_user_input": true,
  "missing_params": ["param1", "param2"],
  "reason": "需要用户提供..."
}
"""

    async def execute_step(self, state: AgentState) -> AgentState:
        """
        执行当前步骤

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        try:
            current_index = state["current_step_index"]
            todo_list = state["todo_list"]

            if current_index >= len(todo_list):
                logger.info("All steps completed")
                state["final_status"] = "success"
                return state

            current_step = todo_list[current_index]
            logger.info(f"Executing step {current_index + 1}/{len(todo_list)}: {current_step.title}")

            # 更新步骤状态为运行中
            current_step.status = "running"
            current_step.started_at = datetime.utcnow()
            state["current_agent"] = "executor"

            # 1. 如果步骤需要调用 Tool
            if current_step.tool_name:
                result = await self._execute_tool_step(current_step, state)

                if result.get("requires_user_input"):
                    # 需要用户输入，暂停执行
                    state["pending_user_input"] = {
                        "step_id": current_step.id,
                        "tool_name": current_step.tool_name,
                        "missing_params": result.get("missing_params"),
                        "reason": result.get("reason")
                    }
                    logger.info("Waiting for user input")
                    return state

                # 执行成功
                current_step.tool_output = result
                current_step.status = "completed"
                current_step.completed_at = datetime.utcnow()

            else:
                # 不需要 Tool 的步骤（例如信息收集）
                current_step.status = "completed"
                current_step.completed_at = datetime.utcnow()

            # 2. 保存步骤结果到上下文
            if "step_results" not in state:
                state["step_results"] = []

            state["step_results"].append({
                "step_id": current_step.id,
                "step_title": current_step.title,
                "result": current_step.tool_output
            })

            # 3. 移动到下一步
            state["current_step_index"] = current_index + 1
            state["updated_at"] = datetime.utcnow().isoformat()

            logger.success(f"Step {current_index + 1} completed")

            return state

        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            current_step = state["todo_list"][state["current_step_index"]]
            current_step.status = "failed"
            current_step.error = str(e)
            current_step.retry_count += 1

            # 重试逻辑
            if current_step.retry_count < settings.MAX_RETRY_COUNT:
                logger.warning(f"Retrying step (attempt {current_step.retry_count + 1}/{settings.MAX_RETRY_COUNT})")
                current_step.status = "pending"
                return state
            else:
                state["error_info"] = f"Step failed after {settings.MAX_RETRY_COUNT} retries: {str(e)}"
                state["final_status"] = "failed"
                return state

    async def _execute_tool_step(
        self,
        step: TaskStep,
        state: AgentState
    ) -> Dict[str, Any]:
        """
        执行 Tool 调用步骤

        Args:
            step: 当前步骤
            state: 状态

        Returns:
            Tool 执行结果
        """
        tool_name = step.tool_name
        tool = tool_registry.get_tool(tool_name)
        tool_schema = tool_registry.get_schema(tool_name)

        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        # 1. 参数填充
        if not step.tool_input:
            # 使用 LLM 填充参数
            context = {
                "user_input": state.get("user_input"),
                "previous_results": state.get("step_results", []),
                "retrieved_knowledge": state.get("retrieved_docs", [])
            }

            chain = self.param_filling_prompt | self.llm

            param_result = await chain.ainvoke({
                "task_description": step.description or step.title,
                "tool_name": tool_name,
                "tool_schema": tool_schema.parameters,
                "context": str(context)
            })

            # 解析 LLM 返回的参数
            import json
            try:
                tool_input = json.loads(param_result.content)
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM output as JSON, using empty params")
                tool_input = {}

            # 检查是否需要用户输入
            if tool_input.get("requires_user_input"):
                return tool_input

            step.tool_input = tool_input

        # 2. 执行 Tool（带超时）
        try:
            logger.debug(f"Calling tool {tool_name} with params: {step.tool_input}")

            result = await asyncio.wait_for(
                tool.ainvoke(step.tool_input),
                timeout=tool_schema.timeout
            )

            logger.debug(f"Tool {tool_name} returned: {result}")
            return {"success": True, "data": result}

        except asyncio.TimeoutError:
            raise Exception(f"Tool execution timeout after {tool_schema.timeout}s")
        except Exception as e:
            raise Exception(f"Tool execution failed: {str(e)}")


# 全局实例
executor_agent = ExecutorAgent()
