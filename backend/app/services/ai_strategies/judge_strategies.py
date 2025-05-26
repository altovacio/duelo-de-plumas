import re
import time
from typing import List, Dict, Tuple, Optional, Any
import logging

from app.services.ai_strategies.base_strategy import JudgeStrategyInterface
from app.services.ai_provider_service import AIProviderInterface
from app.services.ai_strategies.judge_prompts import JUDGE_BASE_PROMPT
# Version constant for tracking AI judge strategy changes
JUDGE_VERSION = "1.0"

# Set up logging
logger = logging.getLogger(__name__)

class JudgeOutput:
    """Structured representation of judge output"""
    def __init__(self, votes: List[Dict[str, Any]], raw_response: str, parsing_success: bool = True):
        self.votes = votes
        self.raw_response = raw_response
        self.parsing_success = parsing_success
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "votes": self.votes,
            "raw_response": self.raw_response,
            "parsing_success": self.parsing_success,
            "votes_count": len(self.votes)
        }

class JudgeStrategy(JudgeStrategyInterface):
    """
    Modern judge strategy that implements AI best practices for structured output handling.
    """
    
    async def judge(
        self,
        provider: AIProviderInterface,
        model_id: str,
        personality_prompt: str,
        contest_description: str,
        texts: List[Dict[str, Any]],
        temperature: Optional[float],
        max_tokens: Optional[int],
        # Debug logging parameters (optional)
        db_session=None,
        user_id: Optional[int] = None,
        agent_id: Optional[int] = None,
        contest_id: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """
        Generate structured judge output with enhanced parsing and validation.
        """

        # Build texts section with better formatting
        texts_to_judge_blocks = []
        for i, text_submission in enumerate(texts):
            title = text_submission.get('title', f'Text {i+1}')
            content = text_submission.get('content', '')
            
            # Clean and format the text content
            cleaned_content = self._clean_text_for_judging(content)
            texts_to_judge_blocks.append(f"Text: {title}\\nContent:\\n{cleaned_content}")
        
        texts_input_block = "\\n\\n".join(texts_to_judge_blocks)

        # Enhanced prompt with better structure
        enhanced_prompt = f"""{JUDGE_BASE_PROMPT}

Personality Instructions:
{personality_prompt}

Judging Context:
Contest Description:
{contest_description}

Texts to Judge:
{texts_input_block}

Remember: Follow the exact ranking format specified above. Provide commentary for each text and rank them clearly."""

        # Use system message for better instruction following
        system_message = "You are a professional judge for writing contests. Always follow the exact output format specified in the prompt."

        # Track execution time for debug logging
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
        judge_output = self._parse_and_validate_response(raw_response, texts)
        
        # Debug logging (development only)
        if db_session is not None:
            from app.utils.debug_logger import AIDebugLogger
            from app.utils.ai_models import estimate_cost_usd
            
            # Calculate cost
            cost_usd = estimate_cost_usd(model_id, prompt_tokens, completion_tokens)
            
            # Prepare strategy input for logging
            strategy_input = {
                "strategy_type": "structured",
                "personality_prompt": personality_prompt,
                "contest_description": contest_description,
                "texts_count": len(texts),
                "texts_summary": [
                    {"id": text.get("id"), "title": text.get("title"), "length": len(text.get("content", ""))}
                    for text in texts
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "parsing_success": judge_output.parsing_success
            }
            
            await AIDebugLogger.log_judge_operation(
                db=db_session,
                user_id=user_id,
                agent_id=agent_id,
                contest_id=contest_id,
                model_id=model_id,
                strategy_input=strategy_input,
                llm_prompt=enhanced_prompt,
                llm_response=raw_response,
                parsed_output=judge_output.to_dict(),
                execution_time_ms=execution_time_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd
            )
        
        return judge_output.votes, prompt_tokens, completion_tokens

    def _clean_text_for_judging(self, content: str) -> str:
        """
        Clean and prepare text content for judging.
        """
        if not content:
            return ""
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\\n\\s*\\n\\s*\\n', '\\n\\n', content)
        cleaned = re.sub(r'[ \\t]+', ' ', cleaned)
        
        return cleaned.strip()

    def _parse_and_validate_response(self, raw_response: str, original_texts: List[Dict[str, Any]]) -> JudgeOutput:
        """
        Enhanced parsing with validation and quality checks.
        """
        logger.info(f"Judge Parser - Processing response (length: {len(raw_response)})")
        
        text_map_by_title = {text['title']: text['id'] for text in original_texts}
        
        # Enhanced parsing: More flexible pattern to handle various formats
        # Pattern 1: Standard format with "Commentary:"
        pattern1 = re.compile(r"^\s*(\d+)\.\s*(.*?)\s*\n\s*Commentary:\s*(.*?)(?=(?:\n\s*\d+\.\s*)|$)", re.MULTILINE | re.DOTALL)
        matches = pattern1.findall(raw_response)
        
        # Pattern 2: Alternative format without explicit "Commentary:" label
        if not matches:
            # Look for numbered entries followed by text (more flexible)
            pattern2 = re.compile(r"^\s*(\d+)\.\s*(.*?)\n\s*(.*?)(?=(?:\n\s*\d+\.\s*)|$)", re.MULTILINE | re.DOTALL)
            potential_matches = pattern2.findall(raw_response)
            
            # Filter matches that look like commentary (longer text, descriptive)
            for rank_str, title, potential_commentary in potential_matches:
                if len(potential_commentary.strip()) > 20:  # Likely commentary if substantial text
                    matches.append((rank_str, title, potential_commentary))
        
        logger.info(f"Judge Parser - Regex matches found: {len(matches)}")

        parsed_votes = []
        parsing_success = True

        for match in matches:
            try:
                rank_str, title, commentary = match
                rank = int(rank_str)
                title = title.strip()
                commentary = commentary.strip()
                
                # Clean up title - remove extra whitespace and common prefixes
                title = re.sub(r'\s+', ' ', title)
                
                # Try exact match first
                text_id = text_map_by_title.get(title)
                
                # If no exact match, try fuzzy matching
                if text_id is None:
                    # Try to find partial matches
                    for original_title, original_id in text_map_by_title.items():
                        # Check if the parsed title is contained in the original title or vice versa
                        if (title.lower() in original_title.lower() or 
                            original_title.lower() in title.lower()):
                            text_id = original_id
                            logger.info(f"Judge Parser - Fuzzy match: '{title}' -> '{original_title}' (ID: {text_id})")
                            break
                
                logger.info(f"Judge Parser - Processing match: rank={rank}, title='{title}', text_id={text_id}")

                if text_id is None:
                    logger.warning(f"Could not map title '{title}' from LLM response to any original text during judging.")
                    parsing_success = False
                    continue 

                # Only assign podium places (1, 2, 3) - texts ranked 4th and below get None
                text_place = rank if rank <= 3 else None
                
                logger.info(f"Judge Parser - Final mapping: text_id={text_id}, original_rank={rank}, final_text_place={text_place}")
                
                parsed_votes.append({
                    "text_id": text_id,
                    "text_place": text_place,
                    "comment": commentary,
                })
            except ValueError as e:
                logger.error(f"Error parsing rank for title '{title}' during judging: {e}. Match: {match}")
                parsing_success = False
            except Exception as e:
                logger.error(f"General error parsing LLM judge response entry: {e}. Entry: {match}")
                parsing_success = False
        
        # If we still have no matches, try a more aggressive parsing approach
        if not parsed_votes:
            logger.info("Judge Parser - Attempting fallback parsing strategy")
            parsed_votes, fallback_success = self._fallback_parsing(raw_response, original_texts)
            if not fallback_success:
                parsing_success = False
        
        # Check if we got all expected texts
        if len(parsed_votes) != len(original_texts):
            logger.warning(f"Number of parsed judge votes ({len(parsed_votes)}) does not match number of original texts ({len(original_texts)}). LLM might have missed some or formatting was off.")
            parsing_success = False
        
        # Sort by ranking
        parsed_votes.sort(key=lambda x: x.get("text_place") or float('inf'))
        
        return JudgeOutput(votes=parsed_votes, raw_response=raw_response, parsing_success=parsing_success)
    
    def _fallback_parsing(self, raw_response: str, original_texts: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Fallback parsing strategy for when primary parsing fails.
        """
        logger.info("Judge Parser - Applying fallback parsing strategy")
        
        text_map_by_title = {text['title']: text['id'] for text in original_texts}
        parsed_votes = []
        success = False
        
        # Split response into lines and look for numbered entries
        lines = raw_response.split('\n')
        current_entry = None
        current_commentary = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for numbered entries (1., 2., etc.)
            number_match = re.match(r'^(\d+)\.\s*(.*)', line)
            if number_match:
                # Process previous entry if exists
                if current_entry:
                    self._process_fallback_entry(current_entry, current_commentary, text_map_by_title, parsed_votes)
                
                # Start new entry
                rank = int(number_match.group(1))
                title = number_match.group(2).strip()
                current_entry = {"rank": rank, "title": title}
                current_commentary = []
                success = True
            elif current_entry and line:
                # Add to commentary if we're in an entry
                current_commentary.append(line)
        
        # Process the last entry
        if current_entry:
            self._process_fallback_entry(current_entry, current_commentary, text_map_by_title, parsed_votes)
        
        return parsed_votes, success
    
    def _process_fallback_entry(self, entry: Dict[str, Any], commentary_lines: List[str], 
                               text_map: Dict[str, int], parsed_votes: List[Dict[str, Any]]):
        """
        Process a single entry from fallback parsing.
        """
        rank = entry["rank"]
        title = entry["title"]
        commentary = " ".join(commentary_lines).strip()
        
        # Remove "Commentary:" prefix if present
        if commentary.lower().startswith("commentary:"):
            commentary = commentary[11:].strip()
        
        # Try to match title
        text_id = text_map.get(title)
        
        # If no exact match, try fuzzy matching
        if text_id is None:
            for original_title, original_id in text_map.items():
                if (title.lower() in original_title.lower() or 
                    original_title.lower() in title.lower()):
                    text_id = original_id
                    logger.info(f"Judge Parser - Fallback fuzzy match: '{title}' -> '{original_title}' (ID: {text_id})")
                    break
        
        if text_id is not None:
            # Only assign podium places (1, 2, 3) - texts ranked 4th and below get None
            text_place = rank if rank <= 3 else None
            
            parsed_votes.append({
                "text_id": text_id,
                "text_place": text_place,
                "comment": commentary or f"Ranked #{rank}",
            })
            logger.info(f"Judge Parser - Fallback processed: rank={rank}, title='{title}', text_id={text_id}")
        else:
            logger.warning(f"Judge Parser - Fallback could not match title: '{title}'") 