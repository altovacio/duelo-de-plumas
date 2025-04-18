import os
import json
from datetime import datetime, timezone
from app import db
from app.models import Contest, Submission, User, Vote, AIEvaluationRun
# We'll need specific API client libraries later, e.g.:
# from openai import OpenAI
# from anthropic import Anthropic
# from google.generativeai import GenerativeModel

# Import specific API client libraries and exceptions
from openai import OpenAI, APIError as OpenAI_APIError, RateLimitError as OpenAI_RateLimitError
from anthropic import Anthropic, APIError as Anthropic_APIError, RateLimitError as Anthropic_RateLimitError
import logging # Use logging for better error reporting

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'ai_model_costs.json')
_MODEL_COSTS = None

def get_model_costs():
    """Loads model cost information from the JSON config file."""
    global _MODEL_COSTS
    if _MODEL_COSTS is None:
        try:
            with open(CONFIG_PATH, 'r') as f:
                all_models = json.load(f)
                # Create a dictionary keyed by model ID for quick lookup
                _MODEL_COSTS = {model['id']: model for model in all_models}
                logging.info(f"Successfully loaded cost data for {len(_MODEL_COSTS)} models.")
        except FileNotFoundError:
            logging.error(f"Error: AI model cost file not found at {CONFIG_PATH}")
            _MODEL_COSTS = {}
        except json.JSONDecodeError:
            logging.error(f"Error: Could not decode JSON from {CONFIG_PATH}")
            _MODEL_COSTS = {}
        except Exception as e:
            logging.exception(f"An unexpected error occurred loading model costs: {e}")
            _MODEL_COSTS = {}
    return _MODEL_COSTS

def build_evaluation_prompt(contest, submissions, judge):
    """Constructs the full prompt for the AI judge."""
    logging.info(f"Building prompt for Contest {contest.id} judged by {judge.username} ({judge.ai_model_id})...")
    # --- 1. Fixed Instruction Prompt --- (Using triple-quoted f-string)
    # Example JSON needs double quotes internally, escaped or handled carefully.
    example_json_3 = '''
        { "rankings": [ { "submission_id": 101, "place": 1, "justification": "Excellent use of imagery." }, { "submission_id": 103, "place": 2, "justification": "Compelling narrative arc." }, { "submission_id": 102, "place": 3, "justification": "Strong character voice." } ] }
    '''
    example_json_4_hm = '''
        { "rankings": [ { "submission_id": 101, "place": 1, "justification": "..." }, { "submission_id": 104, "place": 2, "justification": "..." }, { "submission_id": 102, "place": 3, "justification": "..." }, { "submission_id": 103, "place": 4, "justification": "Unique concept, deserves mention." } ] }
    '''

    instruction_prompt = f'''You are a literary judge tasked with evaluating submissions for a writing contest. 
Read the contest description and all the submissions provided below.

Instructions:
1. Rank the submissions: Assign 1st place, 2nd place, and 3rd place. 
You MUST assign exactly one of each if there are 3 or more submissions. 
If there are fewer than 3 submissions, assign ranks accordingly (e.g., only 1st and 2nd if 2 submissions).
2. Honorable Mentions (Optional): If a submission is outstanding but doesn't make the top 3, you may assign it an Honorable Mention (HM). You can assign multiple HMs.
3. Justification: Provide a brief (1-2 sentence) justification for EACH placement (1st, 2nd, 3rd, and any HMs). Do not provide justifications for unranked submissions.
4. Format: Respond ONLY with a JSON object. The JSON object should have a single key 'rankings'. The value should be a list of objects, where each object represents a ranked submission and contains the following keys: 'submission_id' (integer), 'place' (integer, 1=1st, 2=2nd, 3=3rd, 4=HM), and 'justification' (string).

Example for 3 submissions:
{example_json_3}
Example for 4 submissions with one HM:
{example_json_4_hm}
'''
    # --- 2. Personality Prompt --- 
    personality_prompt = judge.ai_personality_prompt or "Evaluate based on general literary merit, creativity, style, and adherence to the theme."
    
    # --- 3. Contest Information --- 
    contest_info = f"\n--- CONTEST DETAILS ---\nTitle: {contest.title}\nDescription: {contest.description}\n"
    
    # --- 4. Submissions --- 
    submissions_text = "\n--- SUBMISSIONS ---\n"
    for sub in submissions:
        submissions_text += f"\nSubmission ID: {sub.id}\nTitle: {sub.title}\nText:\n{sub.text_content}\n---\n"

    # --- Combine --- 
    full_prompt = f"{instruction_prompt}\n--- JUDGE PERSONALITY ---\n{personality_prompt}{contest_info}{submissions_text}\n--- END SUBMISSIONS ---\n\nProvide your evaluation in the specified JSON format only."

    # TODO: Add token counting / truncation logic if necessary based on model limits
    # print(f"Prompt Length (chars): {len(full_prompt)}") # Basic check
    return full_prompt

def call_ai_api(prompt, model_id):
    """Connects to the appropriate AI API and gets the evaluation."""
    logging.info(f"Attempting AI API call for model: {model_id}")
    
    model_costs = get_model_costs()
    model_info = model_costs.get(model_id)

    if not model_info:
        logging.error(f"Model info not found for ID: {model_id}")
        return {"success": False, "error": f"Configuration missing for model {model_id}."}

    provider = model_info.get('provider')
    api_key = None
    response_data = {"success": False}

    try:
        if provider == "OpenAI":
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set.")
            
            client = OpenAI(api_key=api_key)
            logging.info(f"Calling OpenAI model: {model_id}")
            
            # Determine if the model supports JSON mode
            supports_json_mode = model_id in ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo-0125"] # Add others if needed
            response_format_arg = {"type": "json_object"} if supports_json_mode else None
            
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    # Consider splitting prompt into system/user roles if beneficial
                    # {"role": "system", "content": "You are a literary judge..."},
                    {"role": "user", "content": prompt}
                ],
                # max_tokens can be useful, but let's rely on model defaults for now
                response_format=response_format_arg 
            )
            
            response_data["success"] = True
            response_data["response_text"] = response.choices[0].message.content
            response_data["prompt_tokens"] = response.usage.prompt_tokens
            response_data["completion_tokens"] = response.usage.completion_tokens
            logging.info(f"OpenAI call successful for {model_id}. Tokens: P={response.usage.prompt_tokens}, C={response.usage.completion_tokens}")

        elif provider == "Anthropic":
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
            
            client = Anthropic(api_key=api_key)
            logging.info(f"Calling Anthropic model: {model_id}")
            
            # Anthropic requires max_tokens
            # Let's set a generous default, e.g., 4096, could be made configurable
            max_tokens_to_sample = 4096 
            
            response = client.messages.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens_to_sample
            )

            response_data["success"] = True
            # Assuming the response is in response.content[0].text
            if response.content and len(response.content) > 0:
                 response_data["response_text"] = response.content[0].text
            else:
                 response_data["response_text"] = "" # Handle empty content case
            response_data["prompt_tokens"] = response.usage.input_tokens
            response_data["completion_tokens"] = response.usage.output_tokens
            logging.info(f"Anthropic call successful for {model_id}. Tokens: P={response.usage.input_tokens}, C={response.usage.output_tokens}")
            
        else:
            logging.warning(f"API integration not implemented for provider: {provider} (Model: {model_id})")
            response_data["error"] = f"API integration for provider {provider} not implemented."

    except ValueError as ve:
        logging.error(f"Configuration error for {provider}: {ve}")
        response_data["error"] = str(ve)
    except (OpenAI_APIError, Anthropic_APIError) as api_err:
        logging.error(f"{provider} API Error for model {model_id}: {api_err}")
        response_data["error"] = f"{provider} API Error: {api_err}"
    except (OpenAI_RateLimitError, Anthropic_RateLimitError) as rate_limit_err:
        logging.error(f"{provider} Rate Limit Error for model {model_id}: {rate_limit_err}")
        response_data["error"] = f"{provider} Rate Limit Error: {rate_limit_err}"
    except Exception as e:
        logging.exception(f"Unexpected error calling {provider} API for model {model_id}: {e}")
        response_data["error"] = f"Unexpected {provider} API error: {e}"
        
    return response_data

def parse_ai_response(response_text):
    """Parses the JSON response from the AI."""
    logging.info("Parsing AI response...")
    # Clean potential markdown ```json ... ``` wrapper if present
    if response_text.strip().startswith("```json"):
        response_text = response_text.strip()[7:-3].strip()
    elif response_text.strip().startswith("```"):
         response_text = response_text.strip()[3:-3].strip()

    try:
        data = json.loads(response_text)
        if 'rankings' not in data or not isinstance(data['rankings'], list):
            logging.error("AI response JSON missing 'rankings' list or is not a list.")
            return None
        # TODO: Add more robust validation for submission_id, place, justification types/values
        valid_rankings = []
        for item in data['rankings']:
            if isinstance(item.get('submission_id'), int) and \
               isinstance(item.get('place'), int) and item.get('place') > 0 and \
               isinstance(item.get('justification'), str):
                valid_rankings.append(item)
            else:
                logging.warning(f"Skipping invalid ranking item in AI response: {item}")
        
        logging.info(f"Successfully parsed {len(valid_rankings)} valid rankings.")
        return valid_rankings
    except json.JSONDecodeError:
        logging.error(f"Failed to decode AI response as JSON: {response_text[:300]}...")
        return None
    except Exception as e:
        logging.exception(f"Error parsing AI response: {e}")
        return None

def calculate_cost(model_id, prompt_tokens, completion_tokens):
    """Calculates the cost of the API call."""
    costs = get_model_costs()
    model_info = costs.get(model_id)
    
    if not model_info:
        logging.warning(f"Cost information not found for model {model_id}. Cannot calculate cost.")
        return None
        
    if prompt_tokens is None or completion_tokens is None:
        # Allow cost calculation even if tokens are zero (e.g., free models might return 0)
        logging.warning(f"Token counts missing or zero for model {model_id}. Cost might be inaccurate or zero.")
        prompt_tokens = prompt_tokens or 0
        completion_tokens = completion_tokens or 0
        
    input_cost = (prompt_tokens / 1000) * model_info.get('input_cost_usd_per_1k_tokens', 0)
    output_cost = (completion_tokens / 1000) * model_info.get('output_cost_usd_per_1k_tokens', 0)
    total_cost = input_cost + output_cost
    logging.info(f"Calculated cost for {model_id}: ${total_cost:.6f} (Input: {input_cost:.6f}, Output: {output_cost:.6f})")
    return total_cost

def save_ai_evaluation(run_record, rankings):
    """Saves the parsed AI evaluation results (rankings) to the Vote table."""
    logging.info(f"Saving AI evaluation results for Run ID {run_record.id}...")
    
    submissions_in_contest = {sub.id: sub for sub in run_record.contest.submissions}
    # Get existing votes for this judge/contest to update/delete later
    existing_votes = Vote.query.filter_by(judge_id=run_record.judge_id, contest_id=run_record.contest_id).all()
    existing_votes_map = {v.submission_id: v for v in existing_votes}
    
    processed_submission_ids = set()
    saved_count = 0
    
    for rank_info in rankings:
        submission_id = rank_info.get('submission_id')
        place = rank_info.get('place')
        justification = rank_info.get('justification', '').strip()
        
        if not isinstance(submission_id, int) or submission_id not in submissions_in_contest:
            logging.warning(f"Invalid or unknown submission_id {submission_id} in AI ranking. Skipping.")
            continue
            
        if not isinstance(place, int) or place < 1:
            logging.warning(f"Invalid place {place} for submission {submission_id}. Skipping.")
            continue
            
        processed_submission_ids.add(submission_id)
            
        # Create or update vote
        vote = existing_votes_map.get(submission_id)
        if not vote:
            vote = Vote(judge_id=run_record.judge_id, submission_id=submission_id, contest_id=run_record.contest_id)
            db.session.add(vote)
            
        vote.place = place
        vote.comment = justification # Store justification in the comment field
        vote.timestamp = datetime.now(timezone.utc)
        saved_count += 1
        
    # Handle submissions that were previously ranked but are no longer ranked by the AI
    # Set their place to None or delete the Vote record?
    # Let's set place=None and clear comment for now.
    deleted_count = 0
    for sub_id, vote in existing_votes_map.items():
        if sub_id not in processed_submission_ids:
            logging.info(f"Clearing previous ranking for submission {sub_id} by judge {run_record.judge_id} in contest {run_record.contest_id}.")
            vote.place = None
            vote.comment = None # Or keep old comment? Clearing seems cleaner.
            vote.timestamp = datetime.now(timezone.utc)
            # Alternatively, delete: db.session.delete(vote); deleted_count += 1
            
    try:
        db.session.commit()
        logging.info(f"Successfully saved/updated {saved_count} Vote records and cleared {len(existing_votes_map) - saved_count} previous ranks from AI evaluation.")
        return True
    except Exception as e:
        db.session.rollback()
        logging.exception(f"Error saving AI evaluation votes to database: {e}")
        return False
        
def run_ai_judge_evaluation(contest_id, judge_id):
    """Main function to orchestrate the AI evaluation process."""
    logging.info(f"--- Starting AI Evaluation for Contest ID: {contest_id}, Judge ID: {judge_id} ---")
    
    judge = db.session.get(User, judge_id)
    contest = db.session.get(Contest, contest_id)
    
    if not judge or not judge.is_ai_judge():
        logging.error(f"Judge {judge_id} not found or is not an AI judge.")
        return False
        
    if not contest:
        logging.error(f"Contest {contest_id} not found.")
        return False

    if not judge.ai_model_id:
        logging.error(f"AI Judge {judge_id} does not have an AI model configured.")
        return False
        
    submissions = contest.submissions.all()
    if not submissions:
        logging.warning(f"Contest {contest_id} has no submissions. Skipping AI evaluation.")
        # Create a run record indicating skipped with 0 cost?
        run_record = AIEvaluationRun.query.filter_by(contest_id=contest_id, judge_id=judge_id).first()
        if not run_record:
            run_record = AIEvaluationRun(contest_id=contest_id, judge_id=judge_id)
            db.session.add(run_record)
        run_record.ai_model_used = judge.ai_model_id
        run_record.status = 'completed' # Mark as completed, but with 0 cost/tokens
        run_record.run_timestamp = datetime.now(timezone.utc)
        run_record.prompt_tokens = 0
        run_record.completion_tokens = 0
        run_record.total_cost = 0
        run_record.full_prompt_sent = "No submissions."
        run_record.raw_ai_response = "No submissions."
        try:
            db.session.commit()
            logging.info(f"Marked AIEvaluationRun for Contest {contest_id}, Judge {judge_id} as completed (no submissions).")
            return True # Indicate success, as there was nothing to evaluate
        except Exception as e:
            db.session.rollback()
            logging.exception(f"Error saving skipped AIEvaluationRun record: {e}")
            return False

    # --- 1. Create/Update AIEvaluationRun record --- 
    run_record = AIEvaluationRun.query.filter_by(contest_id=contest_id, judge_id=judge_id).first()
    if not run_record:
        run_record = AIEvaluationRun(contest_id=contest_id, judge_id=judge_id)
        db.session.add(run_record)
    
    run_record.ai_model_used = judge.ai_model_id
    run_record.status = 'running'
    run_record.run_timestamp = datetime.now(timezone.utc)
    run_record.prompt_tokens = None
    run_record.completion_tokens = None
    run_record.total_cost = None
    run_record.full_prompt_sent = None
    run_record.raw_ai_response = None
    
    try:
        db.session.commit()
        logging.info(f"Created/Updated AIEvaluationRun record ID: {run_record.id} with status 'running'.")
    except Exception as e:
        db.session.rollback()
        logging.exception(f"Error saving initial AIEvaluationRun record: {e}")
        return False
        
    # --- 2. Build Prompt --- 
    try:
        full_prompt = build_evaluation_prompt(contest, submissions, judge)
        run_record.full_prompt_sent = full_prompt # Store the prompt
    except Exception as e:
        logging.exception(f"Error building prompt: {e}")
        run_record.status = 'failed'
        db.session.commit() # Commit failure status
        return False
        
    # --- 3. Call AI API --- 
    api_result = call_ai_api(full_prompt, judge.ai_model_id)
    run_record.raw_ai_response = api_result.get('response_text', api_result.get('error')) # Store raw response or error
    
    if not api_result.get('success'):
        logging.error(f"AI API call failed: {api_result.get('error', 'Unknown API error')}")
        run_record.status = 'failed'
        db.session.commit() # Commit failure status
        return False
        
    # Store token counts if available
    run_record.prompt_tokens = api_result.get('prompt_tokens')
    run_record.completion_tokens = api_result.get('completion_tokens')

    # --- 4. Calculate Cost --- 
    run_record.total_cost = calculate_cost(
        run_record.ai_model_used, 
        run_record.prompt_tokens, 
        run_record.completion_tokens
    )
    
    # --- 5. Parse Response --- 
    parsed_rankings = parse_ai_response(api_result['response_text'])
    
    if parsed_rankings is None:
        logging.error("Failed to parse valid rankings from AI response.")
        run_record.status = 'failed'
        db.session.commit() # Commit failure status
        return False
        
    # --- 6. Save Evaluation Results (Votes) --- 
    # Add contest_id to Vote model when saving
    save_success = save_ai_evaluation_with_contest(run_record, parsed_rankings) 
    
    if save_success:
        run_record.status = 'completed'
        logging.info(f"--- AI Evaluation for Contest ID: {contest_id}, Judge ID: {judge_id} Completed Successfully ---")
    else:
        run_record.status = 'failed' # Mark run as failed if votes couldn't be saved
        logging.error(f"--- AI Evaluation for Contest ID: {contest_id}, Judge ID: {judge_id} Failed (DB Save Error) ---")
        
    try:
        db.session.commit() # Commit final status, cost, tokens, etc.
    except Exception as e:
        db.session.rollback()
        logging.exception(f"Error committing final AIEvaluationRun status: {e}")
        return False # Indicate overall failure if final commit fails

    return save_success # Return True only if votes were saved successfully

# Helper function to pass contest_id to save_ai_evaluation if needed
# Refactored save_ai_evaluation to accept run_record which contains contest_id
def save_ai_evaluation_with_contest(run_record, rankings):
    # The contest_id is accessible via run_record.contest_id
    return save_ai_evaluation(run_record, rankings) 