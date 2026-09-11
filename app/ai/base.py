"""AI service abstraction and provider implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class AIService(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    def generate_json(self, prompt: str, schema: type[T], system: str = "") -> T:
        """Generate a structured JSON response validated against ``schema``."""


class AIServiceError(RuntimeError):
    pass
