"""
Planner Agent - 任务规划 Agent
负责：意图理解、任务拆解、依赖推断
"""
from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from loguru import logger
import uuid
from datetime import datetime

from backend.config.settings import settings
from backend.config.llm_config import get_llm
from backend.state.models import AgentState, TaskStep, ParsedIntent
from backend.tools.registry import tool_registry
from backend.rag.vectorstore import knowledge_base


class PlannerOutput(BaseModel):
    """Planner 输出结构"""
    intent: ParsedIntent
    steps: List[Dict[str, Any]]


class PlannerAgent:
    """Planner Agent - 负责理解意图并规划任务"""

    def __init__(self):
        """初始化 Planner Agent"""
        # 使用全局LLM管理器
        self.llm = get_llm()

        # 输出解析器
        self.parser = PydanticOutputParser(pydantic_object=PlannerOutput)

        # Prompt 模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("user", "{user_input}\n\n{format_instructions}")
        ])

        logger.info("Planner Agent initialized")

    def _get_system_prompt(self) -> str:
        """获取系统 Prompt"""
        available_tools = tool_registry.list_tool_names()
        tool_descriptions = "\n".join([
            f"- {name}: {schema.description}"
            for name, schema in tool_registry.get_all_schemas().items()
        ])

        return f"""你是一个任务规划专家 Agent。你的职责是：

1. **理解用户意图**：解析用户的自然语言输入，提取核心目标
2. **任务拆解**：将复杂目标拆解为清晰的执行步骤（TODO List）
3. **依赖推断**：识别步骤间的依赖关系，确保按正确顺序执行
4. **工具选择**：从可用工具中选择合适的工具来完成各个步骤

## 可用工具列表：
{tool_descriptions if tool_descriptions else "（暂无已注册工具）"}

## 规划原则：
- 每个步骤应该是原子性的、可执行的
- 步骤描述要清晰、具体
- 如果需要用户输入配置，明确标注
- 考虑异常情况和重试机制
- 步骤总数不超过 {settings.MAX_TASK_STEPS} 个

## 输出格式要求：
你必须返回 JSON 格式，包含：
1. `intent`: 解析后的用户意图（目标、所需工具、所需信息、置信度）
2. `steps`: 任务步骤列表，每个步骤包含：
   - title: 步骤标题
   - description: 步骤描述
   - tool_name: 使用的工具名称（如果需要）
   - requires_user_input: 是否需要用户输入

请基于用户输入生成合理的任务规划。
"""

    async def plan(self, state: AgentState) -> AgentState:
        """
        规划任务

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        try:
            user_input = state["user_input"]
            logger.info(f"Planning for user input: {user_input[:100]}...")

            # 1. RAG 检索相关知识
            retrieved_docs = knowledge_base.search(user_input, k=3)
            context = "\n\n".join([doc.page_content for doc in retrieved_docs])

            # 2. 调用 LLM 进行规划
            chain = self.prompt | self.llm | self.parser

            result = await chain.ainvoke({
                "user_input": f"{user_input}\n\n相关背景知识：\n{context}" if context else user_input,
                "format_instructions": self.parser.get_format_instructions()
            })

            # 3. 构建 TaskStep 列表
            todo_list = []
            for idx, step_data in enumerate(result.steps):
                step = TaskStep(
                    id=f"step_{uuid.uuid4().hex[:8]}",
                    title=step_data.get("title", f"Step {idx + 1}"),
                    description=step_data.get("description"),
                    tool_name=step_data.get("tool_name"),
                    status="pending"
                )
                todo_list.append(step)

            # 4. 更新状态
            state["parsed_intent"] = result.intent
            state["todo_list"] = todo_list
            state["current_step_index"] = 0
            state["retrieved_docs"] = [doc.page_content for doc in retrieved_docs]
            state["current_agent"] = "planner"
            state["updated_at"] = datetime.utcnow().isoformat()

            logger.success(f"Planning completed: {len(todo_list)} steps generated")

            return state

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            state["error_info"] = f"Planning error: {str(e)}"
            state["final_status"] = "failed"
            return state


# 全局实例
planner_agent = PlannerAgent()
