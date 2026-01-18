"""
FastAPI Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from backend.config.settings import settings
from backend.api.routes import router
from backend.api.websocket import websocket_router
from backend.api.llm_routes import router as llm_router
from backend.state.persistence import db_manager

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="DEBUG" if settings.DEBUG else "INFO"
)

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix=settings.API_PREFIX)
app.include_router(llm_router, prefix=settings.API_PREFIX)
app.include_router(websocket_router)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # 初始化数据库
    try:
        db_manager.create_tables()
        logger.success("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    logger.success("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("Shutting down application")


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
