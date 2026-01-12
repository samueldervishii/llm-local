"""Local Llama model wrapper using llama-cpp-python with CPU optimizations."""

import hashlib
from functools import lru_cache
from typing import Optional

from llama_cpp import Llama

from config import config


class LocalLLM:
    """Optimized wrapper for local Llama model inference on CPU."""

    def __init__(self):
        self._model: Optional[Llama] = None
        self._cache: dict[str, str] = {}

    def load(self) -> None:
        """Load the Llama model with optimized settings."""
        config.validate()
        self._model = Llama(
            model_path=config.MODEL_PATH,
            n_threads=config.MODEL_THREADS,
            n_threads_batch=config.MODEL_THREADS,  # Use same threads for batch
            n_ctx=config.MODEL_CTX,
            n_batch=config.MODEL_BATCH,  # Larger batch = faster prompt processing
            n_gpu_layers=config.MODEL_GPU_LAYERS,
            use_mmap=True,  # Memory-map for faster loading
            use_mlock=False,  # Don't lock memory (better for multi-tasking)
            verbose=False,
        )

    @property
    def model(self) -> Llama:
        """Get the loaded model."""
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load() first.")
        return self._model

    def _get_cache_key(self, system: str, user: str) -> str:
        """Generate cache key from prompts."""
        content = f"{system}:{user}"
        return hashlib.sha256(content.encode()).hexdigest()

    def generate(
        self,
        prompt: str,
        max_tokens: int = 1536,
        temperature: float = 0.3,
        stop: Optional[list[str]] = None,
    ) -> str:
        """
        Generate text completion from the model.

        Args:
            prompt: Input prompt for generation.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (lower = more deterministic).
            stop: Optional stop sequences.

        Returns:
            Generated text response.
        """
        response = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop or [],
            echo=False,
        )
        return response["choices"][0]["text"].strip()

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1536,
        temperature: float = 0.3,
        use_cache: bool = True,
    ) -> str:
        """
        Generate a chat completion using Llama chat format.

        Args:
            system_prompt: System instructions.
            user_message: User input message.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            use_cache: Whether to use response cache.

        Returns:
            Assistant's response.
        """
        # Check cache first
        if use_cache and config.CACHE_ENABLED:
            cache_key = self._get_cache_key(system_prompt, user_message)
            if cache_key in self._cache:
                return self._cache[cache_key]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = self.model.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        result = response["choices"][0]["message"]["content"].strip()

        # Cache the result
        if use_cache and config.CACHE_ENABLED:
            self._cache[cache_key] = result

        return result

    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._cache.clear()

    def unload(self) -> None:
        """Unload the model from memory."""
        self._cache.clear()
        self._model = None

    def __enter__(self):
        """Context manager entry."""
        self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.unload()
