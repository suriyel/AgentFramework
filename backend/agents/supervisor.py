"""
Supervisor Agent - 协调 Agent
负责：协调 Planner/Executor/Validator，控制工作流
"""
from typing import Literal
from loguru import logger

from backend.state.models import AgentState


class SupervisorAgent:
    """Supervisor Agent - 负责协调其他 Agents"""

    def __init__(self):
        """初始化 Supervisor Agent"""
        logger.info("Supervisor Agent initialized")

    def route(self, state: AgentState) -> Literal["planner", "executor", "validator", "end"]:
        """
        路由决策：决定下一步应该执行哪个 Agent

        Args:
            state: 当前状态

        Returns:
            下一个 Agent 名称或 "end"
        """
        # 1. 如果任务失败，结束
        if state.get("final_status") == "failed":
            logger.info("Routing to END (task failed)")
            return "end"

        # 2. 如果任务成功完成，结束
        if state.get("final_status") == "success":
            logger.info("Routing to END (task completed)")
            return "end"

        # 3. 如果等待用户输入，暂停（返回特殊状态）
        if state.get("pending_user_input"):
            logger.info("Routing to END (waiting for user input)")
            return "end"

        # 4. 如果还没有 TODO 列表，执行 Planner
        if not state.get("todo_list"):
            logger.info("Routing to PLANNER (no todo list)")
            return "planner"

        # 5. 如果 TODO 列表存在但未执行完，执行 Executor
        current_index = state.get("current_step_index", 0)
        todo_list = state.get("todo_list", [])

        if current_index < len(todo_list):
            logger.info(f"Routing to EXECUTOR (step {current_index + 1}/{len(todo_list)})")
            return "executor"

        # 6. 所有步骤执行完成，执行 Validator
        if current_index >= len(todo_list) and state.get("final_status") != "success":
            logger.info("Routing to VALIDATOR (all steps completed)")
            return "validator"

        # 默认结束
        logger.info("Routing to END (default)")
        return "end"

    def should_continue(self, state: AgentState) -> bool:
        """
        判断是否应该继续执行

        Args:
            state: 当前状态

        Returns:
            是否继续
        """
        next_node = self.route(state)
        return next_node != "end"


# 全局实例
supervisor_agent = SupervisorAgent()
