"""
Asynchronous services for AI Judge and AI Writer functionalities.
"""

import re
import tiktoken
import asyncio
from typing import List, Dict, Any, Tuple
import openai
import anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, Table, Column
from unittest.mock import MagicMock
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Corrected imports - placed at top level
from ... import models, schemas
from ...database import AsyncSession
from ...fastapi_config import settings

# Alias models for clarity within this service
ContestModel = models.Contest
UserModel = models.User
SubmissionModel = models.Submission
VoteModel = models.Vote
AIEvaluationModel = models.AIEvaluation
AIJudgeModel = models.AIJudge
AIWriterModel = models.AIWriter
ContestAIJudgeAssociationModel = models.ContestAIJudgeAssociation
ContestHumanJudgeAssociationModel = models.ContestHumanJudgeAssociation
AIWritingRequestModel = models.AIWritingRequest

# AI Client setup (assuming dependencies.py handles initialization)
from ..dependencies import get_openai_client, get_anthropic_client

# Configuration (assuming models are adapted for SQLAlchemy 2.0 async later)
# from ..models import Contest, Submission, User, AIWriter # Add specific models as needed
from ..config.ai_params import (
    AI_MODELS, 
    API_PRICING, 
    DEFAULT_AI_MODEL_ID, 
    BASE_JUDGE_INSTRUCTION_PROMPT,
    BASE_WRITER_INSTRUCTION_PROMPT
)

# --- Model Imports (Direct Relative Import - Outside Try/Except for Debugging) ---
# from ..models import Contest as ContestModel, User as UserModel, Submission as SubmissionModel, Vote as VoteModel, AIEvaluation as AIEvaluationModel, contest_judges as contest_judges_table
# Contest, User, Submission, Vote, AIEvaluation, contest_judges = (
#     ContestModel, UserModel, SubmissionModel, VoteModel, AIEvaluationModel, contest_judges_table
# )

# --- Model Imports (Attempt at top level) ---
# Attempt to import actual models, set to None on failure
try:
    # from ..models import Contest as ContestModel, User as UserModel, Submission as SubmissionModel, Vote as VoteModel, AIEvaluation as AIEvaluationModel, contest_judges as contest_judges_table # Old relative import
    from ... import models, schemas # Corrected relative import
    from ...database import AsyncSession # Adjust based on actual location
    ContestModel = models.Contest
    UserModel = models.User
    SubmissionModel = models.Submission
    VoteModel = models.Vote
    AIEvaluationModel = models.AIEvaluation
    AIJudgeModel = models.AIJudge # Added
    AIWriterModel = models.AIWriter # Added AIWriter for generate_text
    ContestAIJudgeAssociationModel = models.ContestAIJudgeAssociation
    ContestHumanJudgeAssociationModel = models.ContestHumanJudgeAssociation
    AIWritingRequestModel = models.AIWritingRequest # Added for generate_text
    # contest_human_judges_table = models.contest_human_judges # If needed
    print("Successfully imported backend models at module level.")
except ImportError as e:
    # Corrected path in error message
    print(f"CRITICAL ERROR: Could not import backend models/schemas using relative path (...). Error: {e}. Check structure and execution path.")
    # Re-raise critical error - app cannot function without models
    raise e

# Placeholder structure for models if import fails - RESTORE THIS BLOCK
class PlaceholderModel:
    id: int
    title: str | None = None
    description: str | None = None
    username: str | None = None
    ai_personality_prompt: str | None = None
    text_content: str | None = None
    contest_id: int | None = None
    judge_id: int | None = None 
    submission_id: int | None = None
    place: int | None = None
    comment: str | None = None
    ai_model: str | None = None
    full_prompt: str | None = None
    response_text: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost: float | None = None
    name: str | None = None # Add name for AIJudge placeholder

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# --- Helper Functions --- 

def get_model_info(model_id: str) -> Dict[str, Any]:
    """Get model information by ID from the loaded AI_MODELS list."""
    for model in AI_MODELS:
        if model['id'] == model_id:
            return model
    # Default to the configured default model if the requested one isn't found or available
    default_model = next((m for m in AI_MODELS if m['id'] == DEFAULT_AI_MODEL_ID), None)
    # Fallback to the first available model if the default is also not found
    return default_model or AI_MODELS[0]

def count_tokens(text: str, model_id: str) -> int:
    """Count the number of tokens in a text string for a specific model."""
    model_info = get_model_info(model_id)
    api_name = model_info.get('api_name', DEFAULT_AI_MODEL_ID) # Use api_name field
    
    try:
        # Use api_name which should correspond to tiktoken model names
        encoding = tiktoken.encoding_for_model(api_name) 
        return len(encoding.encode(text))
    except KeyError:
        # If the specific model name isn't recognized by tiktoken, use a common base
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            print(f"Warning: Could not find tiktoken encoding for model {api_name}. Using cl100k_base.")
            return len(encoding.encode(text))
        except KeyError:
            # Fallback to character count approximation if cl100k_base is unavailable
            print("Warning: cl100k_base encoding not found. Falling back to character count.")
            return len(text) // 4
    except Exception as e:
        print(f"Error counting tokens for model {api_name}: {e}. Falling back to character count.")
        # Fallback to 4 characters per token as a last resort for other errors
        return len(text) // 4

def calculate_cost(model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate the cost of an API call in USD based on model and token counts."""
    model_info = get_model_info(model_id)
    provider = model_info.get('provider')
    api_name = model_info.get('api_name')

    if not provider or not api_name:
        print(f"Warning: Could not find provider or api_name for model {model_id}. Cannot calculate cost.")
        return 0.0
        
    pricing_info = API_PRICING.get(provider, {}).get(api_name)
    
    if not pricing_info:
        print(f"Warning: Pricing info not found for model {api_name} from provider {provider}. Cannot calculate cost.")
        return 0.0
        
    input_cost_per_1k = pricing_info.get('input', 0)
    output_cost_per_1k = pricing_info.get('output', 0)
    
    input_cost = (prompt_tokens / 1000) * input_cost_per_1k
    output_cost = (completion_tokens / 1000) * output_cost_per_1k
    return input_cost + output_cost

def format_submissions_text(submissions: List[Any]) -> str:
    """Format submissions (SQLAlchemy Submission objects) into text for AI prompts."""
    submissions_text = ""
    for sub in submissions:
        # Assuming Submission object has id, title, text_content attributes
        # Judges should not see the author's name to avoid bias
        submissions_text += f"\n\nTEXTO #{sub.id}: \"{sub.title}\"\n"
        submissions_text += f"{sub.text_content}\n"
        submissions_text += f"--- FIN DEL TEXTO #{sub.id} ---"
    return submissions_text

def construct_judge_prompt(contest: Any, ai_judge: Any, submissions: List[Any]) -> str:
    """Constructs the prompt for the AI judge using contest, judge config, and submissions."""
    # Use ai_judge.ai_personality_prompt instead of judge.ai_personality_prompt
    personality = getattr(ai_judge, 'ai_personality_prompt', "Standard literary judge personality.")
    
    contest_desc = f"<CONCURSO>\nID: {getattr(contest, 'id', 'N/A')}\nTitulo: {getattr(contest, 'title', 'N/A')}\nDescripcion: {getattr(contest, 'description', 'N/A')}\n</CONCURSO>"
    submissions_text = format_submissions_text(submissions)
    
    # Include base instructions, judge personality, contest info, submissions, and response format
    full_prompt = f"{BASE_JUDGE_INSTRUCTION_PROMPT}\n\n<PERSONALIDAD>\n{personality}\n</PERSONALIDAD>\n\n{contest_desc}\n\n<TEXTOS_A_EVALUAR>\n{submissions_text}\n</TEXTOS_A_EVALUAR>"
    
    return full_prompt

def construct_writer_prompt(contest: Any, ai_writer: Any, title: str) -> str:
    """Construct the full prompt for the AI writer."""
    # Assuming Contest object has title, description
    # Assuming AIWriter object has personality_prompt
    instruction_prompt = BASE_WRITER_INSTRUCTION_PROMPT
    personality_prompt = ai_writer.personality_prompt or ""
    context = f"CONCURSO: {contest.title}\nDESCRIPCIÓN: {contest.description or 'No hay descripción específica.'}\nTÍTULO DEL TEXTO: {title}\n"
    
    full_prompt = f"""
<INSTRUCCIONES>
{instruction_prompt}
</INSTRUCCIONES>

<PERSONALIDAD>
{personality_prompt}
</PERSONALIDAD>

<CONTEXTO_DEL_CONCURSO>
{context}
</CONTEXTO_DEL_CONCURSO>

Por favor, escribe un texto literario para este concurso usando el título proporcionado.
"""
    return full_prompt

def parse_ai_judge_response(response_text: str, submissions: List[Any]) -> List[Tuple[int, int, str]]:
    """
    Parse the AI judge's response to extract rankings and comments.
    Returns a list of tuples (submission_id, place, comment).
    Requires Submission objects to have an 'id' attribute.
    """
    results = []
    print(f"AI Raw Response:\n{response_text[:500]}...") # Log beginning of response
    
    submissions_by_id = {str(sub.id): sub for sub in submissions}
    submission_ids_found = set()

    # 1. Extract Ranking Section
    # Use non-capturing groups (?:...) for keywords, make section headers optional
    ranking_match = re.search(
        r'(?:RANKING|CLASIFICACIÓN|RESULTADOS|RANKING FINAL|CLASIFICACIÓN FINAL)(?:\s*:\s*\n)?(.*?)'
        r'(?:\n\s*\n|JUSTIFICACIONES|JUSTIFICACIÓN|COMENTARIOS|RAZONES|EXPLICACIÓN|$) # Stop words or end of string', 
        response_text, re.DOTALL | re.IGNORECASE
    )
    ranking_section = ranking_match.group(1).strip() if ranking_match else ""
    if not ranking_section:
        # If no clear section, maybe the whole response is the ranking?
        # Be cautious, try to extract from the start if format matches
        print("Warning: Ranking section not clearly identified. Attempting to parse from beginning.")
        ranking_section = response_text # Less reliable
    else:
        print(f"Identified Ranking Section:\n{ranking_section[:200]}...")

    # 2. Extract Justifications Section
    justifications_match = re.search(
        # Start keywords (non-capturing)
        r'(?:\n|\A)(?:JUSTIFICACIONES|JUSTIFICACIÓN|COMENTARIOS|RAZONES|EXPLICACIÓN|RANK\s+\d+:\s*)'
        # Optional colon and newline
        r'(?:\s*:\s*\n)?'
        # Capture the content (non-greedy)
        r'(.*?)'
        # Lookahead for end patterns: blank line, start of another section, or end of string
        r'(?:\n\s*\n|\n\s*(?:RANKING|CLASIFICACIÓN|RESULTADOS)|$)'
        , response_text, re.DOTALL | re.IGNORECASE
    )
    justifications_section = justifications_match.group(1).strip() if justifications_match else ""
    if justifications_section:
        print(f"Identified Justifications Section:\n{justifications_section[:200]}...")
    else:
        print("Warning: Justifications section not clearly identified.")

    # 3. Parse Rankings from Ranking Section
    rankings: Dict[int, str] = {}
    # Flexible regex: number, optional punctuation/space, word 'TEXTO'/'TEXT', optional '#', number
    # Allows for variations like "1. TEXTO #123", "2 TEXTO 456", "3: Text #789", "4) 101"
    rank_pattern = re.compile(r'(?:^|\s)(\d+)[\.:\) ]*\s*(?:\(?(?:TEXTO|TEXT|SUBMISSION)?\s*(?:#|No\.|Número|Number)?\s*(\d+)\)?)', re.IGNORECASE)
    
    for line in ranking_section.split('\n'):
        line = line.strip()
        if not line: continue

        match = rank_pattern.search(line)
        if match:
            try:
                place = int(match.group(1))
                submission_id_str = match.group(2)
                
                if submission_id_str in submissions_by_id:
                    if place not in rankings: # Avoid overwriting if duplicates found
                        rankings[place] = submission_id_str
                        submission_ids_found.add(submission_id_str)
                        print(f"Parsed ranking: Place {place} -> Submission ID {submission_id_str}")
                    else:
                         print(f"Warning: Duplicate place {place} found in ranking section. Keeping first assignment: {rankings[place]}")
                else:
                    print(f"Warning: Submission ID {submission_id_str} from ranking not in contest submissions.")
            except ValueError:
                print(f"Warning: Could not parse place number from ranking line: {line}")
            except IndexError:
                 print(f"Warning: Regex match error on ranking line: {line}")

    # 4. Parse Justifications (Map place to justification text)
    justifications: Dict[int, str] = {}
    # Look for lines starting with a number/place indicator, possibly followed by the text ID
    # Include patterns like "Rank 1:", "Place 2:", etc.
    place_indicator_pattern = re.compile(
        r'^\s*(?:(?:Rank|Place|Puesto|Lugar)\s+)?(\d+)[\.:\) ]+|^(?:Texto|Text|Submission|Justificación)\s*(?:#|No\.)?\s*(\d+)[:\) ]'
        , re.IGNORECASE
    )
    current_place = None
    current_justification_lines = []

    for line in justifications_section.split('\n'):
        line = line.strip()
        if not line: continue

        match = place_indicator_pattern.match(line)
        if match:
            # Save previous justification if any
            if current_place is not None and current_justification_lines:
                justifications[current_place] = ' '.join(current_justification_lines).strip()
                print(f"Stored justification for place {current_place}")
            
            # Determine the new place number
            place_num_str = match.group(1) or match.group(2)
            try:
                current_place = int(place_num_str)
                # Start collecting new justification, removing the indicator part
                remainder = line[match.end():].strip()
                current_justification_lines = [remainder] if remainder else []
            except (ValueError, TypeError):
                print(f"Warning: Could not parse place number from justification line: {line}")
                current_place = None # Reset if parsing fails
                current_justification_lines.append(line) # Append line to previous justification if indicator is invalid

        elif current_place is not None:
            # If line doesn't start with an indicator, append to current justification
            current_justification_lines.append(line)

    # Save the last justification
    if current_place is not None and current_justification_lines:
        justifications[current_place] = ' '.join(current_justification_lines).strip()
        print(f"Stored justification for place {current_place}")

    # 5. Combine results
    for place, submission_id_str in rankings.items():
        comment = justifications.get(place, "") # Get comment or empty string
        try:
            submission_id_int = int(submission_id_str)
            results.append((submission_id_int, place, comment))
        except ValueError:
             print(f"Warning: Could not convert submission ID {submission_id_str} to int.")

    # 6. Handle submissions mentioned in justifications but missed in ranking (less common)
    # This part is complex and might require more sophisticated NLP. 
    # For now, we rely primarily on the RANKING section.
    # We could potentially try to find submission IDs mentioned near place numbers in justifications 
    # if the ranking section failed, but it's prone to errors.

    print(f"Finished parsing. Found {len(results)} ranked submissions.")
    return results

# --- Core Service Functions (Async Stubs) ---

async def call_ai_api(
    prompt: str, 
    model_id: str, 
    temperature: float, 
    openai_client: 'openai.AsyncOpenAI | None', # Use forward reference for typing
    anthropic_client: 'anthropic.AsyncAnthropic | None' # Use forward reference for typing
) -> Dict[str, Any]:
    """
    Call the appropriate AI API asynchronously based on the model provider.

    Args:
        prompt: The prompt string for the AI.
        model_id: The identifier of the AI model to use.
        temperature: The temperature setting for the AI generation.
        openai_client: An initialized async OpenAI client.
        anthropic_client: An initialized async Anthropic client.

    Returns:
        A dictionary containing the API response details or error information.
    """
    model_info = get_model_info(model_id)
    provider = model_info.get('provider')
    api_name = model_info.get('api_name')
    
    response_text = ""
    prompt_tokens = 0
    completion_tokens = 0
    cost = 0.0
    success = False
    error_message = None

    try:
        prompt_tokens = count_tokens(prompt, model_id) # Count tokens before API call

        if provider == 'openai':
            if not openai_client:
                raise ValueError("OpenAI client not available or API key not configured.")
            print(f"Calling OpenAI model: {api_name}")
            response = await openai_client.chat.completions.create(
                model=api_name,
                messages=[{"role": "system", "content": prompt}],
                temperature=temperature
            )
            response_text = response.choices[0].message.content or ""
            # Use usage stats if available, otherwise count tokens
            prompt_tokens = response.usage.prompt_tokens if response.usage else prompt_tokens
            completion_tokens = response.usage.completion_tokens if response.usage else count_tokens(response_text, model_id)
            success = True
            
        elif provider == 'anthropic':
            if not anthropic_client:
                raise ValueError("Anthropic client not available or API key not configured.")
            print(f"Calling Anthropic model (streaming): {api_name}")
            
            # Define Anthropic max output limit and a desired default
            ANTHROPIC_MAX_OUTPUT_TOKENS = 8192 
            desired_output_tokens = 4096 # Default desired output length

            # Ensure desired tokens doesn't exceed the absolute max
            max_output_tokens = min(desired_output_tokens, ANTHROPIC_MAX_OUTPUT_TOKENS)
            
            # Old calculation based on context window - remove/comment out
            # context_window_tokens = model_info.get('max_tokens', 4000) # Get total context window
            # max_output_tokens = min(context_window_tokens // 2, ANTHROPIC_MAX_OUTPUT_TOKENS) # Use half context, capped at max
            
            # Use context manager for streaming
            async with anthropic_client.messages.stream(
                model=api_name,
                max_tokens=max_output_tokens, # Use the calculated max_output_tokens
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature
            ) as stream:
                # Iterate through the stream and build the response text
                async for text_chunk in stream.text_stream:
                    response_text += text_chunk
                
                # After the stream is finished, get the final message object
                # This contains usage information if available
                final_message = await stream.get_final_message()

            # Old non-streaming code:
            # response = await anthropic_client.messages.create(
            #     model=api_name,
            #     max_tokens=max_output_tokens, 
            #     messages=[
            #         {"role": "user", "content": prompt}
            #     ],
            #     temperature=temperature
            # )
            # response_text = response.content[0].text if response.content else ""
            
            # Initialize completion_tokens before try block
            completion_tokens = 0 
            try:
                # Attempt to get tokens directly from usage of the final message
                if final_message and hasattr(final_message, 'usage') and final_message.usage:
                    usage_tokens = final_message.usage.output_tokens # Assign to temp var
                    # Fallback if API returns None for the value
                    if usage_tokens is None:
                         print("Anthropic returned None for output_tokens in final message, using fallback.")
                         completion_tokens = count_tokens(response_text, model_id)
                    else:
                         completion_tokens = usage_tokens # Assign the valid integer
                else:
                     print("Anthropic final message or usage info not available, using tiktoken count for completion tokens.")
                     completion_tokens = count_tokens(response_text, model_id)
                 
            except (AttributeError, TypeError) as usage_error:
                # Fallback if usage object or attribute doesn't exist
                print(f"Anthropic usage info error ({usage_error}), using tiktoken count for completion tokens as fallback.")
                completion_tokens = count_tokens(response_text, model_id)
                
            success = True
            
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
        
        cost = calculate_cost(model_id, prompt_tokens, completion_tokens)
        
    except Exception as e:
        print(f"Error calling AI API for model {model_id}: {e}")
        # Ensure prompt_tokens is calculated even on error for potential cost estimation
        if prompt_tokens == 0:
             try:
                 prompt_tokens = count_tokens(prompt, model_id)
             except Exception as count_e:
                 print(f"Error counting tokens during exception handling: {count_e}")
        error_message = str(e)
        success = False
        response_text = f"Error: {error_message}"
        completion_tokens = 0
        # Calculate potential cost based on input tokens if possible
        cost = calculate_cost(model_id, prompt_tokens, 0) 

    return {
        'response_text': response_text,
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
        'cost': cost,
        'success': success,
        'error_message': error_message # Include error message for better debugging
    }

async def run_ai_evaluation(
    contest_id: int, 
    ai_judge_id: int, # Changed from judge_id
    admin_user_id: int, # Added ID of user triggering evaluation
    session: AsyncSession,
    openai_client: openai.AsyncOpenAI | None,
    anthropic_client: anthropic.AsyncAnthropic | None,
    temperature: float = 0.2 # Default temperature for judging
) -> Dict[str, Any]:
    """
    Run an AI evaluation for a contest using the specified AI Judge config asynchronously.
    Args:
        contest_id: ID of the contest.
        ai_judge_id: ID of the AIJudge configuration.
        admin_user_id: ID of the User triggering the evaluation (for logging/Vote foreign key).
        session: The asynchronous database session.
        openai_client: Initialized async OpenAI client.
        anthropic_client: Initialized async Anthropic client.
        temperature: The temperature for the AI model call.
    Returns:
        A dictionary containing the status, message, cost, and potentially other details.
    """
    
    # Use module-level models if imported, otherwise use placeholders
    current_Contest = ContestModel if ContestModel else PlaceholderModel
    current_User = UserModel if UserModel else PlaceholderModel # Still needed for admin_user
    current_Submission = SubmissionModel if SubmissionModel else PlaceholderModel
    current_Vote = VoteModel if VoteModel else PlaceholderModel
    current_AIEvaluation = AIEvaluationModel if AIEvaluationModel else PlaceholderModel
    current_AIJudge = AIJudgeModel if AIJudgeModel else PlaceholderModel # Use new AIJudge
    # current_contest_ai_judges = contest_ai_judges_table # REMOVED - Using ContestAIJudgeAssociationModel directly

    # Simplified model check
    if not all([current_Contest, current_User, current_Submission, current_Vote, current_AIEvaluation, current_AIJudge]):
         return {
             'success': False,
             'message': "Error: Critical model class definitions are missing.",
             'cost': 0.0, 'evaluation_id': None, 'votes_created': 0, 'is_reevaluation': False
         }
    # Use the model alias directly now
    if ContestAIJudgeAssociationModel is None: 
        return {'success': False, 'message': "Error: ContestAIJudgeAssociation model definition missing."}

    try:
        # Get contest and AI Judge config
        contest = await session.get(current_Contest, contest_id)
        ai_judge_config = await session.get(current_AIJudge, ai_judge_id)
        # Verify admin user exists (optional sanity check)
        admin_user = await session.get(current_User, admin_user_id)
        
        if not contest or not ai_judge_config or not admin_user:
             missing = []
             if not contest: missing.append(f"Contest ID {contest_id}")
             if not ai_judge_config: missing.append(f"AI Judge Config ID {ai_judge_id}")
             if not admin_user: missing.append(f"Admin User ID {admin_user_id}")
             return {
                 'success': False, 
                 'message': f"Not found: {', '.join(missing)}.",
                 'cost': 0.0, 'evaluation_id': None, 'votes_created': 0, 'is_reevaluation': False
             }
        
        # Check if the AI judge config is assigned to this contest and get the model
        try:
            # Use the Model class directly, access columns without .c
            stmt = select(ContestAIJudgeAssociationModel.ai_model).where(
                ContestAIJudgeAssociationModel.contest_id == contest_id,
                ContestAIJudgeAssociationModel.ai_judge_id == ai_judge_id
            )
            judge_assignment_result = await session.execute(stmt)
            judge_assignment = judge_assignment_result.first()
        except Exception as table_error:
             print(f"Error querying contest_ai_judges table: {table_error}")
             return {
                'success': False, 
                'message': f"Database error checking AI judge assignment: {table_error}",
                'cost': 0.0, 'evaluation_id': None, 'votes_created': 0, 'is_reevaluation': False
            }

        if not judge_assignment:
             return {
                 'success': False, 
                 'message': f"AI Judge '{getattr(ai_judge_config, 'name', ai_judge_id)}' is not assigned to this contest.",
                 'cost': 0.0, 'evaluation_id': None, 'votes_created': 0, 'is_reevaluation': False
             }
             
        ai_model_id = judge_assignment.ai_model
        # No need to check ai_model_id nullability, table constraint enforces it
        
        # Get submissions for this contest
        sub_stmt = select(current_Submission).where(current_Submission.contest_id == contest_id)
        submissions_result = await session.scalars(sub_stmt)
        submissions = submissions_result.all()
        
        if not submissions:
            return {
                'success': False, 
                'message': f"No submissions found for contest ID {contest_id}.",
                 'cost': 0.0, 'evaluation_id': None, 'votes_created': 0, 'is_reevaluation': False
            }
        
        # Check for existing evaluation to avoid duplicates / handle re-evaluation
        is_reevaluation = False
        eval_stmt = select(current_AIEvaluation).where(
            current_AIEvaluation.contest_id == contest_id,
            current_AIEvaluation.judge_id == admin_user_id, # Check against triggering user
            current_AIEvaluation.ai_model == ai_model_id # Might want to check model too?
        )
        existing_evaluation_result = await session.scalars(eval_stmt)
        existing_evaluation = existing_evaluation_result.first()
        
        if existing_evaluation:
            print(f"Existing evaluation found for user {admin_user_id} triggering AI judge {ai_judge_id} in contest {contest_id}. Deleting previous votes and evaluation.")
            # Delete previous votes by this *user* for this contest
            sub_ids_stmt = select(current_Submission.id).where(current_Submission.contest_id == contest_id)
            await session.execute(
                delete(current_Vote)
                .where(current_Vote.judge_id == admin_user_id)
                .where(current_Vote.submission_id.in_(sub_ids_stmt))
            )
            await session.delete(existing_evaluation)
            await session.flush()
            is_reevaluation = True
        
        # Construct the prompt using the AI Judge config
        prompt = construct_judge_prompt(contest, ai_judge_config, submissions)
        
        # Call the AI API using helper
        api_result = await call_ai_api(
            prompt=prompt, 
            model_id=ai_model_id, 
            temperature=temperature, 
            openai_client=openai_client, 
            anthropic_client=anthropic_client
        )
        
        if not api_result['success']:
            await session.rollback() 
            return {
                'success': False, 
                'message': f"Error calling AI API: {api_result['error_message']}",
                'cost': api_result['cost'], 
                'evaluation_id': None, 'votes_created': 0, 'is_reevaluation': is_reevaluation 
            }
        
        # Parse the response using helper
        parsed_results = parse_ai_judge_response(api_result['response_text'], submissions)
        
        # Create an AIEvaluation record - linking to the admin user ID
        evaluation = current_AIEvaluation(
            contest_id=contest_id,
            judge_id=admin_user_id, # FK to User table (triggering user)
            # ai_judge_config_id=ai_judge_id, # Optional: Add if schema changes later
            ai_model=ai_model_id,
            full_prompt=prompt[:20000], 
            response_text=api_result['response_text'][:20000],
            prompt_tokens=api_result['prompt_tokens'],
            completion_tokens=api_result['completion_tokens'],
            cost=api_result['cost']
        )
        session.add(evaluation)
        await session.flush() 
        evaluation_id = evaluation.id
        
        # Create Vote records - linking to the admin user ID
        votes_created = 0
        rankings_dict = {}
        comments_dict = {}
        submission_ids_in_contest = {sub.id for sub in submissions}
        
        for submission_id, place, comment in parsed_results:
            if submission_id not in submission_ids_in_contest:
                print(f"Warning: Parsed submission ID {submission_id} not found in current contest submissions. Skipping vote.")
                continue
            
            # Create Vote object linked to admin user
            vote = current_Vote(
                judge_id=admin_user_id, 
                submission_id=submission_id,
                place=place,
                comment=comment[:5000] 
            )
            session.add(vote)
            votes_created += 1
            
            # Populate response dictionaries (remains the same)
            rankings_dict[str(submission_id)] = place 
            if comment: comments_dict[str(submission_id)] = comment 
        
        await session.commit()
        
        # Update the return dictionary to include all fields required by the schema
        return {
            'success': True,
            'message': f"AI evaluation completed successfully. Created {votes_created} vote records.",
            'evaluation_id': evaluation_id,
            'judge_id': admin_user_id, # Return triggering user ID
            'contest_id': contest_id,
            'rankings': rankings_dict,
            'comments': comments_dict,
            # Optional internal details (not part of AIEvaluationResult schema)
            'cost': api_result['cost'], 
            'votes_created': votes_created,
            'is_reevaluation': is_reevaluation
        }
    
    except Exception as e:
        await session.rollback()
        print(f"Error during AI evaluation execution: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': f"An unexpected error occurred during AI evaluation: {str(e)}",
            'cost': 0.0,
            'evaluation_id': None,
            'votes_created': 0,
            'is_reevaluation': False
        }

# --- AI Writer Service ---

async def generate_text(
    session: AsyncSession,
    contest_id: int,
    ai_writer_id: int,
    model_id: str,
    title: str,
    openai_client: openai.AsyncOpenAI | None = None,
    anthropic_client: anthropic.AsyncAnthropic | None = None,
) -> dict:
    """
    Generate a text using an AI writer and submit it to a contest (Async version).
    Uses models imported at the module level.
    """
    # Models (ContestModel, AIWriterModel, SubmissionModel, AIWritingRequestModel)
    # and APP_VERSION should be available from module-level imports.
    # No local imports needed here anymore.

    # --- Helper Functions ---

    try:
        # Get the contest and AI writer asynchronously using locally imported models
        contest_result = await session.execute(select(ContestModel).where(ContestModel.id == contest_id))
        contest = contest_result.scalar_one_or_none()

        ai_writer_result = await session.execute(select(AIWriterModel).where(AIWriterModel.id == ai_writer_id))
        ai_writer = ai_writer_result.scalar_one_or_none()

        if not contest:
            return {"success": False, "message": f"Contest with ID {contest_id} not found"}
        
        if not ai_writer:
            return {"success": False, "message": f"AI Writer with ID {ai_writer_id} not found"}
        
        # Check if contest is open (Assuming 'status' attribute exists)
        if not hasattr(contest, 'status') or contest.status != 'open':
            return {"success": False, "message": "Contest is not open for submissions"}
        
        # Construct the prompt (using the existing synchronous helper for now)
        # TODO: Consider making construct_writer_prompt async if it involves I/O
        prompt = construct_writer_prompt(contest, ai_writer, title)
        
        # Call the AI API asynchronously
        # Use a default temperature suitable for creative writing if not specified
        creative_temperature = 0.7 
        api_result = await call_ai_api(
            prompt=prompt, 
            model_id=model_id, 
            temperature=creative_temperature,
            openai_client=openai_client,
            anthropic_client=anthropic_client
        )
        
        if not api_result['success']:
            # Log the underlying error if possible
            print(f"AI API call failed for contest {contest_id}, writer {ai_writer_id}: {api_result.get('error_message', api_result['response_text'])}")
            return {"success": False, "message": f"Error calling AI API: {api_result['response_text']}"}
        
        # Create a submission
        # Use a helper to get current timestamp if needed, e.g., datetime.utcnow()
        from datetime import datetime # Add import if not present at top
        submission = SubmissionModel(
            author_name=f"{ai_writer.name} (IA)", # Assuming 'name' attribute exists
            title=title,
            text_content=api_result['response_text'],
            contest_id=contest.id,
            is_ai_generated=True,
            ai_writer_id=ai_writer.id,
            submission_date = datetime.utcnow() # Add submission date
        )
        
        session.add(submission)
        await session.flush() # Flush here to get submission ID for the request log

        if submission.id is None:
             # This shouldn't happen if flush is successful, but good to check
             await session.rollback()
             print(f"Error: Failed to get submission ID after flush for contest {contest_id}")
             return {"success": False, "message": "Failed to create submission record."}
             
        # Record the AI writing request
        writing_request = AIWritingRequestModel(
            contest_id=contest.id,
            ai_writer_id=ai_writer.id,
            ai_model=model_id, # Use the requested model_id
            full_prompt=prompt,
            response_text=api_result['response_text'],
            prompt_tokens=api_result.get('prompt_tokens'), # Use .get for safety
            completion_tokens=api_result.get('completion_tokens'),
            cost=api_result.get('cost'),
            timestamp=submission.submission_date, # Use submission timestamp
            # Use the imported settings object for APP_VERSION
            app_version=settings.APP_VERSION,
            submission_id=submission.id # Link the submission
        )
        
        session.add(writing_request)
        
        await session.commit()
        
        return {
            "success": True, 
            "message": f"Text generated and submitted successfully",
            "submission_id": submission.id,
            "text": api_result['response_text']
        }
        
    except Exception as e:
        await session.rollback()
        # Log the exception for debugging
        print(f"Error generating text for contest {contest_id}, writer {ai_writer_id}: {e}")
        import traceback
        traceback.print_exc() 
        return {"success": False, "message": f"An unexpected error occurred: {str(e)}"}

# Placeholder for the old function signature (if any) - remove if not needed
# async def generate_text(): # Placeholder - REMOVE THIS LINE
#    pass # REMOVE THIS LINE 