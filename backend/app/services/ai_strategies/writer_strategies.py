from typing import Tuple, Optional, List, Dict, Any
from app.services.ai_strategies.base_strategy import WriterStrategyInterface
from app.services.ai_provider_service import AIProviderInterface
from app.utils.writer_prompts import WRITER_BASE_PROMPT # Import base prompt

class SimpleChatCompletionWriterStrategy(WriterStrategyInterface):
    async def generate(
        self,
        provider: AIProviderInterface,
        model_id: str,
        personality_prompt: str,
        contest_description: Optional[str],
        user_guidance_title: Optional[str],
        user_guidance_description: Optional[str],
        temperature: float,
        max_tokens: Optional[int]
    ) -> Tuple[str, int, int]: # generated_content, prompt_tokens, completion_tokens
        
        input_prompt_parts = []
        if contest_description:
            input_prompt_parts.append(f"Contest Description:\\n{contest_description}")
        
        user_guidance_parts = []
        if user_guidance_title:
            user_guidance_parts.append(f"Title: {user_guidance_title}")
        if user_guidance_description:
            user_guidance_parts.append(f"Description/Elements to include: {user_guidance_description}")
        
        if user_guidance_parts:
            input_prompt_parts.append("User Guidance:\\n" + "\\n".join(user_guidance_parts))
        else:
            input_prompt_parts.append("User Guidance:\\n(None provided)")

        input_details = "\\n\\n".join(input_prompt_parts)

        # Construct the full prompt using the imported WRITER_BASE_PROMPT
        full_prompt = (
            f"{WRITER_BASE_PROMPT}\\n\\n"
            f"Personality Prompt:\\n{personality_prompt}\\n\\n"
            f"Input:\\n{input_details}\\n\\n"
            f"Your Generated Text:" # This matches the expectation for parsing in agent_service
        )
        
        # For this simple strategy, the system_message for the provider is usually None,
        # as instructions are baked into the full_prompt.
        system_message_for_provider = None

        generated_content, prompt_tokens, completion_tokens = await provider.generate_text(
            model_id=model_id,
            prompt=full_prompt,
            system_message=system_message_for_provider,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return generated_content, prompt_tokens, completion_tokens 