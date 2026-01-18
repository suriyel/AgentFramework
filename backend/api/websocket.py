"""
WebSocket Handler - 实时通信
用于实时推送任务状态更新、TODO 列表变化等
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
from loguru import logger
import json
import asyncio

from backend.graph.workflow import agent_workflow
from backend.state.persistence import db_manager, TaskRepository, MessageRepository
from backend.state.models import TaskStep

websocket_router = APIRouter()


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # conversation_id -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        """建立连接"""
        await websocket.accept()

        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = set()

        self.active_connections[conversation_id].add(websocket)
        logger.info(f"WebSocket connected: conversation={conversation_id}")

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        """断开连接"""
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].discard(websocket)

            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

        logger.info(f"WebSocket disconnected: conversation={conversation_id}")

    async def send_to_conversation(self, conversation_id: str, message: dict):
        """发送消息到对话的所有连接"""
        if conversation_id in self.active_connections:
            disconnected = set()

            for websocket in self.active_connections[conversation_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
                    disconnected.add(websocket)

            # 清理断开的连接
            for ws in disconnected:
                self.disconnect(ws, conversation_id)


manager = ConnectionManager()


@websocket_router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """
    WebSocket 端点

    客户端消息格式:
    {
        "type": "start_task",
        "user_input": "...",
        "user_id": "..."
    }

    服务端消息格式:
    {
        "type": "state_update",
        "data": {...}
    }
    """
    await manager.connect(websocket, conversation_id)

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "start_task":
                # 启动新任务
                await handle_start_task(
                    websocket,
                    conversation_id,
                    data.get("user_input"),
                    data.get("user_id")
                )

            elif message_type == "resume_task":
                # 恢复任务（Human-in-the-Loop）
                await handle_resume_task(
                    websocket,
                    data.get("task_id"),
                    data.get("user_provided_config")
                )

            elif message_type == "ping":
                # 心跳
                await websocket.send_json({"type": "pong"})

            else:
                logger.warning(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, conversation_id)


async def handle_start_task(
    websocket: WebSocket,
    conversation_id: str,
    user_input: str,
    user_id: str
):
    """处理任务启动"""
    try:
        # 1. 创建任务记录
        db = db_manager.get_session()
        task_repo = TaskRepository(db)
        msg_repo = MessageRepository(db)

        task = task_repo.create(
            conversation_id=conversation_id,
            user_id=user_id,
            user_input=user_input
        )

        msg_repo.create(
            conversation_id=conversation_id,
            task_id=task.id,
            role="user",
            content=user_input
        )

        db.close()

        # 2. 发送任务创建确认
        await manager.send_to_conversation(conversation_id, {
            "type": "task_created",
            "data": {
                "task_id": task.id,
                "status": "running"
            }
        })

        # 3. 流式执行工作流
        async for event in agent_workflow.stream(
            user_input=user_input,
            conversation_id=conversation_id,
            user_id=user_id
        ):
            # 提取状态更新
            state = extract_state_from_event(event)

            if state:
                # 广播状态更新
                await manager.send_to_conversation(conversation_id, {
                    "type": "state_update",
                    "data": serialize_state(state)
                })

                # 更新数据库
                update_task_in_db(task.id, state)

        # 4. 任务完成
        logger.info(f"Task {task.id} completed")

    except Exception as e:
        logger.error(f"Task execution error: {e}")
        await manager.send_to_conversation(conversation_id, {
            "type": "task_error",
            "data": {
                "error": str(e)
            }
        })


async def handle_resume_task(
    websocket: WebSocket,
    task_id: str,
    user_provided_config: dict
):
    """处理任务恢复（Human-in-the-Loop）"""
    try:
        # 恢复工作流
        state = agent_workflow.resume(
            thread_id=task_id,
            user_provided_config=user_provided_config
        )

        # 获取 conversation_id
        db = db_manager.get_session()
        task_repo = TaskRepository(db)
        task = task_repo.get_by_id(task_id)
        conversation_id = task.conversation_id
        db.close()

        # 广播恢复事件
        await manager.send_to_conversation(conversation_id, {
            "type": "task_resumed",
            "data": serialize_state(state)
        })

        logger.info(f"Task {task_id} resumed")

    except Exception as e:
        logger.error(f"Task resume error: {e}")
        await websocket.send_json({
            "type": "task_error",
            "data": {"error": str(e)}
        })


def extract_state_from_event(event: dict) -> dict:
    """从 LangGraph 事件中提取状态"""
    # LangGraph 事件格式: {node_name: state_update}
    for node_name, state_data in event.items():
        if isinstance(state_data, dict):
            return state_data
    return None


def serialize_state(state: dict) -> dict:
    """序列化状态（转换为 JSON 友好格式）"""
    if not state:
        return {}

    # 序列化 TaskStep 对象
    todo_list = state.get("todo_list", [])
    serialized_todos = []

    for step in todo_list:
        if isinstance(step, TaskStep):
            serialized_todos.append(step.model_dump())
        else:
            serialized_todos.append(step)

    return {
        "conversation_id": state.get("conversation_id"),
        "user_input": state.get("user_input"),
        "todo_list": serialized_todos,
        "current_step_index": state.get("current_step_index", 0),
        "step_results": state.get("step_results", []),
        "current_agent": state.get("current_agent"),
        "final_status": state.get("final_status"),
        "error_info": state.get("error_info"),
        "pending_user_input": state.get("pending_user_input"),
        "updated_at": state.get("updated_at")
    }


def update_task_in_db(task_id: str, state: dict):
    """更新数据库中的任务状态"""
    try:
        db = db_manager.get_session()
        task_repo = TaskRepository(db)

        # 序列化 todo_list
        todo_list = state.get("todo_list", [])
        serialized_todos = []

        for step in todo_list:
            if isinstance(step, TaskStep):
                serialized_todos.append(step.model_dump())
            else:
                serialized_todos.append(step)

        task_repo.update(
            task_id=task_id,
            todo_list=serialized_todos,
            current_step_index=state.get("current_step_index", 0),
            step_results=state.get("step_results", []),
            status=state.get("final_status", "running"),
            error_info=state.get("error_info")
        )

        db.close()

    except Exception as e:
        logger.error(f"Failed to update task in DB: {e}")
