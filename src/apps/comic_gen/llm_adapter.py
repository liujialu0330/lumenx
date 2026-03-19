"""
LLM Adapter - Unified interface for DashScope, OpenAI-compatible, and ARK APIs.

Supports three providers:
  - dashscope (default): Alibaba Cloud DashScope via OpenAI-compatible endpoint
  - openai: Any OpenAI-compatible API (OpenAI, DeepSeek, Ollama, etc.)
  - ark: Volcengine ARK (Doubao) via OpenAI-compatible endpoint

Configuration via environment variables:
  LLM_PROVIDER=dashscope|openai|ark
  DASHSCOPE_API_KEY=...
  OPENAI_API_KEY=...
  OPENAI_BASE_URL=https://api.openai.com/v1
  OPENAI_MODEL=gpt-4o
  ARK_API_KEY=...

Provider can also be auto-inferred from model name:
  doubao-* models -> ark provider
  qwen*, wan* models -> dashscope provider
"""
import os
import logging
from typing import Dict, List, Optional, Any

from ...utils.endpoints import get_provider_base_url

logger = logging.getLogger(__name__)


def _infer_provider_from_model(model_name: str) -> Optional[str]:
    """Infer the provider from a model name prefix."""
    if not model_name:
        return None
    if model_name.startswith("doubao-"):
        return "ark"
    if model_name.startswith(("qwen", "wan")):
        return "dashscope"
    return None


class LLMAdapter:
    """Unified LLM call interface supporting DashScope, OpenAI-compatible, and ARK APIs."""

    def __init__(self, model: Optional[str] = None):
        self._env_provider = os.getenv("LLM_PROVIDER", "dashscope").lower()
        self._model_override = model
        self._client = None
        self._client_provider = None  # tracks which provider the cached client belongs to
        logger.info(f"LLM Adapter initialized with env provider: {self._env_provider}")

    @property
    def _effective_provider(self) -> str:
        """Determine the actual provider to use.

        Priority:
          1. Model name inference (doubao-* -> ark, qwen* -> dashscope)
          2. LLM_PROVIDER env var (explicit user choice)
          3. Auto-detect from available API keys (fallback)
        """
        # 1) Infer from model name
        if self._model_override:
            inferred = _infer_provider_from_model(self._model_override)
            if inferred:
                return inferred

        # 2) If env provider is explicitly set to non-default, respect it
        env_provider = self._env_provider
        if env_provider != "dashscope":
            return env_provider

        # 3) If default (dashscope) but DashScope key is missing, try ARK fallback
        if not os.getenv("DASHSCOPE_API_KEY") and os.getenv("ARK_API_KEY"):
            return "ark"

        return env_provider

    @property
    def is_configured(self) -> bool:
        provider = self._effective_provider
        if provider == "openai":
            return bool(os.getenv("OPENAI_API_KEY"))
        if provider == "ark":
            return bool(os.getenv("ARK_API_KEY"))
        # dashscope or fallback: either DashScope key OR ARK key should work
        # (user may have only ARK configured and will select a doubao model later)
        return bool(os.getenv("DASHSCOPE_API_KEY")) or bool(os.getenv("ARK_API_KEY"))

    def _get_client(self):
        """Get or create the OpenAI-compatible client (lazy, cached per provider)."""
        provider = self._effective_provider

        # Invalidate cache if provider changed
        if self._client is not None and self._client_provider != provider:
            self._client = None

        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise RuntimeError(
                    "openai package not installed. Run: pip install openai>=1.0.0"
                )

            if provider == "openai":
                self._client = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                )
            elif provider == "ark":
                self._client = OpenAI(
                    api_key=os.getenv("ARK_API_KEY"),
                    base_url=get_provider_base_url("ARK"),
                )
            else:
                # DashScope uses OpenAI-compatible endpoint
                self._client = OpenAI(
                    api_key=os.getenv("DASHSCOPE_API_KEY"),
                    base_url=f"{get_provider_base_url('DASHSCOPE')}/compatible-mode/v1",
                )
            self._client_provider = provider
        return self._client

    def _get_default_model(self) -> str:
        if self._model_override:
            return self._model_override
        provider = self._effective_provider
        if provider == "openai":
            return os.getenv("OPENAI_MODEL", "gpt-4o")
        if provider == "ark":
            return "doubao-seed-2-0-pro-260215"
        return "qwen3.5-plus"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Send a chat completion request and return the response content.

        Args:
            messages: List of {"role": ..., "content": ...} dicts
            model: Model name override (uses provider default if None)
            response_format: Optional {"type": "json_object"} constraint

        Returns:
            The assistant's response content as a string.

        Raises:
            RuntimeError: If the API call fails.
        """
        client = self._get_client()
        model = model or self._get_default_model()

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            provider = self._effective_provider
            provider_labels = {"openai": "OpenAI", "ark": "ARK (Doubao)"}
            provider_label = provider_labels.get(provider, "DashScope")
            raise RuntimeError(f"{provider_label} API error: {e}") from e
