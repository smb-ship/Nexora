from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Abstract interface all AI providers must implement."""

    @abstractmethod
    async def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.4,
        max_tokens: int = 800,
        json_mode: bool = False,
    ) -> str:
        """Return the raw text completion from the underlying model."""
        raise NotImplementedError