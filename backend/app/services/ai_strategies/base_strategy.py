from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Any
from app.services.ai_provider_service import AIProviderInterface

class WriterStrategyInterface(ABC):
    @abstractmethod
    async def generate(
        self,
        provider: AIProviderInterface,
        model_id: str,
        # Base prompt template will be accessed directly by the strategy from utils
        personality_prompt: str,
        contest_description: Optional[str],
        user_guidance_title: Optional[str],
        user_guidance_description: Optional[str],
        temperature: float,
        max_tokens: Optional[int]
    ) -> Tuple[str, int, int]:  # Returns: generated_content, prompt_tokens, completion_tokens
        """Generates text based on the implemented strategy."""
        pass

class JudgeStrategyInterface(ABC):
    @abstractmethod
    async def judge(
        self,
        provider: AIProviderInterface,
        model_id: str,
        # Base prompt template will be accessed directly by the strategy from utils
        personality_prompt: str,
        contest_description: str,
        texts: List[Dict[str, Any]], # List of dicts with 'id', 'title', 'content'
        temperature: float,
        max_tokens: Optional[int]
    ) -> Tuple[List[Dict[str, Any]], int, int]:  # Returns: parsed_votes, prompt_tokens, completion_tokens
        """Judges texts based on the implemented strategy."""
        pass 