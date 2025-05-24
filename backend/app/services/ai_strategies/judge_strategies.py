import re
from typing import List, Dict, Tuple, Optional, Any
import logging # Added standard logging

from app.services.ai_strategies.base_strategy import JudgeStrategyInterface
from app.services.ai_provider_service import AIProviderInterface
from app.utils.judge_prompts import JUDGE_BASE_PROMPT # Import base prompt
# from app.utils.logging_utils import logger # Removed this import

logger = logging.getLogger(__name__) # Initialized standard logger

class SimpleChatCompletionJudgeStrategy(JudgeStrategyInterface):
    async def judge(
        self,
        provider: AIProviderInterface,
        model_id: str,
        personality_prompt: str,
        contest_description: str,
        texts: List[Dict[str, Any]],
        temperature: Optional[float], # Now optional, AIService can pass None
        max_tokens: Optional[int]     # Now optional
    ) -> Tuple[List[Dict[str, Any]], int, int]: # parsed_votes, prompt_tokens, completion_tokens

        texts_to_judge_prompt_block = []
        for i, text_submission in enumerate(texts):
            title = text_submission.get('title', f'Text {i+1}')
            content = text_submission.get('content', '')
            texts_to_judge_prompt_block.append(f"Text: {title}\\nContent:\\n{content}")
        
        texts_input_block = "\\n\\n".join(texts_to_judge_prompt_block)

        full_prompt = (
            f"{JUDGE_BASE_PROMPT}\\n\\n"
            f"Personality Prompt:\\n{personality_prompt}\\n\\n"
            f"Input:\\n"
            f"Contest Description:\\n{contest_description}\\n\\n"
            f"Texts to Judge:\\n{texts_input_block}"
        )
        
        system_message_for_provider = None
        current_temperature = temperature
        current_max_tokens = max_tokens

        llm_response, prompt_tokens, completion_tokens = await provider.generate_text(
            model_id=model_id,
            prompt=full_prompt,
            system_message=system_message_for_provider,
            temperature=current_temperature, 
            max_tokens=current_max_tokens
        )

        parsed_votes = self._parse_judge_llm_response(llm_response, texts)
        
                        # Debug logging        logger.info(f"Judge Strategy Debug - Original texts count: {len(texts)}")        logger.info(f"Judge Strategy Debug - Parsed votes count: {len(parsed_votes)}")        print(f"DEBUG: Judge Strategy - Original texts count: {len(texts)}")        print(f"DEBUG: Judge Strategy - Parsed votes count: {len(parsed_votes)}")        for i, vote in enumerate(parsed_votes):            logger.info(f"Judge Strategy Debug - Vote {i+1}: text_id={vote.get('text_id')}, text_place={vote.get('text_place')}, comment_preview={vote.get('comment', '')[:50]}...")            print(f"DEBUG: Judge Strategy - Vote {i+1}: text_id={vote.get('text_id')}, text_place={vote.get('text_place')}, comment_preview={vote.get('comment', '')[:50]}...")
        
        return parsed_votes, prompt_tokens, completion_tokens

    def _parse_judge_llm_response(self, llm_response: str, original_texts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parses the LLM's judging response (ranking and commentaries) into a structured list.
        Matches titles from the response to original text IDs.
        Expected format from LLM (based on JUDGE_BASE_PROMPT):
        1. [Title of Text A]
           Commentary: [Your commentary for Text A.]
        2. [Title of Text B]
           Commentary: [Your commentary for Text B.]
        ...
        """
        parsed_data = []
        text_map_by_title = {text['title']: text['id'] for text in original_texts}
        
        # Debug logging
        logger.info(f"Judge Parser Debug - LLM Response:\n{llm_response}")
        logger.info(f"Judge Parser Debug - Text map: {text_map_by_title}")
        
        pattern = re.compile(r"^\s*(\d+)\.\s*(.*?)\s*\n\s*Commentary:\s*(.*?)(?=(?:\n\s*\d+\.\s*)|$)", re.MULTILINE | re.DOTALL)
        matches = pattern.findall(llm_response)
        
        logger.info(f"Judge Parser Debug - Regex matches found: {len(matches)}")

        for match in matches:
            try:
                rank_str, title, commentary = match
                rank = int(rank_str)
                title = title.strip()
                commentary = commentary.strip()
                text_id = text_map_by_title.get(title)
                
                logger.info(f"Judge Parser Debug - Processing match: rank={rank}, title='{title}', text_id={text_id}")

                if text_id is None:
                    logger.warning(f"Could not map title '{title}' from LLM response to any original text during judging.")
                    continue 

                # Only assign podium places (1, 2, 3) - texts ranked 4th and below get None
                text_place = rank if rank <= 3 else None
                
                logger.info(f"Judge Parser Debug - Final mapping: text_id={text_id}, original_rank={rank}, final_text_place={text_place}")
                
                parsed_data.append({
                    "text_id": text_id,
                    "text_place": text_place,
                    "comment": commentary,
                })
            except ValueError as e:
                logger.error(f"Error parsing rank for title '{title}' during judging: {e}. Match: {match}")
            except Exception as e:
                logger.error(f"General error parsing LLM judge response entry: {e}. Entry: {match}")
        
        if len(parsed_data) != len(original_texts) and matches:
             logger.warning(f"Number of parsed judge votes ({len(parsed_data)}) does not match number of original texts ({len(original_texts)}). LLM might have missed some or formatting was off.")
        
        parsed_data.sort(key=lambda x: x.get("text_place") or float('inf'))
        return parsed_data 