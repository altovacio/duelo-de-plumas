import time
import re
import json
import logging
from typing import Tuple, Optional, List, Dict, Any
from app.services.ai_strategies.base_strategy import WriterStrategyInterface
from app.services.ai_provider_service import AIProviderInterface
from app.services.ai_strategies.writer_prompts import WRITER_BASE_PROMPT

# Version constant for tracking AI writer strategy changes
WRITER_VERSION = "1.0"

# Set up logging
logger = logging.getLogger(__name__)

class WriterOutput:
    """Structured representation of writer output"""
    def __init__(self, title: str, content: str, raw_response: str, parsing_success: bool = True):
        self.title = title
        self.content = content
        self.raw_response = raw_response
        self.parsing_success = parsing_success
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "raw_response": self.raw_response,
            "parsing_success": self.parsing_success
        }

class WriterStrategy(WriterStrategyInterface):
    """
    Modern writer strategy that implements AI best practices for structured output handling.
    """
    
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
    ) -> Tuple[str, int, int]:
        """
        Generate structured writer output with enhanced parsing and validation.
        """
        
        # Build input sections
        input_sections = []
        
        if contest_description:
            input_sections.append(f"Contest Description:\n{contest_description}")
        
        # Handle user guidance more explicitly
        guidance_parts = []
        if user_guidance_title:
            guidance_parts.append(f"Preferred Title: {user_guidance_title}")
        if user_guidance_description:
            guidance_parts.append(f"Requirements: {user_guidance_description}")
        
        if guidance_parts:
            input_sections.append("User Guidance:\n" + "\n".join(guidance_parts))
        
        input_block = "\n\n".join(input_sections) if input_sections else "No specific requirements provided."
        
        # Enhanced prompt with better structure
        enhanced_prompt = f"""{WRITER_BASE_PROMPT}

Personality Instructions:
{personality_prompt}

Writing Context:
{input_block}

Remember: Your response must follow the exact format specified above. Start with "Title:" followed by your title, then "Text:" followed by your creative content."""
        
        # Use system message for better instruction following
        system_message = "You are a professional creative writer. Always follow the exact output format specified in the prompt."
        
        start_time = time.time()
        
        raw_response, prompt_tokens, completion_tokens = await provider.generate_text(
            model_id=model_id,
            prompt=enhanced_prompt,
            system_message=system_message,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Parse with enhanced validation
        parsed_output = self._parse_and_validate_response(raw_response, user_guidance_title)
        
        # Return formatted content
        generated_content = f"Title: {parsed_output.title}\nText: {parsed_output.content}"
        
        # Enhanced debug logging
        if db_session is not None:
            from app.utils.debug_logger import AIDebugLogger
            from app.utils.ai_models import estimate_cost_usd
            
            cost_usd = estimate_cost_usd(model_id, prompt_tokens, completion_tokens)
            
            strategy_input = {
                "strategy_type": "structured",
                "personality_prompt": personality_prompt,
                "contest_description": contest_description,
                "user_guidance_title": user_guidance_title,
                "user_guidance_description": user_guidance_description,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "parsing_success": parsed_output.parsing_success
            }
            
            await AIDebugLogger.log_writer_operation(
                db=db_session,
                user_id=user_id,
                agent_id=agent_id,
                model_id=model_id,
                strategy_input=strategy_input,
                llm_prompt=enhanced_prompt,
                llm_response=raw_response,
                parsed_output=json.dumps(parsed_output.to_dict(), indent=2),
                execution_time_ms=execution_time_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd
            )
        
        return generated_content, prompt_tokens, completion_tokens
    
    def _parse_and_validate_response(self, raw_response: str, fallback_title: Optional[str] = None) -> WriterOutput:
        """
        Enhanced parsing with validation and quality checks.
        """
        logger.info(f"Writer Parser - Processing response (length: {len(raw_response)})")
        
        cleaned_response = raw_response.strip()
        
        # Primary parsing: Look for exact format
        title_pattern = r"^Title:\s*(.+?)(?=\n|$)"
        text_pattern = r"Text:\s*(.+)$"
        
        title_match = re.search(title_pattern, cleaned_response, re.MULTILINE | re.IGNORECASE)
        text_match = re.search(text_pattern, cleaned_response, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        
        if title_match and text_match:
            title = title_match.group(1).strip()
            content = text_match.group(1).strip()
            
            # Validate the parsed content
            if self._validate_parsed_content(title, content):
                logger.info(f"Writer Parser - Success: title='{title[:50]}...', content_length={len(content)}")
                return WriterOutput(title=title, content=content, raw_response=raw_response, parsing_success=True)
            else:
                logger.warning("Writer Parser - Validation failed for parsed content")
        
        # Enhanced fallback strategies
        return self._fallback_parsing(cleaned_response, fallback_title, raw_response)
    
    def _validate_parsed_content(self, title: str, content: str) -> bool:
        """
        Validate that the parsed content meets quality standards.
        """
        # Title validation
        if not title or len(title.strip()) == 0:
            return False
        
        if len(title) > 200:  # Unreasonably long title
            return False
        
        # Content validation
        if not content or len(content.strip()) < 10:  # Too short
            return False
        
        # Check for common parsing errors
        if title.lower().startswith("text:") or content.lower().startswith("title:"):
            return False
        
        return True
    
    def _fallback_parsing(self, cleaned_response: str, fallback_title: Optional[str], raw_response: str) -> WriterOutput:
        """
        Enhanced fallback parsing strategies.
        """
        logger.info("Writer Parser - Applying fallback strategies")
        
        lines = [line.strip() for line in cleaned_response.split('\n') if line.strip()]
        
        if not lines:
            title = fallback_title or "Generated Text"
            logger.warning("Writer Parser - No content lines found, using fallback")
            return WriterOutput(title=title, content=cleaned_response, raw_response=raw_response, parsing_success=False)
        
        # Strategy 1: Smart title detection
        potential_title = lines[0]
        
        # Clean up potential title
        for prefix in ["title:", "Title:", "TITLE:", "**", "*", "#"]:
            if potential_title.lower().startswith(prefix.lower()):
                potential_title = potential_title[len(prefix):].strip()
        
        # Check if it looks like a title
        if (len(potential_title) <= 150 and 
            not potential_title.endswith('.') and 
            not potential_title.lower().startswith('text:')):
            
            title = potential_title
            content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
            
            if content:  # Only use if we have content
                logger.info(f"Writer Parser - Fallback success: '{title[:30]}...'")
                return WriterOutput(title=title, content=content, raw_response=raw_response, parsing_success=False)
        
        # Strategy 2: Use fallback title
        if fallback_title:
            logger.info(f"Writer Parser - Using fallback title: '{fallback_title}'")
            return WriterOutput(title=fallback_title, content=cleaned_response, raw_response=raw_response, parsing_success=False)
        
        # Strategy 3: Generate title from content
        if lines:
            # Try to extract a meaningful title from the first sentence
            first_sentence = lines[0]
            if len(first_sentence) > 150:
                # Take first few words
                words = first_sentence.split()[:8]
                generated_title = ' '.join(words) + "..."
            else:
                generated_title = first_sentence
            
            logger.info(f"Writer Parser - Generated title from content: '{generated_title[:30]}...'")
            return WriterOutput(title=generated_title, content=cleaned_response, raw_response=raw_response, parsing_success=False)
        
        # Final fallback
        logger.warning("Writer Parser - All strategies failed, using generic title")
        return WriterOutput(title="Generated Text", content=cleaned_response, raw_response=raw_response, parsing_success=False) 