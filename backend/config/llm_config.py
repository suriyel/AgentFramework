"""
LLM Configuration Manager - 多平台LLM配置管理
支持阿里百炼、OpenAI、Azure、智谱AI、火山引擎等
"""
from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
from loguru import logger
import os


# ============ LLM Provider Enum ============

LLMProvider = Literal[
    "dashscope",      # 阿里百炼
    "openai",         # OpenAI
    "azure_openai",   # Azure OpenAI
    "zhipuai",        # 智谱AI
    "volcengine",     # 火山引擎（豆包）
    "ollama",         # Ollama本地
    "custom"          # 自定义兼容OpenAI API
]


# ============ LLM Configuration Models ============

class LLMConfig(BaseModel):
    """LLM 基础配置"""
    provider: LLMProvider
    model_name: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=32000)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    timeout: int = Field(default=60, ge=1, le=300)


class DashScopeConfig(LLMConfig):
    """阿里百炼配置"""
    provider: Literal["dashscope"] = "dashscope"
    api_key: str
    model_name: str = "qwen-max"  # qwen-max, qwen-plus, qwen-turbo


class OpenAIConfig(LLMConfig):
    """OpenAI 配置"""
    provider: Literal["openai"] = "openai"
    api_key: str
    model_name: str = "gpt-4"  # gpt-4, gpt-3.5-turbo
    base_url: Optional[str] = None


class AzureOpenAIConfig(LLMConfig):
    """Azure OpenAI 配置"""
    provider: Literal["azure_openai"] = "azure_openai"
    api_key: str
    azure_endpoint: str
    api_version: str = "2024-02-15-preview"
    deployment_name: str
    model_name: str = "gpt-4"


class ZhipuAIConfig(LLMConfig):
    """智谱AI 配置"""
    provider: Literal["zhipuai"] = "zhipuai"
    api_key: str
    model_name: str = "glm-4"  # glm-4, glm-3-turbo


class VolcEngineConfig(LLMConfig):
    """火山引擎（豆包）配置"""
    provider: Literal["volcengine"] = "volcengine"
    api_key: str
    endpoint_id: str
    model_name: str = "doubao-pro"


class OllamaConfig(LLMConfig):
    """Ollama 本地配置"""
    provider: Literal["ollama"] = "ollama"
    base_url: str = "http://localhost:11434"
    model_name: str = "qwen2.5:latest"


class CustomLLMConfig(LLMConfig):
    """自定义LLM配置（兼容OpenAI API）"""
    provider: Literal["custom"] = "custom"
    api_key: Optional[str] = None
    base_url: str
    model_name: str


# ============ LLM Factory ============

class LLMFactory:
    """LLM 工厂类 - 根据配置创建LLM实例"""

    @staticmethod
    def create_llm(config: LLMConfig) -> BaseChatModel:
        """
        根据配置创建LLM实例

        Args:
            config: LLM配置对象

        Returns:
            BaseChatModel实例
        """
        provider = config.provider
        logger.info(f"Creating LLM: provider={provider}, model={config.model_name}")

        try:
            if provider == "dashscope":
                return LLMFactory._create_dashscope(config)
            elif provider == "openai":
                return LLMFactory._create_openai(config)
            elif provider == "azure_openai":
                return LLMFactory._create_azure_openai(config)
            elif provider == "zhipuai":
                return LLMFactory._create_zhipuai(config)
            elif provider == "volcengine":
                return LLMFactory._create_volcengine(config)
            elif provider == "ollama":
                return LLMFactory._create_ollama(config)
            elif provider == "custom":
                return LLMFactory._create_custom(config)
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to create LLM: {e}")
            raise

    @staticmethod
    def _create_dashscope(config: DashScopeConfig) -> BaseChatModel:
        """创建阿里百炼LLM"""
        from langchain_community.chat_models import ChatTongyi

        return ChatTongyi(
            model_name=config.model_name,
            dashscope_api_key=config.api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
        )

    @staticmethod
    def _create_openai(config: OpenAIConfig) -> BaseChatModel:
        """创建OpenAI LLM"""
        return ChatOpenAI(
            model=config.model_name,
            openai_api_key=config.api_key,
            base_url=config.base_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout,
        )

    @staticmethod
    def _create_azure_openai(config: AzureOpenAIConfig) -> BaseChatModel:
        """创建Azure OpenAI LLM"""
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            azure_deployment=config.deployment_name,
            azure_endpoint=config.azure_endpoint,
            api_key=config.api_key,
            api_version=config.api_version,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    @staticmethod
    def _create_zhipuai(config: ZhipuAIConfig) -> BaseChatModel:
        """创建智谱AI LLM"""
        from langchain_community.chat_models import ChatZhipuAI

        return ChatZhipuAI(
            model=config.model_name,
            api_key=config.api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    @staticmethod
    def _create_volcengine(config: VolcEngineConfig) -> BaseChatModel:
        """创建火山引擎LLM"""
        # 火山引擎使用OpenAI兼容接口
        return ChatOpenAI(
            model=config.model_name,
            openai_api_key=config.api_key,
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    @staticmethod
    def _create_ollama(config: OllamaConfig) -> BaseChatModel:
        """创建Ollama本地LLM"""
        return ChatOpenAI(
            base_url=config.base_url,
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key="ollama",  # Ollama不需要真实key
        )

    @staticmethod
    def _create_custom(config: CustomLLMConfig) -> BaseChatModel:
        """创建自定义LLM（兼容OpenAI API）"""
        return ChatOpenAI(
            base_url=config.base_url,
            model=config.model_name,
            openai_api_key=config.api_key or "custom",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )


# ============ LLM Manager ============

class LLMManager:
    """LLM 管理器 - 单例模式"""

    _instance = None
    _current_config: Optional[LLMConfig] = None
    _current_llm: Optional[BaseChatModel] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def set_config(self, config: LLMConfig):
        """设置LLM配置并创建实例"""
        self._current_config = config
        self._current_llm = LLMFactory.create_llm(config)
        logger.success(f"LLM configured: {config.provider}/{config.model_name}")

    def get_llm(self) -> BaseChatModel:
        """获取当前LLM实例"""
        if self._current_llm is None:
            # 使用默认配置（从环境变量）
            self._load_from_env()

        return self._current_llm

    def get_config(self) -> Optional[LLMConfig]:
        """获取当前配置"""
        return self._current_config

    def _load_from_env(self):
        """从环境变量加载默认配置"""
        provider = os.getenv("LLM_PROVIDER", "ollama")

        logger.info(f"Loading LLM config from environment: provider={provider}")

        if provider == "dashscope":
            config = DashScopeConfig(
                api_key=os.getenv("DASHSCOPE_API_KEY", ""),
                model_name=os.getenv("DASHSCOPE_MODEL", "qwen-max"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
            )
        elif provider == "openai":
            config = OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model_name=os.getenv("OPENAI_MODEL", "gpt-4"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
            )
        elif provider == "azure_openai":
            config = AzureOpenAIConfig(
                api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
                model_name=os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
            )
        elif provider == "zhipuai":
            config = ZhipuAIConfig(
                api_key=os.getenv("ZHIPUAI_API_KEY", ""),
                model_name=os.getenv("ZHIPUAI_MODEL", "glm-4"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
            )
        elif provider == "volcengine":
            config = VolcEngineConfig(
                api_key=os.getenv("VOLCENGINE_API_KEY", ""),
                endpoint_id=os.getenv("VOLCENGINE_ENDPOINT_ID", ""),
                model_name=os.getenv("VOLCENGINE_MODEL", "doubao-pro"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
            )
        elif provider == "ollama":
            config = OllamaConfig(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                model_name=os.getenv("OLLAMA_MODEL", "qwen2.5:latest"),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
            )
        else:
            # 默认使用Ollama
            config = OllamaConfig(
                base_url="http://localhost:11434",
                model_name="qwen2.5:latest",
                temperature=0.7,
                max_tokens=2048,
            )

        self.set_config(config)


# 全局LLM管理器实例
llm_manager = LLMManager()


# ============ Helper Functions ============

def get_llm() -> BaseChatModel:
    """获取全局LLM实例"""
    return llm_manager.get_llm()


def set_llm_config(config: LLMConfig):
    """设置全局LLM配置"""
    llm_manager.set_config(config)
