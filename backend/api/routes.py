"""
API Routes - REST API 端点
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger

from backend.state.persistence import (
    db_manager,
    cache_manager,
    ConversationRepository,
    TaskRepository,
    MessageRepository
)
from backend.graph.workflow import agent_workflow
from backend.tools.registry import tool_registry
from backend.rag.vectorstore import knowledge_base

router = APIRouter(tags=["Agent API"])


# ============ Pydantic Models ============

class CreateConversationRequest(BaseModel):
    user_id: str
    title: str


class CreateTaskRequest(BaseModel):
    conversation_id: str
    user_id: str
    user_input: str


class ResumeTaskRequest(BaseModel):
    task_id: str
    user_provided_config: dict


class UploadKnowledgeRequest(BaseModel):
    title: str
    content: str
    metadata: Optional[dict] = None


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: str
    conversation_id: str
    user_input: str
    status: str
    todo_list: Optional[List[dict]] = None
    current_step_index: int
    error_info: Optional[str] = None

    class Config:
        from_attributes = True


# ============ Dependencies ============

def get_db():
    """获取数据库会话"""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()


# ============ Conversation Endpoints ============

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    db = Depends(get_db)
):
    """创建新对话"""
    try:
        repo = ConversationRepository(db)
        conversation = repo.create(
            user_id=request.user_id,
            title=request.title
        )
        return conversation
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db = Depends(get_db)
):
    """获取对话详情"""
    repo = ConversationRepository(db)
    conversation = repo.get_by_id(conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.get("/users/{user_id}/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(
    user_id: str,
    db = Depends(get_db)
):
    """获取用户的所有对话"""
    repo = ConversationRepository(db)
    conversations = repo.get_by_user(user_id)
    return conversations


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db = Depends(get_db)
):
    """删除对话"""
    repo = ConversationRepository(db)
    success = repo.delete(conversation_id)

    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"message": "Conversation deleted"}


# ============ Task Endpoints ============

@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    request: CreateTaskRequest,
    db = Depends(get_db)
):
    """创建新任务并开始执行"""
    try:
        # 1. 创建任务记录
        task_repo = TaskRepository(db)
        task = task_repo.create(
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            user_input=request.user_input
        )

        # 2. 创建用户消息
        msg_repo = MessageRepository(db)
        msg_repo.create(
            conversation_id=request.conversation_id,
            task_id=task.id,
            role="user",
            content=request.user_input
        )

        # 3. 异步执行工作流（实际应该用后台任务）
        # 这里简化处理，实际应使用 Celery 或 FastAPI BackgroundTasks
        logger.info(f"Task {task.id} created, workflow will be triggered via WebSocket")

        return task

    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db = Depends(get_db)
):
    """获取任务详情"""
    # 1. 尝试从缓存获取
    cached_state = cache_manager.get_task_state(task_id)

    if cached_state:
        return TaskResponse(**cached_state)

    # 2. 从数据库获取
    task_repo = TaskRepository(db)
    task = task_repo.get_by_id(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.get("/conversations/{conversation_id}/tasks", response_model=List[TaskResponse])
async def get_conversation_tasks(
    conversation_id: str,
    db = Depends(get_db)
):
    """获取对话的所有任务"""
    task_repo = TaskRepository(db)
    tasks = task_repo.get_by_conversation(conversation_id)
    return tasks


@router.post("/tasks/resume")
async def resume_task(
    request: ResumeTaskRequest,
    db = Depends(get_db)
):
    """恢复暂停的任务（Human-in-the-Loop）"""
    try:
        # 使用工作流的 resume 功能
        state = agent_workflow.resume(
            thread_id=request.task_id,
            user_provided_config=request.user_provided_config
        )

        # 更新数据库
        task_repo = TaskRepository(db)
        task_repo.update(
            task_id=request.task_id,
            status=state.get("final_status", "running")
        )

        return {"message": "Task resumed", "state": state}

    except Exception as e:
        logger.error(f"Failed to resume task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Tool Endpoints ============

@router.get("/tools")
async def list_tools():
    """列出所有已注册的 Tools"""
    schemas = tool_registry.get_all_schemas()
    return {
        "tools": [
            {
                "name": name,
                "description": schema.description,
                "requires_auth": schema.requires_auth,
                "requires_user_config": schema.requires_user_config,
                "tags": schema.tags
            }
            for name, schema in schemas.items()
        ]
    }


@router.get("/tools/{tool_name}")
async def get_tool_schema(tool_name: str):
    """获取 Tool 的详细 Schema"""
    schema = tool_registry.get_schema(tool_name)

    if not schema:
        raise HTTPException(status_code=404, detail="Tool not found")

    return schema


# ============ Knowledge Base Endpoints ============

@router.post("/knowledge")
async def upload_knowledge(request: UploadKnowledgeRequest):
    """上传知识库文档"""
    try:
        ids = knowledge_base.add_documents(
            documents=[request.content],
            metadatas=[{
                "title": request.title,
                **(request.metadata or {})
            }]
        )

        return {
            "message": "Knowledge uploaded",
            "document_ids": ids
        }

    except Exception as e:
        logger.error(f"Failed to upload knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/search")
async def search_knowledge(query: str, k: int = 5):
    """搜索知识库"""
    try:
        results = knowledge_base.search(query, k=k)

        return {
            "query": query,
            "results": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in results
            ]
        }

    except Exception as e:
        logger.error(f"Failed to search knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/stats")
async def get_knowledge_stats():
    """获取知识库统计"""
    return knowledge_base.get_collection_stats()
