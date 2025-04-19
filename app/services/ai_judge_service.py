"""
Service module for AI judges in Duelo de Plumas.

This module provides functionality for:
- Connecting to AI model APIs (OpenAI, Anthropic)
- Formatting prompts and submissions
- Parsing AI responses
- Creating Vote records from AI evaluations
"""

import os
import re
import json
import openai
import anthropic
import tiktoken
from app import db
from app.models import User, Contest, Submission, Vote, AIEvaluation
from app.config.ai_judge_params import AI_MODELS, BASE_INSTRUCTION_PROMPT, API_PRICING, DEFAULT_AI_MODEL

# Initialize API clients
openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
anthropic_client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

def get_model_info(model_id):
    """Get model information by ID."""
    for model in AI_MODELS:
        if model['id'] == model_id:
            return model
    # Default to first model if not found
    return next((m for m in AI_MODELS if m['id'] == DEFAULT_AI_MODEL), AI_MODELS[0])

def format_submissions_text(submissions):
    """Format submissions into a concise text format for the AI prompt."""
    submissions_text = ""
    for sub in submissions:
        submissions_text += f"\n\nTEXTO #{sub.id}: \"{sub.title}\" por {sub.author_name}\n"
        submissions_text += f"{sub.text_content}\n"
        submissions_text += f"--- FIN DEL TEXTO #{sub.id} ---"
    return submissions_text

def count_tokens(text, model_id):
    """Count the number of tokens in a text string for a specific model."""
    model_info = get_model_info(model_id)
    
    if model_info['provider'] == 'openai':
        # OpenAI models use tiktoken
        try:
            encoding = tiktoken.encoding_for_model(model_info['api_name'])
            return len(encoding.encode(text))
        except Exception:
            # Fallback to cl100k_base encoding as a reasonable approximation
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
    elif model_info['provider'] == 'anthropic':
        # Anthropic models - use Claude's tokenizer or approximation
        # For simplicity, we'll use a rough approximation
        # ~4 characters per token on average
        return len(text) // 4
    
    # Fallback for unknown providers
    return len(text) // 4

def construct_prompt(contest, judge, submissions):
    """Construct the full prompt for the AI judge."""
    # Get the base instruction prompt
    instruction_prompt = BASE_INSTRUCTION_PROMPT
    
    # Get the judge's personality prompt
    personality_prompt = judge.ai_personality_prompt or ""
    
    # Combine the prompts with context about the contest
    context = f"CONCURSO: {contest.title}\nDESCRIPCIÓN: {contest.description or 'No hay descripción específica.'}\n"
    submissions_text = format_submissions_text(submissions)
    
    full_prompt = f"{instruction_prompt}\n\n{personality_prompt}\n\n{context}\n\nSUMISIONES:\n{submissions_text}\n\n"
    
    return full_prompt

def calculate_cost(model_info, prompt_tokens, completion_tokens):
    """Calculate the cost of an API call in USD."""
    pricing = API_PRICING.get(model_info['provider'], {}).get(model_info['api_name'], {'input': 0, 'output': 0})
    input_cost = (prompt_tokens / 1000) * pricing['input']
    output_cost = (completion_tokens / 1000) * pricing['output']
    return input_cost + output_cost

def call_ai_api(prompt, model_id):
    """Call the appropriate AI API with the prompt."""
    model_info = get_model_info(model_id)
    
    try:
        if model_info['provider'] == 'openai':
            response = openai_client.chat.completions.create(
                model=model_info['api_name'],
                messages=[{"role": "system", "content": prompt}],
                temperature=0.2
            )
            response_text = response.choices[0].message.content
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            
        elif model_info['provider'] == 'anthropic':
            response = anthropic_client.messages.create(
                model=model_info['api_name'],
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            response_text = response.content[0].text
            # Anthropic doesn't provide token counts directly in the same way
            # Use our count_tokens function as an approximation
            prompt_tokens = count_tokens(prompt, model_id)
            completion_tokens = count_tokens(response_text, model_id)
        else:
            raise ValueError(f"Unsupported AI provider: {model_info['provider']}")
        
        cost = calculate_cost(model_info, prompt_tokens, completion_tokens)
        
        return {
            'response_text': response_text,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'cost': cost,
            'success': True
        }
    except Exception as e:
        print(f"Error calling AI API: {e}")
        return {
            'response_text': f"Error: {str(e)}",
            'prompt_tokens': count_tokens(prompt, model_id),
            'completion_tokens': 0,
            'cost': 0,
            'success': False
        }

def parse_ai_response(response_text, submissions):
    """
    Parse the AI's response to extract rankings and comments.
    Returns a list of tuples (submission_id, place, comment).
    """
    results = []
    
    # Debug print
    print("AI RESPONSE:\n" + response_text)
    
    # Create submission lookup by ID
    submissions_by_id = {str(sub.id): sub for sub in submissions}
    
    # Extract rankings section - make the regex more flexible
    ranking_match = re.search(r'(?:RANKING|CLASIFICACIÓN|RANKING:|CLASIFICACIÓN:)(.*?)(?:JUSTIFICACIONES|JUSTIFICACIÓN|JUSTIFICACIONES:|JUSTIFICACIÓN:|$)', response_text, re.DOTALL | re.IGNORECASE)
    if not ranking_match:
        print("Failed to find RANKING section")
        return []
    
    ranking_section = ranking_match.group(1).strip()
    print("Found ranking section:\n" + ranking_section)
    
    # Extract justifications section - make the regex more flexible
    justifications_match = re.search(r'(?:JUSTIFICACIONES|JUSTIFICACIÓN|JUSTIFICACIONES:|JUSTIFICACIÓN:)(.*?)$', response_text, re.DOTALL | re.IGNORECASE)
    justifications_section = justifications_match.group(1).strip() if justifications_match else ""
    if justifications_section:
        print("Found justifications section")
    
    # Parse rankings - more flexible regex
    ranking_lines = ranking_section.split('\n')
    rankings = {}
    
    for line in ranking_lines:
        line = line.strip()
        if not line:
            continue
            
        # Try to extract place and submission ID - more flexible patterns
        rank_match = re.match(r'(\d+)[\.:\)]?\s*(?:\[?(\d+)\]?|TEXTO\s*(?:#|No\.|Número)?\s*(\d+))', line, re.IGNORECASE)
        if rank_match:
            place = int(rank_match.group(1))
            
            # Try to find submission ID in the line
            submission_id = None
            if rank_match.group(2):
                submission_id = rank_match.group(2)
            elif rank_match.group(3):
                submission_id = rank_match.group(3)
            else:
                # Try to extract ID using a more flexible pattern if the first one failed
                id_match = re.search(r'(?:^|\s|#|No\.|Número)(\d+)(?:\s|$|\.|\)|-|:)', line)
                if id_match:
                    submission_id = id_match.group(1)
            
            print(f"Found ranking: Place {place}, Submission ID {submission_id}")
            
            if submission_id and submission_id in submissions_by_id:
                rankings[place] = submission_id
            else:
                print(f"Warning: Submission ID {submission_id} not found in available submissions")
    
    # Parse justifications
    justifications = {}
    
    # Look for lines starting with a number and period
    current_place = None
    current_justification = []
    
    for line in justifications_section.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        place_match = re.match(r'(\d+)\.', line)
        if place_match:
            # Save previous justification if exists
            if current_place is not None and current_justification:
                justifications[current_place] = ' '.join(current_justification)
                current_justification = []
            
            # Start new justification
            current_place = int(place_match.group(1))
            current_justification.append(line[place_match.end():].strip())
        elif current_place is not None:
            # Continue previous justification
            current_justification.append(line)
    
    # Save the last justification
    if current_place is not None and current_justification:
        justifications[current_place] = ' '.join(current_justification)
    
    # Create result tuples
    for place, submission_id in rankings.items():
        comment = justifications.get(place, "")
        results.append((submission_id, place, comment))
    
    return results

def run_ai_evaluation(contest_id, judge_id):
    """
    Run the AI evaluation process for a contest.
    
    1. Fetch contest, judge, and submission data
    2. Construct the prompt
    3. Call the AI API
    4. Parse the response
    5. Create Vote records
    6. Create AIEvaluation record
    7. Return success/failure info
    """
    try:
        # Get contest, judge, and submissions
        contest = db.session.get(Contest, contest_id)
        judge = db.session.get(User, judge_id)
        
        if not contest or not judge:
            return {
                'success': False,
                'message': "Contest or judge not found"
            }
        
        if judge.judge_type != 'ai':
            return {
                'success': False,
                'message': "The specified judge is not an AI judge"
            }
        
        if contest.status != 'evaluation':
            return {
                'success': False,
                'message': f"Contest is not in evaluation phase (current status: {contest.status})"
            }
        
        submissions = contest.submissions.all()
        if len(submissions) < 1:
            return {
                'success': False,
                'message': "No submissions to evaluate"
            }
        
        # Get the AI model to use
        model_id = judge.ai_model or DEFAULT_AI_MODEL
        
        # Construct prompt
        prompt = construct_prompt(contest, judge, submissions)
        
        # Call AI API
        api_result = call_ai_api(prompt, model_id)
        
        if not api_result['success']:
            return {
                'success': False,
                'message': f"API call failed: {api_result['response_text']}"
            }
        
        # Parse response
        parsed_results = parse_ai_response(api_result['response_text'], submissions)
        
        if not parsed_results:
            return {
                'success': False,
                'message': "Failed to parse AI response or no rankings found"
            }
        
        # Delete any existing votes from this judge for this contest
        Vote.query.filter(
            Vote.judge_id == judge.id,
            Vote.submission.has(contest_id=contest.id)
        ).delete(synchronize_session='fetch')
        
        # Create Vote records
        votes_to_add = []
        for submission_id, place, comment in parsed_results:
            vote = Vote(
                judge_id=judge.id,
                submission_id=int(submission_id),
                place=place,
                comment=comment
            )
            votes_to_add.append(vote)
        
        # Create AIEvaluation record
        evaluation = AIEvaluation(
            contest_id=contest.id,
            judge_id=judge.id,
            ai_model=model_id,
            full_prompt=prompt,
            response_text=api_result['response_text'],
            prompt_tokens=api_result['prompt_tokens'],
            completion_tokens=api_result['completion_tokens'],
            cost=api_result['cost']
        )
        
        # Add to database and commit
        db.session.add_all(votes_to_add)
        db.session.add(evaluation)
        db.session.commit()
        
        # Now check if this evaluation completes the contest
        from app.contest.routes import calculate_contest_results
        contest_completed = calculate_contest_results(contest.id)
        
        return {
            'success': True,
            'message': "AI evaluation completed successfully" + (" and contest has been closed" if contest_completed else ""),
            'cost': api_result['cost'],
            'votes_count': len(votes_to_add),
            'contest_completed': contest_completed
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in run_ai_evaluation: {e}")
        return {
            'success': False,
            'message': f"Error: {str(e)}"
        } 