"""
State Persistence - 状态持久化
PostgreSQL + Redis
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from redis import Redis
from loguru import logger
import json
import uuid

from backend.config.settings import settings
from backend.state.models import Base, Conversation, Task, Message, KnowledgeDocument, TaskStatusEnum


# ============ Database ============

class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        """初始化数据库连接"""
        # Sync engine (for initialization)
        self.engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True
        )

        # Async engine (for runtime)
        async_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        self.async_engine = create_async_engine(
            async_url,
            echo=settings.DEBUG,
            pool_pre_ping=True
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info("Database manager initialized")

    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self.engine)
        logger.success("Database tables created")

    def get_session(self) -> Session:
        """获取同步 Session"""
        return self.SessionLocal()

    async def get_async_session(self) -> AsyncSession:
        """获取异步 Session"""
        from sqlalchemy.ext.asyncio import async_sessionmaker
        async_session = async_sessionmaker(
            self.async_engine,
            expire_on_commit=False
        )
        return async_session()


# ============ Redis Cache ============

class CacheManager:
    """Redis 缓存管理器"""

    def __init__(self):
        """初始化 Redis 连接"""
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        logger.info("Cache manager initialized")

    def set_task_state(self, task_id: str, state: Dict[str, Any], ttl: int = 3600):
        """缓存任务状态（用于快速访问）"""
        key = f"task_state:{task_id}"
        self.redis.setex(key, ttl, json.dumps(state, default=str))

    def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的任务状态"""
        key = f"task_state:{task_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def delete_task_state(self, task_id: str):
        """删除任务状态缓存"""
        key = f"task_state:{task_id}"
        self.redis.delete(key)

    def set_user_session(self, user_id: str, session_data: Dict[str, Any], ttl: int = 86400):
        """设置用户会话"""
        key = f"user_session:{user_id}"
        self.redis.setex(key, ttl, json.dumps(session_data))

    def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户会话"""
        key = f"user_session:{user_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None


# ============ Repository Pattern ============

class ConversationRepository:
    """对话仓储"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, title: str) -> Conversation:
        """创建对话"""
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        logger.info(f"Created conversation: {conversation.id}")
        return conversation

    def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """根据 ID 获取对话"""
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

    def get_by_user(self, user_id: str, limit: int = 50) -> List[Conversation]:
        """获取用户的所有对话"""
        return self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.updated_at.desc()).limit(limit).all()

    def delete(self, conversation_id: str) -> bool:
        """删除对话"""
        conversation = self.get_by_id(conversation_id)
        if conversation:
            self.db.delete(conversation)
            self.db.commit()
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        return False


class TaskRepository:
    """任务仓储"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        conversation_id: str,
        user_id: str,
        user_input: str
    ) -> Task:
        """创建任务"""
        task = Task(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            user_id=user_id,
            user_input=user_input
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        logger.info(f"Created task: {task.id}")
        return task

    def update(self, task_id: str, **kwargs) -> Optional[Task]:
        """更新任务"""
        task = self.get_by_id(task_id)
        if task:
            for key, value in kwargs.items():
                setattr(task, key, value)
            self.db.commit()
            self.db.refresh(task)
            return task
        return None

    def get_by_id(self, task_id: str) -> Optional[Task]:
        """根据 ID 获取任务"""
        return self.db.query(Task).filter(Task.id == task_id).first()

    def get_by_conversation(self, conversation_id: str) -> List[Task]:
        """获取对话的所有任务"""
        return self.db.query(Task).filter(
            Task.conversation_id == conversation_id
        ).order_by(Task.created_at.desc()).all()

    def get_running_tasks(self, user_id: str) -> List[Task]:
        """获取用户正在运行的任务"""
        return self.db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == TaskStatusEnum.running
        ).all()


class MessageRepository:
    """消息仓储"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        conversation_id: str,
        role: str,
        content: str,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """创建消息"""
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            task_id=task_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_by_conversation(
        self,
        conversation_id: str,
        limit: int = 100
    ) -> List[Message]:
        """获取对话的所有消息"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).limit(limit).all()


# 全局实例
db_manager = DatabaseManager()
cache_manager = CacheManager()
