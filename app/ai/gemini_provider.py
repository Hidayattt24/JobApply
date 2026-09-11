"""Gemini provider implementation using the google-genai SDK."""

from __future__ import annotations

import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.ai.base import AIService, AIServiceError
from app.config import get_settings
from app.logging_config import get_logger

T = TypeVar("T", bound=BaseModel)

logger = get_logger(__name__)


class GeminiProvider(AIService):
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.ai_api_key:
            raise AIServiceError(
                "AI_API_KEY is not set. Configure it in .env (Gemini API key)."
            )
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover
            raise AIServiceError(
                "google-genai is not installed. Run: pip install -r requirements.txt"
            ) from exc

        self._client = genai.Client(api_key=settings.ai_api_key)
        self._model = settings.ai_model
        self._temperature = settings.ai_temperature

    def generate_json(self, prompt: str, schema: type[T], system: str = "") -> T:
        try:
            contents = prompt
            if system:
                contents = f"{system}\n\n{prompt}"

            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": schema,
                    "temperature": self._temperature,
                },
            )

            text = getattr(response, "text", None)
            if not text:
                raise AIServiceError("Gemini returned empty response.")

            data = json.loads(text)
            return schema.model_validate(data)
        except ValidationError as exc:
            logger.error("Schema validation failed: %s", exc)
            raise AIServiceError(f"AI response did not match schema: {exc}") from exc
        except AIServiceError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error("Gemini request failed: %s", exc)
            raise AIServiceError(f"AI generation failed: {exc}") from exc


def get_ai_service() -> AIService:
    settings = get_settings()
    provider = settings.ai_provider.lower()
    if provider == "gemini":
        return GeminiProvider()
    raise AIServiceError(f"Unsupported AI provider: {provider}")
