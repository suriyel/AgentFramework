"""
LangGraph State Models
定义 Agent 工作流中的状态结构
"""
from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


# ============ Enums & Status ============

TaskStatus = Literal["pending", "running", "completed", "failed"]


# ============ Step Models ============

class TaskStep(BaseModel):
    """单个任务步骤"""
    id: str = Field(description="步骤唯一ID")
    title: str = Field(description="步骤标题")
    description: Optional[str] = Field(default=None, description="步骤描述")
    status: TaskStatus = Field(default="pending", description="步骤状态")
    tool_name: Optional[str] = Field(default=None, description="使用的 Tool 名称")
    tool_input: Optional[Dict[str, Any]] = Field(default=None, description="Tool 输入参数")
    tool_output: Optional[Any] = Field(default=None, description="Tool 输出结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    retry_count: int = Field(default=0, description="重试次数")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============ Intent Models ============

class ParsedIntent(BaseModel):
    """解析后的用户意图"""
    goal: str = Field(description="用户目标描述")
    required_tools: List[str] = Field(default_factory=list, description="需要的 Tool 列表")
    required_info: Dict[str, Any] = Field(default_factory=dict, description="需要收集的信息")
    confidence: float = Field(ge=0.0, le=1.0, description="意图识别置信度")


# ============ LangGraph State ============

class AgentState(TypedDict, total=False):
    """LangGraph Agent State"""

    # 输入
    user_input: str
    conversation_id: str
    user_id: str

    # 意图解析
    parsed_intent: Optional[ParsedIntent]

    # 任务规划
    todo_list: List[TaskStep]
    current_step_index: int

    # 执行过程
    step_results: List[Dict[str, Any]]
    context: Dict[str, Any]  # 执行上下文（跨步骤共享）

    # RAG 检索结果
    retrieved_docs: List[str]

    # Human-in-the-Loop
    pending_user_input: Optional[Dict[str, Any]]  # 等待用户输入的配置
    user_provided_config: Optional[Dict[str, Any]]  # 用户提供的配置

    # 状态标识
    current_agent: str  # 当前正在执行的 Agent: supervisor/planner/executor/validator
    final_status: Literal["success", "failed", "pending"]
    error_info: Optional[str]

    # 元信息
    created_at: str
    updated_at: str

    # Token 管理
    token_count: int
    compressed_history: List[str]


# ============ Database Models (SQLAlchemy) ============

from sqlalchemy import Column, String, Integer, JSON, DateTime, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class TaskStatusEnum(enum.Enum):
    """任务状态枚举"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Conversation(Base):
    """对话表"""
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Task(Base):
    """任务表"""
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)
    conversation_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)

    user_input = Column(Text, nullable=False)
    parsed_intent = Column(JSON, nullable=True)

    todo_list = Column(JSON, nullable=True)  # List[TaskStep]
    current_step_index = Column(Integer, default=0)

    context = Column(JSON, default=dict)
    step_results = Column(JSON, default=list)

    status = Column(Enum(TaskStatusEnum), default=TaskStatusEnum.pending)
    error_info = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class Message(Base):
    """消息表"""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True)
    conversation_id = Column(String(36), nullable=False, index=True)
    task_id = Column(String(36), nullable=True, index=True)

    role = Column(String(20), nullable=False)  # user/assistant/system
    content = Column(Text, nullable=False)
    meta = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KnowledgeDocument(Base):
    """知识库文档表"""
    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    meta = Column("metadata", JSON, default=dict)

    # Vector store reference
    vector_id = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
