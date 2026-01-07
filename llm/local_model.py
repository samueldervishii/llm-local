"""Local Llama model wrapper using llama-cpp-python."""

from typing import Optional
from llama_cpp import Llama

from config import config


class LocalLLM:
    """Wrapper for local Llama model inference."""

    def __init__(self):
        self._model: Optional[Llama] = None

    def load(self) -> None:
        """Load the Llama model into memory."""
        config.validate()
        self._model = Llama(
            model_path=config.MODEL_PATH,
            n_threads=config.MODEL_THREADS,
            n_ctx=config.MODEL_CTX,
            verbose=False,
        )

    @property
    def model(self) -> Llama:
        """Get the loaded model."""
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load() first.")
        return self._model

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
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
        max_tokens: int = 2048,
        temperature: float = 0.3,
    ) -> str:
        """
        Generate a chat completion using Llama chat format.

        Args:
            system_prompt: System instructions.
            user_message: User input message.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            Assistant's response.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = self.model.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response["choices"][0]["message"]["content"].strip()

    def unload(self) -> None:
        """Unload the model from memory."""
        self._model = None

    def __enter__(self):
        """Context manager entry."""
        self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.unload()
