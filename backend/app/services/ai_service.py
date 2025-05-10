from typing import Dict, List, Optional, Tuple
import os
import json
import logging
from fastapi import HTTPException, status

from app.utils.ai_models import (
    get_model_by_id,
    is_model_available,
    estimate_credits,
    estimate_cost_usd
)
from app.services.ai_provider_service import get_provider_for_model, estimate_token_count

# Configure logger
logger = logging.getLogger(__name__)

# This is a placeholder for actual LLM integration
# In a real implementation, you would use a library like openai for GPT models
class AIService:
    """Service for interacting with LLM models."""
    
    # Available models and their cost per 1000 tokens
    AVAILABLE_MODELS = {
        "gpt-3.5-turbo": 0.002,  # $0.002 per 1k tokens
        "gpt-4": 0.06,           # $0.06 per 1k tokens
        "gpt-4-turbo": 0.03,     # $0.03 per 1k tokens
        "claude-3-sonnet": 0.03, # $0.03 per 1k tokens
        "claude-3-opus": 0.15,   # $0.15 per 1k tokens
    }
    
    @classmethod
    def validate_model(cls, model: str) -> None:
        """Validate that the requested model is available."""
        if not is_model_available(model):
            # Get list of available models for error message
            from app.utils.ai_models import get_available_models
            available_models = [model.id for model in get_available_models()]
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model '{model}' not available or not enabled. Available models: {available_models}"
            )
            
    @classmethod
    def estimate_token_count(cls, text: str) -> int:
        """
        Estimate the number of tokens in a text.
        This is a simple approximation.
        """
        return estimate_token_count(text)
        
    @classmethod
    def estimate_cost(cls, model: str, prompt_tokens: int, completion_tokens: Optional[int] = None) -> int:
        """
        Estimate the cost in credits for a given model and token counts.
        Returns the cost in credits (1 credit = $0.01).
        """
        cls.validate_model(model)
        return estimate_credits(model, prompt_tokens, completion_tokens)
    
    @classmethod
    async def generate_text(
        cls, 
        model: str, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Tuple[str, int, float]:
        """
        Generate text using an LLM model.
        Returns (generated_text, tokens_used, cost_per_1k).
        """
        cls.validate_model(model)
        
        # Get the provider implementation for this model
        provider_class = get_provider_for_model(model)
        if not provider_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No provider implementation available for model '{model}'"
            )
        
        try:
            # Call the provider to generate text
            generated_text, prompt_tokens, completion_tokens = await provider_class.generate_text(
                model_id=model,
                prompt=prompt,
                system_message=system_message,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            total_tokens = prompt_tokens + completion_tokens
            
            # Get cost rate information
            model_info = get_model_by_id(model)
            avg_cost_per_1k = (
                model_info.input_cost_usd_per_1k_tokens * prompt_tokens + 
                model_info.output_cost_usd_per_1k_tokens * completion_tokens
            ) / total_tokens * 1000 if total_tokens > 0 else 0
            
            return generated_text, total_tokens, avg_cost_per_1k
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating text: {str(e)}"
            )
        
    @classmethod
    async def judge_contest(
        cls,
        model: str,
        judge_prompt: str,
        contest_description: str,
        texts: List[Dict]
    ) -> Tuple[List[Dict], int, float]:
        """
        Judge a contest using an LLM model.
        Returns (judging_results, tokens_used, cost_per_1k).
        """
        cls.validate_model(model)
        
        # Get the provider implementation for this model
        provider_class = get_provider_for_model(model)
        if not provider_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No provider implementation available for model '{model}'"
            )
        
        # Determine if we can use batch processing 
        model_info = get_model_by_id(model)
        use_batch = len(texts) > 1
        
        try:
            # If there's just one text or we can't use batching, use the standard method
            if len(texts) <= 1 or not use_batch:
                # Build the complete prompt for a single evaluation
                prompt = f"{judge_prompt}\n\nContest Description: {contest_description}\n\n"
                
                for i, text in enumerate(texts):
                    prompt += f"Text #{i+1}:\nTitle: {text['title']}\nContent: {text['content']}\n\n"
                
                prompt += "Please evaluate all texts and assign 1st place to the best, 2nd place to the second best, and 3rd place to the third best. Provide a justification for each choice."
                
                # Generate the judgment
                judgment, prompt_tokens, completion_tokens = await provider_class.generate_text(
                    model_id=model,
                    prompt=prompt,
                    system_message="You are an expert literary judge. Your task is to evaluate texts in a contest and determine the winners. You will provide detailed, constructive feedback.",
                    temperature=0.3  # Lower temperature for more consistent judging
                )
                
                total_tokens = prompt_tokens + completion_tokens
                
                # Parse the judgment to extract results
                results = cls._parse_judging_results(judgment, texts)
                
                # Calculate average cost per 1k tokens
                avg_cost_per_1k = (
                    model_info.input_cost_usd_per_1k_tokens * prompt_tokens + 
                    model_info.output_cost_usd_per_1k_tokens * completion_tokens
                ) / total_tokens * 1000 if total_tokens > 0 else 0
                
                return results, total_tokens, avg_cost_per_1k
            
            else:
                # For multiple texts, we'll use batch processing for efficiency
                # We'll create individual prompts for each text to evaluate
                
                # First, prepare a context prompt that will be used for all evaluations
                context_prompt = f"Contest Description: {contest_description}\n\n"
                context_prompt += "You are judging a literary contest. Evaluate this single text based on the contest description. "
                context_prompt += "Give it a score from 1-10 and provide detailed feedback. Do not compare it to other texts yet."
                
                # Individual prompts for each text
                prompts = []
                for i, text in enumerate(texts):
                    prompt = f"{context_prompt}\n\nText to evaluate:\nTitle: {text['title']}\nContent: {text['content']}\n\n"
                    prompts.append(prompt)
                
                # Get batch evaluations
                batch_results = await provider_class.generate_batch(
                    model_id=model,
                    prompts=prompts,
                    system_message=f"{judge_prompt}\nYou are an expert literary judge evaluating submissions for a contest.",
                    temperature=0.3
                )
                
                # Calculate total tokens and retrieve individual evaluations
                total_prompt_tokens = 0
                total_completion_tokens = 0
                evaluations = []
                
                for i, (text_evaluation, prompt_tokens, completion_tokens) in enumerate(batch_results):
                    total_prompt_tokens += prompt_tokens
                    total_completion_tokens += completion_tokens
                    evaluations.append({
                        "text_id": texts[i].get("id"),
                        "evaluation": text_evaluation,
                        "score": cls._extract_score_from_evaluation(text_evaluation)
                    })
                
                # Now create a ranking prompt based on the individual evaluations
                ranking_prompt = f"Contest Description: {contest_description}\n\n"
                ranking_prompt += "You have evaluated the following texts individually. Now rank them from best to worst.\n\n"
                
                for i, eval_result in enumerate(evaluations):
                    text = texts[i]
                    ranking_prompt += f"Text #{i+1}:\nTitle: {text['title']}\n"
                    ranking_prompt += f"Your evaluation: {eval_result['evaluation'][:200]}...\n"
                    ranking_prompt += f"Score: {eval_result['score']}/10\n\n"
                
                ranking_prompt += "Based on the above, assign 1st place to the best text, 2nd place to the second best, and 3rd place to the third best. "
                ranking_prompt += "Provide a brief explanation for your ranking. Format your response as 'Text #X: Yth place - reason'."
                
                # Generate final ranking
                ranking, ranking_prompt_tokens, ranking_completion_tokens = await provider_class.generate_text(
                    model_id=model,
                    prompt=ranking_prompt,
                    system_message="You are an expert literary judge making the final ranking decision for a contest.",
                    temperature=0.2  # Even lower temperature for the final decision
                )
                
                # Add to token totals
                total_prompt_tokens += ranking_prompt_tokens
                total_completion_tokens += ranking_completion_tokens
                total_tokens = total_prompt_tokens + total_completion_tokens
                
                # Parse the final ranking
                results = cls._parse_ranking_results(ranking, evaluations, texts)
                
                # Calculate average cost per 1k tokens
                avg_cost_per_1k = (
                    model_info.input_cost_usd_per_1k_tokens * total_prompt_tokens + 
                    model_info.output_cost_usd_per_1k_tokens * total_completion_tokens
                ) / total_tokens * 1000 if total_tokens > 0 else 0
                
                return results, total_tokens, avg_cost_per_1k
                
        except Exception as e:
            logger.error(f"Error judging contest: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error judging contest: {str(e)}"
            )
    
    @classmethod
    def _extract_score_from_evaluation(cls, evaluation: str) -> float:
        """Extract a numerical score from an evaluation text."""
        try:
            # First look for a score out of 10 pattern
            import re
            score_patterns = [
                r'(\d+(?:\.\d+)?)\s*\/\s*10',  # e.g. "8/10" or "7.5/10"
                r'score\s*:\s*(\d+(?:\.\d+)?)',  # e.g. "Score: 8" or "SCORE: 7.5"
                r'rating\s*:\s*(\d+(?:\.\d+)?)',  # e.g. "Rating: 8"
                r'(\d+(?:\.\d+)?)\s*out of\s*10',  # e.g. "8 out of 10"
            ]
            
            for pattern in score_patterns:
                match = re.search(pattern, evaluation.lower())
                if match:
                    return float(match.group(1))
            
            # If no explicit score, estimate based on sentiment
            if "excellent" in evaluation.lower() or "outstanding" in evaluation.lower():
                return 9.0
            elif "very good" in evaluation.lower() or "impressive" in evaluation.lower():
                return 8.0
            elif "good" in evaluation.lower():
                return 7.0
            elif "average" in evaluation.lower() or "decent" in evaluation.lower():
                return 5.0
            elif "poor" in evaluation.lower() or "weak" in evaluation.lower():
                return 3.0
            
            # Default score if we couldn't extract one
            return 5.0
            
        except Exception as e:
            logger.warning(f"Failed to extract score from evaluation: {e}")
            return 5.0  # Default to middle score
    
    @classmethod
    def _parse_judging_results(cls, judgment: str, texts: List[Dict]) -> List[Dict]:
        """Parse judging results from a judgment text."""
        results = []
        
        # Try to extract structured results from the judgment text
        lines = judgment.split('\n')
        
        for i, text in enumerate(texts):
            text_id = text.get("id")
            text_num = i + 1
            
            # Look for text references in the judgment
            for j, line in enumerate(lines):
                if f"Text #{text_num}" in line or f"Text {text_num}:" in line:
                    # Found a reference to this text
                    place = None
                    
                    # Try to find place assignment directly (e.g., "1st place")
                    if "1st place" in line or "first place" in line:
                        place = 1
                    elif "2nd place" in line or "second place" in line:
                        place = 2
                    elif "3rd place" in line or "third place" in line:
                        place = 3
                        
                    # Extract comment (all lines until next text or end)
                    comment_lines = []
                    for k in range(j + 1, len(lines)):
                        if "Text #" in lines[k] and ":" in lines[k]: # Heuristic for next text
                            break
                        comment_lines.append(lines[k])
                    
                    comment_text = "\n".join(comment_lines).strip()
                    
                    # Add to results if any information was found
                    if place is not None or comment_text:
                        result_entry = {
                            "text_id": text_id,
                            "text_place": place,
                            "comment": comment_text,
                            "evaluation": judgment # The full judgment for context if needed later
                        }
                        results.append(result_entry)
                    break # Move to next text
        
        # If no structured results, return a generic comment for all texts
        if not results and texts:
            for text_data in texts:
                results.append({
                    "text_id": text_data.get("id"),
                    "text_place": None,
                    "comment": judgment, # Assign full judgment as comment
                    "evaluation": judgment
                })
        return results
    
    @classmethod
    def _parse_ranking_results(cls, ranking_text: str, evaluations: List[Dict], texts: List[Dict]) -> List[Dict]:
        """
        Parse the ranking results from the AI model output.
        
        The expected format is something like:
        Text #1: 1st place - [reason]
        Text #2: 2nd place - [reason]
        Text #3: 3rd place - [reason]
        """
        results = []
        
        try:
            # Try to extract rankings using places (1st, 2nd, 3rd)
            import re
            
            # Only find place-based rankings (e.g., "1st place")
            place_rankings = re.findall(r'Text #(\d+):\s*(\d+)(?:st|nd|rd|th)\s*place', ranking_text, re.IGNORECASE)
            
            # Create a map from text position in the list to its actual ID
            text_position_to_id = {i+1: text["id"] for i, text in enumerate(texts)}
            
            processed_texts_by_pos = set()

            # Process place rankings
            for pos_str, place_str in place_rankings:
                pos = int(pos_str)
                place = int(place_str)
                processed_texts_by_pos.add(pos)
                
                # Only consider valid positions and places
                if pos in text_position_to_id and place in [1, 2, 3]:
                    text_id = text_position_to_id[pos]
                    
                    # Extract the specific comment for this ranking position
                    comment_match = re.search(r'Text #{}:.*?-\s*(.*?)(?=Text #\d+:|$)'.format(pos), 
                                             ranking_text, re.DOTALL | re.IGNORECASE)
                    comment = comment_match.group(1).strip() if comment_match else ""
                    
                    results.append({
                        "text_id": text_id,
                        "text_place": place,
                        "comment": comment
                    })
                    
            # Add texts that were not ranked with a comment from their individual evaluation
            for i, text_data in enumerate(texts):
                text_pos = i + 1
                if text_pos not in processed_texts_by_pos:
                    text_id = text_data.get("id")
                    # Find the corresponding evaluation comment
                    evaluation_entry = next((e for e in evaluations if e["text_id"] == text_id), None)
                    comment = evaluation_entry["evaluation"][:500] + "..." if evaluation_entry else "No specific ranking comment."
                    
                    results.append({
                        "text_id": text_id,
                        "text_place": None, # Not ranked
                        "comment": comment
                    })

        except Exception as e:
            logger.error(f"Error parsing AI ranking results: {e}")
            # Fallback: return all texts with no place and a generic error message as comment
            results = []
            for text_data in texts:
                results.append({
                    "text_id": text_data.get("id"),
                    "text_place": None,
                    "comment": f"Error processing ranking: {str(e)}"
                })
        
        return results
    
    @classmethod
    def estimate_tokens_for_judging(
        cls, 
        model: str, 
        prompt_length: int, 
        contest_desc_length: int, 
        texts: List[Dict]
    ) -> int:
        """
        Estimate the number of tokens that will be used for judging a contest.
        This is a rough estimate based on the length of the prompt, contest description, and texts.
        """
        # Estimate tokens for texts
        text_tokens = 0
        for text in texts:
            # Title plus content plus some overhead
            text_tokens += estimate_token_count(text.get('title', '')) + estimate_token_count(text.get('content', '')) + 50
        
        # Estimate for individual evaluations
        eval_tokens = text_tokens * 2  # Roughly double the text size for evaluations
        
        # Estimate for final ranking
        # Base prompt + contest description + some text for each evaluation
        ranking_tokens = contest_desc_length + 200 + (len(texts) * 100)
        
        # System message tokens
        system_tokens = 100
        
        # Total estimate
        total_tokens = prompt_length + contest_desc_length + text_tokens + eval_tokens + ranking_tokens + system_tokens
        
        # Add a buffer for safety
        return int(total_tokens * 1.2)  # 20% buffer 