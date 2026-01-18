"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Agent Workstation"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # LLM Configuration
    LLM_PROVIDER: str = "ollama"  # dashscope, openai, azure_openai, zhipuai, volcengine, ollama
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048

    # DashScope (阿里百炼)
    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_MODEL: str = "qwen-max"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_BASE_URL: Optional[str] = None

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = None
    AZURE_OPENAI_MODEL: str = "gpt-4"

    # ZhipuAI (智谱AI)
    ZHIPUAI_API_KEY: Optional[str] = None
    ZHIPUAI_MODEL: str = "glm-4"

    # VolcEngine (火山引擎)
    VOLCENGINE_API_KEY: Optional[str] = None
    VOLCENGINE_ENDPOINT_ID: Optional[str] = None
    VOLCENGINE_MODEL: str = "doubao-pro"

    # Ollama (本地)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:latest"

    # Vector Database (Chroma)
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    CHROMA_COLLECTION_NAME: str = "knowledge_base"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "agent_workstation"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Agent Configuration
    MAX_TASK_STEPS: int = 20
    MAX_NESTING_DEPTH: int = 3
    MAX_RETRY_COUNT: int = 3
    TOOL_TIMEOUT: int = 60

    # Token Management
    MAX_CONTEXT_TOKENS: int = 8000
    COMPRESSION_THRESHOLD: float = 0.8

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
