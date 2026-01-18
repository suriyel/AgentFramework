"""
LangGraph Workflow - Agent 工作流定义
实现 Plan-and-Execute 模式的 Multi-Agent 协作
"""
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from loguru import logger

from backend.state.models import AgentState
from backend.agents.planner import planner_agent
from backend.agents.executor import executor_agent
from backend.agents.validator import validator_agent
from backend.agents.supervisor import supervisor_agent


class AgentWorkflow:
    """Agent 工作流管理器"""

    def __init__(self, checkpoint_db_path: str = "./data/checkpoints.db"):
        """
        初始化工作流

        Args:
            checkpoint_db_path: Checkpoint 数据库路径
        """
        self.checkpoint_saver = SqliteSaver.from_conn_string(checkpoint_db_path)
        self.graph = self._build_graph()
        logger.info("Agent workflow initialized")

    def _build_graph(self) -> StateGraph:
        """构建 LangGraph"""

        # 1. 创建 StateGraph
        workflow = StateGraph(AgentState)

        # 2. 添加节点（Agents）
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("executor", self._executor_node)
        workflow.add_node("validator", self._validator_node)

        # 3. 设置入口点
        workflow.set_entry_point("planner")

        # 4. 添加条件边（由 Supervisor 路由）
        workflow.add_conditional_edges(
            "planner",
            self._supervisor_route,
            {
                "executor": "executor",
                "validator": "validator",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "executor",
            self._supervisor_route,
            {
                "executor": "executor",  # 继续下一步
                "validator": "validator",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "validator",
            self._supervisor_route,
            {
                "planner": "planner",  # 重新规划（如果需要）
                "end": END
            }
        )

        # 5. 编译图
        compiled_graph = workflow.compile(checkpointer=self.checkpoint_saver)

        logger.success("LangGraph compiled successfully")
        return compiled_graph

    async def _planner_node(self, state: AgentState) -> AgentState:
        """Planner 节点"""
        logger.info("Entering Planner node")
        return await planner_agent.plan(state)

    async def _executor_node(self, state: AgentState) -> AgentState:
        """Executor 节点"""
        logger.info("Entering Executor node")
        return await executor_agent.execute_step(state)

    async def _validator_node(self, state: AgentState) -> AgentState:
        """Validator 节点"""
        logger.info("Entering Validator node")
        return await validator_agent.validate(state)

    def _supervisor_route(
        self,
        state: AgentState
    ) -> Literal["planner", "executor", "validator", "end"]:
        """Supervisor 路由逻辑"""
        return supervisor_agent.route(state)

    async def run(
        self,
        user_input: str,
        conversation_id: str,
        user_id: str,
        config: dict = None
    ) -> AgentState:
        """
        运行工作流

        Args:
            user_input: 用户输入
            conversation_id: 对话 ID
            user_id: 用户 ID
            config: 运行配置（包含 thread_id 等）

        Returns:
            最终状态
        """
        from datetime import datetime

        # 初始化状态
        initial_state: AgentState = {
            "user_input": user_input,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "todo_list": [],
            "current_step_index": 0,
            "step_results": [],
            "context": {},
            "current_agent": "supervisor",
            "final_status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "token_count": 0,
            "compressed_history": []
        }

        # 运行配置
        run_config = config or {}
        if "configurable" not in run_config:
            run_config["configurable"] = {
                "thread_id": conversation_id  # 使用 conversation_id 作为 thread_id
            }

        logger.info(f"Starting workflow for conversation: {conversation_id}")

        try:
            # 执行工作流
            final_state = await self.graph.ainvoke(
                initial_state,
                config=run_config
            )

            logger.success(f"Workflow completed with status: {final_state.get('final_status')}")
            return final_state

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            initial_state["final_status"] = "failed"
            initial_state["error_info"] = str(e)
            return initial_state

    async def stream(
        self,
        user_input: str,
        conversation_id: str,
        user_id: str,
        config: dict = None
    ):
        """
        流式运行工作流（用于实时更新前端）

        Args:
            user_input: 用户输入
            conversation_id: 对话 ID
            user_id: 用户 ID
            config: 运行配置

        Yields:
            状态更新事件
        """
        from datetime import datetime

        initial_state: AgentState = {
            "user_input": user_input,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "todo_list": [],
            "current_step_index": 0,
            "step_results": [],
            "context": {},
            "current_agent": "supervisor",
            "final_status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "token_count": 0,
            "compressed_history": []
        }

        run_config = config or {}
        if "configurable" not in run_config:
            run_config["configurable"] = {
                "thread_id": conversation_id
            }

        logger.info(f"Starting streaming workflow for conversation: {conversation_id}")

        try:
            async for event in self.graph.astream(
                initial_state,
                config=run_config
            ):
                # 每次 Agent 执行后都会产生一个事件
                logger.debug(f"Workflow event: {event}")
                yield event

        except Exception as e:
            logger.error(f"Streaming workflow failed: {e}")
            yield {
                "error": str(e),
                "final_status": "failed"
            }

    def get_state(self, thread_id: str) -> AgentState:
        """
        获取指定 thread 的当前状态

        Args:
            thread_id: Thread ID（通常是 conversation_id）

        Returns:
            当前状态
        """
        config = {"configurable": {"thread_id": thread_id}}
        state = self.graph.get_state(config)
        return state.values if state else None

    def resume(
        self,
        thread_id: str,
        user_provided_config: dict = None
    ) -> AgentState:
        """
        恢复一个暂停的工作流（用于 Human-in-the-Loop）

        Args:
            thread_id: Thread ID
            user_provided_config: 用户提供的配置

        Returns:
            更新后的状态
        """
        config = {"configurable": {"thread_id": thread_id}}
        state = self.get_state(thread_id)

        if not state:
            raise ValueError(f"No state found for thread: {thread_id}")

        # 清除等待标记，注入用户配置
        state["pending_user_input"] = None
        state["user_provided_config"] = user_provided_config

        logger.info(f"Resuming workflow for thread: {thread_id}")

        # 继续执行
        return self.graph.invoke(state, config=config)


# 全局工作流实例
agent_workflow = AgentWorkflow()
