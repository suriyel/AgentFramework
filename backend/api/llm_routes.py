"""
LLM Configuration Routes - LLM配置管理API
"""
from typing import Union
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from backend.config.llm_config import (
    llm_manager,
    LLMConfig,
    DashScopeConfig,
    OpenAIConfig,
    AzureOpenAIConfig,
    ZhipuAIConfig,
    VolcEngineConfig,
    OllamaConfig,
    CustomLLMConfig,
)

router = APIRouter(prefix="/llm", tags=["LLM Configuration"])


# ============ Response Models ============

class LLMConfigResponse(BaseModel):
    """LLM配置响应"""
    provider: str
    model_name: str
    temperature: float
    max_tokens: int
    status: str = "active"


class LLMTestResponse(BaseModel):
    """LLM测试响应"""
    success: bool
    message: str
    response: str = None


# ============ API Endpoints ============

@router.get("/config", response_model=LLMConfigResponse)
async def get_llm_config():
    """获取当前LLM配置"""
    try:
        config = llm_manager.get_config()

        if not config:
            raise HTTPException(status_code=404, detail="No LLM configuration found")

        return LLMConfigResponse(
            provider=config.provider,
            model_name=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            status="active"
        )

    except Exception as e:
        logger.error(f"Failed to get LLM config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def set_llm_config(
    config: Union[
        DashScopeConfig,
        OpenAIConfig,
        AzureOpenAIConfig,
        ZhipuAIConfig,
        VolcEngineConfig,
        OllamaConfig,
        CustomLLMConfig
    ]
):
    """设置LLM配置"""
    try:
        logger.info(f"Setting LLM config: provider={config.provider}, model={config.model_name}")

        # 设置新配置
        llm_manager.set_config(config)

        return {
            "message": "LLM configuration updated successfully",
            "provider": config.provider,
            "model_name": config.model_name
        }

    except Exception as e:
        logger.error(f"Failed to set LLM config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test", response_model=LLMTestResponse)
async def test_llm():
    """测试当前LLM配置"""
    try:
        llm = llm_manager.get_llm()

        # 发送测试消息
        test_prompt = "你好，请简单介绍一下你自己。"

        response = await llm.ainvoke(test_prompt)

        return LLMTestResponse(
            success=True,
            message="LLM test successful",
            response=response.content
        )

    except Exception as e:
        logger.error(f"LLM test failed: {e}")
        return LLMTestResponse(
            success=False,
            message=f"LLM test failed: {str(e)}"
        )


@router.get("/providers")
async def list_providers():
    """列出所有支持的LLM提供商"""
    return {
        "providers": [
            {
                "id": "dashscope",
                "name": "阿里百炼 (DashScope)",
                "description": "阿里云大模型服务，支持通义千问系列模型",
                "models": ["qwen-max", "qwen-plus", "qwen-turbo"],
                "required_fields": ["api_key", "model_name"],
                "optional_fields": ["temperature", "max_tokens", "top_p"]
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "description": "OpenAI官方API，支持GPT系列模型",
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "required_fields": ["api_key", "model_name"],
                "optional_fields": ["base_url", "temperature", "max_tokens"]
            },
            {
                "id": "azure_openai",
                "name": "Azure OpenAI",
                "description": "微软Azure平台的OpenAI服务",
                "models": ["gpt-4", "gpt-35-turbo"],
                "required_fields": ["api_key", "azure_endpoint", "deployment_name"],
                "optional_fields": ["api_version", "temperature", "max_tokens"]
            },
            {
                "id": "zhipuai",
                "name": "智谱AI (GLM)",
                "description": "智谱AI大模型服务，支持ChatGLM系列",
                "models": ["glm-4", "glm-3-turbo"],
                "required_fields": ["api_key", "model_name"],
                "optional_fields": ["temperature", "max_tokens"]
            },
            {
                "id": "volcengine",
                "name": "火山引擎 (豆包)",
                "description": "字节跳动火山引擎大模型服务",
                "models": ["doubao-pro", "doubao-lite"],
                "required_fields": ["api_key", "endpoint_id"],
                "optional_fields": ["model_name", "temperature", "max_tokens"]
            },
            {
                "id": "ollama",
                "name": "Ollama (本地)",
                "description": "本地部署的大模型服务",
                "models": ["qwen2.5:latest", "llama3", "mistral"],
                "required_fields": ["base_url", "model_name"],
                "optional_fields": ["temperature", "max_tokens"]
            },
            {
                "id": "custom",
                "name": "自定义 (OpenAI兼容)",
                "description": "任何兼容OpenAI API的服务",
                "models": [],
                "required_fields": ["base_url", "model_name"],
                "optional_fields": ["api_key", "temperature", "max_tokens"]
            }
        ]
    }


@router.get("/models/{provider}")
async def list_provider_models(provider: str):
    """获取指定提供商的模型列表"""
    models_map = {
        "dashscope": [
            {"id": "qwen-max", "name": "通义千问-Max", "description": "最强性能"},
            {"id": "qwen-plus", "name": "通义千问-Plus", "description": "平衡性能与成本"},
            {"id": "qwen-turbo", "name": "通义千问-Turbo", "description": "快速响应"}
        ],
        "openai": [
            {"id": "gpt-4", "name": "GPT-4", "description": "最强推理能力"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "更快更便宜"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "性价比高"}
        ],
        "zhipuai": [
            {"id": "glm-4", "name": "ChatGLM-4", "description": "最新版本"},
            {"id": "glm-3-turbo", "name": "ChatGLM-3 Turbo", "description": "快速版本"}
        ],
        "volcengine": [
            {"id": "doubao-pro", "name": "豆包-Pro", "description": "专业版"},
            {"id": "doubao-lite", "name": "豆包-Lite", "description": "轻量版"}
        ],
        "ollama": [
            {"id": "qwen2.5:latest", "name": "Qwen 2.5", "description": "通义千问本地版"},
            {"id": "llama3", "name": "Llama 3", "description": "Meta开源模型"},
            {"id": "mistral", "name": "Mistral", "description": "高效开源模型"}
        ]
    }

    if provider not in models_map:
        raise HTTPException(status_code=404, detail=f"Provider not found: {provider}")

    return {"models": models_map[provider]}
