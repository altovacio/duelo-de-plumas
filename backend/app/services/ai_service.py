from typing import Dict, List, Optional, Tuple
import os
import json
from fastapi import HTTPException, status

from app.utils.ai_models import (
    get_model_by_id,
    is_model_available,
    estimate_credits,
    estimate_cost_usd
)
from app.services.ai_provider_service import get_provider_for_model, estimate_token_count

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
                
                prompt += "Please evaluate all texts and assign 3 points to the best, 2 points to the second best, and 1 point to the third best. Provide a justification for each choice."
                
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
                
                ranking_prompt += "Based on the above, assign 3 points to the best text, 2 points to the second best, and 1 point to the third best. "
                ranking_prompt += "Provide a brief explanation for your ranking. Format your response as 'Text #X: Y points - reason'."
                
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
                    points = 0
                    if "3 points" in line or "first place" in line or "1st place" in line:
                        points = 3
                    elif "2 points" in line or "second place" in line or "2nd place" in line:
                        points = 2
                    elif "1 point" in line or "third place" in line or "3rd place" in line:
                        points = 1
                        
                    # Extract comment (all lines until next text or end)
                    comment_lines = []
                    k = j + 1
                    while k < len(lines) and not any(f"Text #{n}" in lines[k] for n in range(1, len(texts) + 1)):
                        comment_lines.append(lines[k])
                        k += 1
                        
                    comment = "\n".join(comment_lines).strip()
                    if not comment and j + 1 < len(lines):
                        comment = lines[j + 1].strip()
                        
                    results.append({
                        "text_id": text_id,
                        "points": points,
                        "comment": comment
                    })
                    break
        
        # Ensure every text has a result
        processed_text_ids = {result["text_id"] for result in results}
        for text in texts:
            if text.get("id") not in processed_text_ids:
                results.append({
                    "text_id": text.get("id"),
                    "points": 0,
                    "comment": "This text was reviewed but did not place in the top rankings."
                })
        
        return results
        
    @classmethod
    def _parse_ranking_results(cls, ranking: str, evaluations: List[Dict], texts: List[Dict]) -> List[Dict]:
        """Parse ranking results from a ranking text."""
        results = []
        
        # Try to extract structured results from the ranking text
        lines = ranking.split('\n')
        
        # Map of text numbers to points based on extracted ranking
        text_points = {}
        
        # First pass: extract points from the ranking
        for line in lines:
            # Look for patterns like "Text #1: 3 points" or "Text #2: 2 points"
            if "Text #" in line and "point" in line.lower():
                try:
                    # Extract text number
                    import re
                    text_num_match = re.search(r'Text #(\d+)', line)
                    if text_num_match:
                        text_num = int(text_num_match.group(1))
                        
                        # Extract points
                        points_match = re.search(r'(\d+)\s*points?', line.lower())
                        if points_match:
                            points = int(points_match.group(1))
                            text_points[text_num] = points
                except Exception as e:
                    logger.warning(f"Failed to parse ranking line '{line}': {e}")
        
        # Second pass: create results with points and comments
        for i, text in enumerate(texts):
            text_id = text.get("id")
            text_num = i + 1
            
            points = text_points.get(text_num, 0)
            
            # For comments, use a combination of LLM's evaluation and any ranking explanation
            evaluation = evaluations[i]["evaluation"]
            ranking_comment = ""
            
            # Look for specific comments about this text in the ranking
            for line in lines:
                if f"Text #{text_num}" in line:
                    # Get everything after the points
                    parts = line.split("points")
                    if len(parts) > 1:
                        ranking_comment = parts[1].strip()
                        if ranking_comment.startswith("-"):
                            ranking_comment = ranking_comment[1:].strip()
            
            # Combine comments
            if ranking_comment:
                comment = f"{ranking_comment}\n\nDetailed evaluation:\n{evaluation}"
            else:
                comment = evaluation
            
            results.append({
                "text_id": text_id,
                "points": points,
                "comment": comment
            })
        
        return results 