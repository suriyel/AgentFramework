"""
Validator Agent - 结果校验 Agent
负责：结果判定、错误归因、状态说明
"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from datetime import datetime

from backend.config.settings import settings
from backend.config.llm_config import get_llm
from backend.state.models import AgentState


class ValidatorAgent:
    """Validator Agent - 负责校验执行结果"""

    def __init__(self):
        """初始化 Validator Agent"""
        # 使用全局LLM管理器
        self.llm = get_llm()

        self.validation_prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_validation_prompt()),
            ("user", "原始目标: {user_input}\n\n执行步骤: {steps}\n\n执行结果: {results}")
        ])

        logger.info("Validator Agent initialized")

    def _get_validation_prompt(self) -> str:
        """校验 Prompt"""
        return """你是一个结果校验专家。你的任务是：

1. **判定任务是否成功**：对比原始目标和执行结果，判断任务是否完成
2. **错误归因**：如果失败，定位到具体的失败步骤和原因
3. **生成用户友好的状态说明**：使用业务语言描述执行状态

## 校验原则：
- 严格对比目标和实际结果
- 失败时明确指出哪个步骤、什么原因
- 使用非技术语言描述状态
- 提供改进建议（如果适用）

请返回 JSON 格式：
{
  "is_successful": true/false,
  "failed_step_id": "step_xxx" (如果失败),
  "failure_reason": "失败原因" (如果失败),
  "status_message": "用户友好的状态描述",
  "suggestions": ["改进建议1", "改进建议2"]
}
"""

    async def validate(self, state: AgentState) -> AgentState:
        """
        校验任务执行结果

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        try:
            logger.info("Validating task results")

            todo_list = state.get("todo_list", [])
            step_results = state.get("step_results", [])

            # 1. 检查是否所有步骤都完成
            all_completed = all(
                step.status == "completed"
                for step in todo_list
            )

            if not all_completed:
                # 查找失败的步骤
                failed_steps = [
                    step for step in todo_list
                    if step.status == "failed"
                ]

                if failed_steps:
                    first_failed = failed_steps[0]
                    state["final_status"] = "failed"
                    state["error_info"] = f"步骤失败: {first_failed.title} - {first_failed.error}"
                    logger.error(f"Validation failed: {state['error_info']}")
                    return state

            # 2. 使用 LLM 进行深度校验
            chain = self.validation_prompt | self.llm

            validation_result = await chain.ainvoke({
                "user_input": state.get("user_input"),
                "steps": [
                    {"title": step.title, "status": step.status}
                    for step in todo_list
                ],
                "results": step_results
            })

            # 3. 解析校验结果
            import json
            try:
                result_data = json.loads(validation_result.content)
            except json.JSONDecodeError:
                logger.warning("Failed to parse validation result, assuming success")
                result_data = {"is_successful": True, "status_message": "任务已完成"}

            # 4. 更新状态
            if result_data.get("is_successful"):
                state["final_status"] = "success"
                logger.success("Task validation passed")
            else:
                state["final_status"] = "failed"
                state["error_info"] = result_data.get("failure_reason", "Unknown error")
                logger.error(f"Task validation failed: {state['error_info']}")

            state["current_agent"] = "validator"
            state["updated_at"] = datetime.utcnow().isoformat()

            return state

        except Exception as e:
            logger.error(f"Validation error: {e}")
            state["error_info"] = f"Validation error: {str(e)}"
            state["final_status"] = "failed"
            return state


# 全局实例
validator_agent = ValidatorAgent()
