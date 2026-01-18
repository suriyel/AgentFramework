"""
FastAPI Main Application
"""
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.config.settings import settings
from backend.api.routes import router
from backend.api.websocket import websocket_router
from backend.api.llm_routes import router as llm_router
from backend.state.persistence import db_manager
# 导入工作流实例以便在关闭时清理
from backend.graph.workflow import agent_workflow

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="DEBUG" if settings.DEBUG else "INFO"
)

# 1. 定义生命周期管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    管理应用的启动和关闭生命周期
    """
    # --- 启动逻辑 (Startup) ---
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # 初始化数据库
    try:
        # 如果 db_manager 是异步的，这里可能需要 await
        db_manager.create_tables()
        logger.success("Database tables initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    logger.success("Application startup complete")

    yield  # 运行应用期间在这里挂起

    # --- 关闭逻辑 (Shutdown) ---
    logger.info("Shutting down application...")

    try:
        # 调用 workflow 中我们新增的 close 方法释放 SQLite 连接
        agent_workflow.close()
        logger.success("Agent workflow resources released")
    except Exception as e:
        logger.error(f"Error during resource cleanup: {e}")

    logger.info("Application shutdown complete")


# 2. 创建 FastAPI 应用并关联 lifespan
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix=settings.API_PREFIX)
app.include_router(llm_router, prefix=settings.API_PREFIX)
app.include_router(websocket_router)


@app.get("/")
async def root():
    """健康检查"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """详细健康检查"""
    return {
        "status": "healthy",
        "database": "connected",
        "cache": "connected"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )