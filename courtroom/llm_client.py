"""
LLM 客户端 - 用于与 Claude API 交互
"""
import os
import json
from typing import Optional, Dict, Any
from anthropic import Anthropic


class LLMClient:
    """LLM 客户端，封装 Claude API 调用"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-6"):
        """
        初始化 LLM 客户端

        Args:
            api_key: Anthropic API 密钥，如果为 None 则从环境变量读取
            model: 使用的模型，默认 claude-sonnet-4-6
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "未找到 API 密钥。请设置 ANTHROPIC_API_KEY 环境变量或传入 api_key 参数"
            )

        self.client = Anthropic(api_key=self.api_key)
        self.model = model

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 1.0,
        **kwargs
    ) -> str:
        """
        生成文本

        Args:
            prompt: 用户提示
            system: 系统提示
            max_tokens: 最大 token 数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        messages = [{"role": "user", "content": prompt}]

        params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
            **kwargs
        }

        if system:
            params["system"] = system

        response = self.client.messages.create(**params)
        return response.content[0].text

    def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成 JSON 格式的响应

        Args:
            prompt: 用户提示
            system: 系统提示
            max_tokens: 最大 token 数
            **kwargs: 其他参数

        Returns:
            解析后的 JSON 对象
        """
        # 在提示中明确要求 JSON 格式
        json_prompt = f"{prompt}\n\n请以 JSON 格式返回结果。"

        response_text = self.generate(
            prompt=json_prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=0.7,
            **kwargs
        )

        # 尝试提取 JSON
        try:
            # 如果响应包含 markdown 代码块，提取其中的 JSON
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            else:
                json_str = response_text.strip()

            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"无法解析 JSON 响应: {e}\n原始响应: {response_text}")


# 全局单例
_llm_client: Optional[LLMClient] = None


def get_llm_client(api_key: Optional[str] = None, model: str = "claude-sonnet-4-6") -> LLMClient:
    """
    获取全局 LLM 客户端单例

    Args:
        api_key: API 密钥
        model: 模型名称

    Returns:
        LLM 客户端实例
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(api_key=api_key, model=model)
    return _llm_client
