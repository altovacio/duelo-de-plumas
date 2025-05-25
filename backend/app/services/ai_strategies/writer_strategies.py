import time
from typing import Tuple, Optional, List, Dict, Any
from app.services.ai_strategies.base_strategy import WriterStrategyInterface
from app.services.ai_provider_service import AIProviderInterface
from app.utils.writer_prompts import WRITER_BASE_PROMPT # Import base prompt

# Version constant for tracking AI writer strategy changes
WRITER_VERSION = "1.0"

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
        max_tokens: Optional[int],
        # Debug logging parameters (optional)
        db_session=None,
        user_id: Optional[int] = None,
        agent_id: Optional[int] = None
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

        # Track execution time for debug logging
        start_time = time.time()
        
        generated_content, prompt_tokens, completion_tokens = await provider.generate_text(
            model_id=model_id,
            prompt=full_prompt,
            system_message=system_message_for_provider,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Debug logging (development only)
        if db_session is not None:
            from app.utils.debug_logger import AIDebugLogger
            from app.utils.ai_models import estimate_cost_usd
            
            # Calculate cost
            cost_usd = estimate_cost_usd(model_id, prompt_tokens, completion_tokens)
            
            # Prepare strategy input for logging
            strategy_input = {
                "personality_prompt": personality_prompt,
                "contest_description": contest_description,
                "user_guidance_title": user_guidance_title,
                "user_guidance_description": user_guidance_description,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            await AIDebugLogger.log_writer_operation(
                db=db_session,
                user_id=user_id,
                agent_id=agent_id,
                model_id=model_id,
                strategy_input=strategy_input,
                llm_prompt=full_prompt,
                llm_response=generated_content,
                parsed_output=generated_content,  # For writer, output = response
                execution_time_ms=execution_time_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd
            )
        
        return generated_content, prompt_tokens, completion_tokens 