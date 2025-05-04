import tiktoken
import openai
import anthropic
import re
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ... import models, schemas
from ..config.settings import Settings, AIModelConfig
from ..dependencies import get_settings # To access settings instance
# Import the base prompts from the new file
from ..config.prompt_templates import BASE_WRITER_INSTRUCTION_PROMPT, BASE_JUDGE_INSTRUCTION_PROMPT

# --- Helper Functions ---

def get_model_config(model_id: str, settings: Settings) -> Optional[AIModelConfig]:
    """Retrieves the configuration for a specific model_id from settings."""
    return settings.AI_MODELS.get(model_id)

def count_tokens(text: str, model_id: str, settings: Settings) -> int:
    """
    Calculates the token count for the given text based on the model.
    Uses tiktoken with fallbacks for models not directly supported by tiktoken.
    """
    model_config = get_model_config(model_id, settings)
    if not model_config:
        # Default or fallback if model info is missing
        # Simple word count as a rough estimate? Or raise error?
        # For now, let's try a default encoding
        try:
            encoding = tiktoken.get_encoding("cl100k_base") # Common default
            return len(encoding.encode(text))
        except Exception:
            return len(text.split()) # Very rough fallback: word count

    # Determine the appropriate tiktoken encoding based on provider/model
    # See: https://github.com/openai/tiktoken/blob/main/tiktoken/model.py
    encoding_name = "cl100k_base" # Default for newer OpenAI models
    if model_config.provider == "openai":
        # Add logic for older models if needed, e.g., based on api_name
        if "gpt-3.5" in model_config.api_name or "gpt-4" in model_config.api_name:
            encoding_name = "cl100k_base"
        # else: handle other specific OpenAI models
    # elif model_config.provider == "anthropic":
        # Anthropic tokenization might differ, cl100k_base is often a reasonable approximation
        # If precise Anthropic token counts are needed, their specific library/method should be used.
        # For now, we use cl100k_base as an estimate.
        # pass 

    try:
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception as e:
        print(f"Error getting tiktoken encoding {encoding_name} for model {model_id}: {e}. Falling back.")
        # Fallback if encoding fails
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            return len(text.split()) # Final fallback: word count

def calculate_monetary_cost(model_id: str, prompt_tokens: int, completion_tokens: int, settings: Settings) -> Optional[float]:
    """
    Calculates the estimated monetary cost (e.g., in USD) based on token counts
    and pricing information from settings. Returns None if cost cannot be determined.
    """
    model_config = get_model_config(model_id, settings)
    if not model_config:
        return None # Cannot calculate cost without model info

    cost = 0.0
    calculated = False

    # Check for cost per 1k tokens first (more common)
    if model_config.cost_per_1k_prompt_tokens is not None and model_config.cost_per_1k_completion_tokens is not None:
        cost += (prompt_tokens / 1000) * model_config.cost_per_1k_prompt_tokens
        cost += (completion_tokens / 1000) * model_config.cost_per_1k_completion_tokens
        calculated = True
    # Fallback to cost per token if 1k costs aren't defined
    elif model_config.cost_per_prompt_token is not None and model_config.cost_per_completion_token is not None:
        cost += prompt_tokens * model_config.cost_per_prompt_token
        cost += completion_tokens * model_config.cost_per_completion_token
        calculated = True

    return cost if calculated else None

def calculate_credit_cost(monetary_cost: Optional[float], prompt_tokens: int, completion_tokens: int, settings: Settings) -> int:
    """
    Translates monetary cost and/or token counts into the integer credit cost
    based on the configured credit cost model settings.
    Handles potential None for monetary_cost and ensures a minimum credit cost.
    """
    credit_cost = 0

    if monetary_cost is not None and settings.CREDITS_PER_DOLLAR > 0:
        # Calculate based on USD cost
        credit_cost = int(monetary_cost * settings.CREDITS_PER_DOLLAR)
    # else:
        # Add alternative calculation based on CREDITS_PER_1K_TOKENS if needed
        # if settings.CREDITS_PER_1K_PROMPT_TOKENS is not None and settings.CREDITS_PER_1K_COMPLETION_TOKENS is not None:
        #     credit_cost += int((prompt_tokens / 1000) * settings.CREDITS_PER_1K_PROMPT_TOKENS)
        #     credit_cost += int((completion_tokens / 1000) * settings.CREDITS_PER_1K_COMPLETION_TOKENS)
        # else:
            # Fallback if no cost model applies? Maybe charge minimum?
            # For now, if monetary cost is None and no token cost is defined, cost is 0 before minimum.

    # Apply minimum cost
    # Ensure cost is at least the minimum, but also at least 0 if calculation yielded negative (shouldn't happen)
    final_cost = max(settings.MINIMUM_CREDIT_COST, credit_cost)
    
    return max(0, final_cost) # Ensure non-negative


async def call_llm_api(
    prompt: str,
    model_id: str,
    settings: Settings,
    openai_client: Optional[openai.AsyncOpenAI] = None,
    anthropic_client: Optional[anthropic.AsyncAnthropic] = None,
    max_tokens: int = 1500, # Default max tokens for completion
    temperature: float = 0.7 # Default temperature
) -> Dict[str, Any]:
    """
    Calls the appropriate LLM API based on the model_id's provider.

    Returns a dictionary containing:
    {'success': bool, 'response_text': Optional[str], 'prompt_tokens': Optional[int],
     'completion_tokens': Optional[int], 'monetary_cost': Optional[float], 'error': Optional[str]}
    """
    model_config = get_model_config(model_id, settings)
    if not model_config:
        return {'success': False, 'error': f"Model configuration not found for ID: {model_id}"}

    provider = model_config.provider
    api_name = model_config.api_name

    response_text = None
    prompt_tokens = None
    completion_tokens = None
    monetary_cost = None
    error_message = None
    success = False

    try:
        # Count prompt tokens before API call
        prompt_tokens = count_tokens(prompt, model_id, settings)

        if provider == "openai" and openai_client:
            # --- OpenAI API Call ---
            completion = await openai_client.chat.completions.create(
                model=api_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant fulfilling a specific role based on the user's prompt."},                    
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                # Add other parameters as needed (e.g., top_p, presence_penalty)
            )
            
            if completion.choices and completion.choices[0].message:
                response_text = completion.choices[0].message.content.strip() if completion.choices[0].message.content else ""
                success = True
            else:
                 error_message = "OpenAI API returned empty response or choices."

            # Get token usage if available
            if success and completion.usage:
                 prompt_tokens = completion.usage.prompt_tokens # Use actual count from API if available
                 completion_tokens = completion.usage.completion_tokens
                 # Recalculate monetary cost with API token counts
                 monetary_cost = calculate_monetary_cost(model_id, prompt_tokens, completion_tokens, settings)
            elif success and response_text:
                # Estimate completion tokens if not provided by API (less accurate)
                 completion_tokens = count_tokens(response_text, model_id, settings)
                 monetary_cost = calculate_monetary_cost(model_id, prompt_tokens, completion_tokens, settings)


        elif provider == "anthropic" and anthropic_client:
            # --- Anthropic API Call ---
            # Note: Anthropic API structure might differ (e.g., system prompt handling)
             message = await anthropic_client.messages.create(
                 model=api_name,
                 system="You are a helpful assistant fulfilling a specific role based on the user's prompt.", # System prompt
                 messages=[
                    {"role": "user", "content": prompt}
                 ],
                 max_tokens=max_tokens, 
                 temperature=temperature,
                 # Add other parameters as needed
             )
             
             if message.content and isinstance(message.content, list) and message.content[0].text:
                 response_text = message.content[0].text.strip()
                 success = True
             else:
                  error_message = "Anthropic API returned empty or unexpected content format."

             # Get token usage if available
             if success and message.usage:
                  prompt_tokens = message.usage.input_tokens # Use actual count from API
                  completion_tokens = message.usage.output_tokens
                  # Recalculate monetary cost with API token counts
                  monetary_cost = calculate_monetary_cost(model_id, prompt_tokens, completion_tokens, settings)
             elif success and response_text:
                 # Estimate completion tokens if not provided by API (less accurate)
                 completion_tokens = count_tokens(response_text, model_id, settings)
                 monetary_cost = calculate_monetary_cost(model_id, prompt_tokens, completion_tokens, settings)

        else:
            error_message = f"Provider '{provider}' not supported or required client not provided."

    except openai.APIError as e:
        error_message = f"OpenAI API Error: {e}"
        print(f"ERROR calling OpenAI: {e}")
    except anthropic.APIError as e:
        error_message = f"Anthropic API Error: {e}"
        print(f"ERROR calling Anthropic: {e}")
    except Exception as e:
        error_message = f"An unexpected error occurred during LLM call: {e}"
        print(f"ERROR calling LLM: {e}")

    # Ensure token counts are integers or None
    prompt_tokens = int(prompt_tokens) if prompt_tokens is not None else None
    completion_tokens = int(completion_tokens) if completion_tokens is not None else None
    
    # Fallback token calculation if API failed or didn't return usage
    if success and response_text and completion_tokens is None:
         completion_tokens = count_tokens(response_text, model_id, settings)
    if prompt_tokens is None: # Should have been calculated before call, but just in case
         prompt_tokens = count_tokens(prompt, model_id, settings)

    # Final cost calculation attempt if needed
    if success and monetary_cost is None and prompt_tokens is not None and completion_tokens is not None:
        monetary_cost = calculate_monetary_cost(model_id, prompt_tokens, completion_tokens, settings)


    return {
        'success': success,
        'response_text': response_text,
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
        'monetary_cost': monetary_cost,
        'error': error_message
    }


# --- Prompt Construction ---

# Base instruction prompt for all AI writers (from ai_params.py)


# Base instruction prompt for all AI judges (from ai_params.py)

def construct_writer_prompt(writer: models.UserAIWriter, context: Optional[Dict[str, Any]] = None) -> str:
    """Builds the full prompt for the AI writer."""
    # Base instructions could be stored elsewhere (e.g., config or constants)
    # base_instructions = "You are an AI writer participating in a creative writing contest. Generate a text based on the provided context and your personality."
    # base_instructions = BASE_WRITER_INSTRUCTION_PROMPT # REMOVED - Use constant directly
    
    # Combine base instructions, personality, and any dynamic context
    # Use the imported constant directly
    full_prompt = f"{BASE_WRITER_INSTRUCTION_PROMPT}\n\n<PERSONALIDAD>\n{writer.personality_prompt}\n</PERSONALIDAD>\n"
    
    if context:
        # Example: Include contest description if provided
        if 'contest_description' in context and context['contest_description']:
            full_prompt += f"\n<CONCURSO>\nDescription:\n{context['contest_description']}\n</CONCURSO>\n"
        # Add other contextual elements as needed
        if 'contest_title' in context:
             full_prompt += f"\nTitle Provided for your text: {context['contest_title']}\n"

    # The prompt asks the model to deliver the text directly.
    # full_prompt += "\nGenerate your creative text now:"
    return full_prompt

def construct_judge_prompt(
    judge: models.UserAIJudge, 
    contest: models.Contest, 
    submissions: List[models.Submission],
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Builds the full prompt for the AI judge."""

    #full_prompt = f"{base_instructions}\n\nYour Judging Personality:\n{judge.personality_prompt}\n"
    #full_prompt += f"\nContest Title: {contest.title}\nContest Description:\n{contest.description}\n"
    # Use the imported constant directly
    full_prompt = f"{BASE_JUDGE_INSTRUCTION_PROMPT}\n\n<PERSONALIDAD>\n{judge.personality_prompt}\n</PERSONALIDAD>\n"
    full_prompt += f"\n<CONCURSO>\nTitle: {contest.title}\nDescription:\n{contest.description}\n</CONCURSO>\n"

    full_prompt += "\n<TEXTOS_A_EVALUAR>\n"
    for sub in submissions:
        # Include Title and Text, but NOT author information for anonymity
        full_prompt += f"---\\nSubmission ID: {sub.id}\\nTitle: {sub.title}\\nText:\\n{sub.text_content}\\n---\\n"
        full_prompt += f"---\nSubmission ID: {sub.id}\nTitle: {sub.title}\nText:\n{sub.text_content}\n---\n"
        
    full_prompt += "</TEXTOS_A_EVALUAR>\n"
        
    if context:
        # Add other contextual elements if needed
        pass

    #full_prompt += "\nPlease provide your evaluation in the specified format above."
    # Prompt already asks for the evaluation based on the format description
    # full_prompt += "\nPlease provide your evaluation in the specified format above."
    return full_prompt


# --- Response Parsing ---

def parse_judge_response(response_text: str, submissions: List[models.Submission]) -> List[Dict[str, Any]]:
    """
    Parses the AI judge's response text to extract rankings and comments.
    Uses the format defined in BASE_JUDGE_INSTRUCTION_PROMPT.
    Returns a list of dictionaries, one for each submission:
    [{'submission_id': int, 'place': Optional[int], 'comment': Optional[str]}]
    
    Handles potential parsing errors gracefully.
    """
    results_map = {sub.id: {'submission_id': sub.id, 'place': None, 'comment': None} for sub in submissions}
    submission_ids = {sub.id for sub in submissions}
    # parsed_comments = {} # Replaced by results_map
    # parsed_rankings = {} # {place: submission_id} # Replaced by results_map

    # --- Robust Regex Parsing ---
    try:
        # Extract Ranking block (Handles optional Mencion Honorifica - place 4)
        ranking_block_match = re.search(r"RANKING:(.*?)(?:JUSTIFICACIONES:|\Z)", response_text, re.DOTALL | re.IGNORECASE)
        if ranking_block_match:
            ranking_block = ranking_block_match.group(1).strip()
            ranking_lines = ranking_block.split('\n')
            for line in ranking_lines:
                # Match format like: 1. [ID] - Title OR 4. [ID] - Title (Mencion Honorifica)
                rank_match = re.match(r"^\s*(\d)\.\s*\[?(\d+)\]?\s*-", line.strip())
                if rank_match:
                    place_str, sub_id_str = rank_match.groups()
                    place = int(place_str)
                    sub_id = int(sub_id_str)
                    if sub_id in submission_ids and 1 <= place <= 4:
                        # Only assign place if not already assigned (first match wins)
                        if results_map[sub_id]['place'] is None:
                             results_map[sub_id]['place'] = place
                            
        # Extract Justifications block
        justifications_block_match = re.search(r"JUSTIFICACIONES:(.*?)(?:\Z)", response_text, re.DOTALL | re.IGNORECASE)
        if justifications_block_match:
             justifications_block = justifications_block_match.group(1).strip()
             # Match format like: 1. [Justification text] (potentially multi-line)
             # Use finditer to handle multi-line justifications potentially better
             justification_matches = re.finditer(r"^\s*(\d)\.\s*(.*?)(?=\n\s*\d\.\s*|\Z)", justifications_block, re.MULTILINE | re.DOTALL | re.IGNORECASE)
             found_places_in_justification = set()
             for match in justification_matches:
                 place_str, justification_text = match.groups()
                 place = int(place_str)
                 # Find which submission ID corresponds to this place from the ranking block
                 corresponding_sub_id = None
                 for sub_id, data in results_map.items():
                     if data['place'] == place:
                         corresponding_sub_id = sub_id
                         break
                 
                 if corresponding_sub_id is not None and place not in found_places_in_justification:
                     # Only assign first justification found for a place
                     comment = justification_text.strip()
                     # Basic validation/cleanup
                     if not isinstance(comment, str):
                         comment = str(comment) # Ensure comment is a string
                     if len(comment) > 1024: # Example length limit
                         comment = comment[:1021] + "..."
                     results_map[corresponding_sub_id]['comment'] = comment
                     found_places_in_justification.add(place)
                     
    except Exception as e:
        print(f"Error parsing judge response with regex: {e}")
        # Fallback or alternative parsing can be added here if needed
        # If parsing fails significantly, results might be empty or partial

    # --- Consolidate Results --- (Convert map to list)
    results = list(results_map.values())
    # for sub_id in submission_ids:
    #     place = None
    #     for p, ranked_id in parsed_rankings.items():
    #         if ranked_id == sub_id:
    #             place = p
    #             break
        
    #     comment = parsed_comments.get(sub_id, None) # Get comment found for this ID

    #     # Basic validation/cleanup
    #     if comment is not None and not isinstance(comment, str):
    #         comment = str(comment) # Ensure comment is a string
    #     if comment is not None and len(comment) > 1024: # Example length limit
    #         comment = comment[:1021] + "..."

    #     results.append({
    #         'submission_id': sub_id,
    #         'place': place,
    #         'comment': comment
    #     })
        
    # Validation: Ensure all submissions have an entry, even if comment/place is None
    # This is handled by initializing results_map with all submission IDs
    # if len(results) != len(submission_ids):
    #     print("Warning: Parsed results count doesn't match submission count.")
    #     # Potentially add missing submission IDs with None values
    #     found_ids = {res['submission_id'] for res in results}
    #     missing_ids = submission_ids - found_ids
    #     for missing_id in missing_ids:
    #          results.append({'submission_id': missing_id, 'place': None, 'comment': None})

    return results


# --- Main Service Functions (Orchestration) ---

async def perform_ai_generation(
    writer: models.UserAIWriter,
    model_id: str,
    db: AsyncSession, # Pass session for potential future needs (e.g., context fetching)
    settings: Settings,
    openai_client: Optional[openai.AsyncOpenAI] = None,
    anthropic_client: Optional[anthropic.AsyncAnthropic] = None,
    generation_context: Optional[Dict[str, Any]] = None # e.g., contest details
) -> Dict[str, Any]:
    """
    Orchestrates AI text generation using a UserAIWriter.
    Does NOT handle credit deduction or CostLedger logging.

    Returns a dictionary including:
    `success`, `generated_text`, `prompt_tokens`, `completion_tokens`, `monetary_cost`, `error`
    """
    model_config = get_model_config(model_id, settings)
    if not model_config:
        return {'success': False, 'error': f"Model configuration not found for ID: {model_id}"}
    # if "generate" not in model_config.features: # REMOVED Feature check
    #     return {'success': False, 'error': f"Model {model_id} does not support the 'generate' feature."}

    # 1. Construct Prompt
    # Prepare context for the prompt
    prompt_context = generation_context or {}
    # Example: Add contest info if available in context
    # if contest_object: 
    #    prompt_context['contest_description'] = contest_object.description
    #    prompt_context['contest_title'] = contest_object.title # If writer needs it
    
    prompt = construct_writer_prompt(writer, context=prompt_context)

    # 2. Call LLM API
    api_result = await call_llm_api(
        prompt=prompt,
        model_id=model_id,
        settings=settings,
        openai_client=openai_client,
        anthropic_client=anthropic_client,
        # Adjust max_tokens/temperature for generation if needed
        max_tokens=2000 
    )

    # 3. Format Result
    return {
        'success': api_result['success'],
        'generated_text': api_result.get('response_text'),
        'prompt_tokens': api_result.get('prompt_tokens'),
        'completion_tokens': api_result.get('completion_tokens'),
        'monetary_cost': api_result.get('monetary_cost'),
        'error': api_result.get('error')
    }

async def perform_ai_evaluation(
    judge: models.UserAIJudge,
    contest_id: int,
    model_id: str,
    db: AsyncSession,
    settings: Settings,
    openai_client: Optional[openai.AsyncOpenAI] = None,
    anthropic_client: Optional[anthropic.AsyncAnthropic] = None,
    evaluation_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Orchestrates AI evaluation of contest submissions using a UserAIJudge.
    Fetches data, calls LLM, parses response, and prepares Vote objects (added to session, NOT committed).
    Does NOT handle credit deduction or CostLedger logging.

    Returns a dictionary including:
    `success`, `status_message`, `prompt_tokens`, `completion_tokens`,
    `monetary_cost`, `error`, `parsed_votes` (list of dicts for CostLedger context),
    `db_votes_added` (boolean indicating if Vote objects were added to session)
    """
    model_config = get_model_config(model_id, settings)
    if not model_config:
        return {'success': False, 'error': f"Model configuration not found for ID: {model_id}", 'db_votes_added': False}
    # if "evaluate" not in model_config.features: # REMOVED Feature check
    #      return {'success': False, 'error': f"Model {model_id} does not support the 'evaluate' feature.", 'db_votes_added': False}


    # 1. Fetch Contest and Submissions
    try:
        stmt = select(models.Contest).where(models.Contest.id == contest_id).options(
            selectinload(models.Contest.submissions) # Eager load submissions
        )
        result = await db.execute(stmt)
        contest = result.scalar_one_or_none()

        if not contest:
            return {'success': False, 'error': f"Contest with ID {contest_id} not found.", 'db_votes_added': False}
            
        # Filter submissions? Or assume all submissions in the contest are evaluated?
        submissions = contest.submissions
        if not submissions:
             return {'success': False, 'error': f"No submissions found for Contest {contest_id} to evaluate.", 'db_votes_added': False}

    except Exception as e:
        return {'success': False, 'error': f"Database error fetching contest/submissions: {e}", 'db_votes_added': False}

    # 2. Construct Prompt
    prompt = construct_judge_prompt(judge, contest, submissions, context=evaluation_context)

    # 3. Call LLM API
    api_result = await call_llm_api(
        prompt=prompt,
        model_id=model_id,
        settings=settings,
        openai_client=openai_client,
        anthropic_client=anthropic_client,
        max_tokens=3000 # Allow more tokens for evaluation response
    )

    if not api_result['success']:
        return {
            'success': False,
            'status_message': 'AI evaluation failed.',
            'prompt_tokens': api_result.get('prompt_tokens'),
            'completion_tokens': api_result.get('completion_tokens'),
            'monetary_cost': api_result.get('monetary_cost'),
            'error': api_result.get('error'),
            'parsed_votes': [],
            'db_votes_added': False
        }

    # 4. Parse Response
    response_text = api_result.get('response_text')
    if not response_text:
         return {
             'success': False,
             'status_message': 'AI evaluation failed: Empty response from API.',
             'prompt_tokens': api_result.get('prompt_tokens'),
             'completion_tokens': api_result.get('completion_tokens'),
             'monetary_cost': api_result.get('monetary_cost'),
             'error': 'Empty response from API.',
             'parsed_votes': [],
             'db_votes_added': False
         }
         
    parsed_results = parse_judge_response(response_text, submissions)
    
    # 5. Create Vote objects (add to session, don't commit)
    db_votes_added = False
    try:
        # Check for existing votes from this AI judge for this contest/model combo?
        # For simplicity now, assume we overwrite or add new ones.
        # A more robust approach might delete previous votes from this judge+model for this contest first.
        
        for result_data in parsed_results:
            # Check if submission_id is valid (should be guaranteed by parser logic)
            if result_data['submission_id'] not in {sub.id for sub in submissions}:
                print(f"Warning: Parsed result for unknown submission ID {result_data['submission_id']}. Skipping.")
                continue

            new_vote = models.Vote(
                submission_id=result_data['submission_id'],
                judge_id=judge.owner_id, # *** The VOTE is cast by the OWNER of the AI Judge ***
                place=result_data.get('place'),
                comment=result_data.get('comment'),
                # Consider adding metadata like ai_judge_id=judge.id, ai_model=model_id ?
                # The Vote model currently only links to User (judge_id).
                # We might need to adjust Vote model or store this context elsewhere (e.g., CostLedger)
            )
            db.add(new_vote)
            db_votes_added = True # Mark that we have votes ready to be committed

        # Don't commit here - that happens in the router after credit deduction
        # await db.flush() # Flush to get potential errors early? Optional.
        
        status_message = f"AI evaluation completed. {len(parsed_results)} votes/comments parsed."

    except Exception as e:
        # Don't rollback here, let the router handle rollback for the whole transaction
        print(f"Error creating Vote objects in session: {e}")
        return {
            'success': False,
            'status_message': 'AI evaluation completed, but failed to prepare votes in database session.',
            'prompt_tokens': api_result.get('prompt_tokens'),
            'completion_tokens': api_result.get('completion_tokens'),
            'monetary_cost': api_result.get('monetary_cost'),
            'error': f"Error creating Vote objects: {e}",
            'parsed_votes': parsed_results, # Return parsed data even if DB part failed
            'db_votes_added': False
        }

    # 6. Format Success Result
    return {
        'success': True,
        'status_message': status_message,
        'prompt_tokens': api_result.get('prompt_tokens'),
        'completion_tokens': api_result.get('completion_tokens'),
        'monetary_cost': api_result.get('monetary_cost'),
        'error': None,
        'parsed_votes': parsed_results, # Include parsed data for logging/context
        'db_votes_added': db_votes_added
    } 