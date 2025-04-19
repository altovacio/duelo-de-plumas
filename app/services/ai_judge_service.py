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
from app.models import User, Contest, Submission, Vote, AIEvaluation, contest_judges
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
        #Judges should not see the author's name to avoid bias
        #submissions_text += f"\n\nTEXTO #{sub.id}: \"{sub.title}\" por {sub.author_name}\n"
        submissions_text += f"\n\nTEXTO #{sub.id}: \"{sub.title}\"\n"
        submissions_text += f"{sub.text_content}\n"
        submissions_text += f"--- FIN DEL TEXTO #{sub.id} ---"
    return submissions_text

def count_tokens(text, model_id):
    """Count the number of tokens in a text string for a specific model."""
    model_info = get_model_info(model_id)
    
    try:
        encoding = tiktoken.encoding_for_model(model_info['api_name'])
        return len(encoding.encode(text))
    except Exception:
        try:
            # Fallback to cl100k_base encoding as a reasonable approximation
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            # Fallback to 4 characters per token as a last resort
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
                max_tokens=2500,
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
    
    # Extract rankings section - make the regex even more flexible
    ranking_match = re.search(r'(?:RANKING|CLASIFICACIÓN|RANKING:|CLASIFICACIÓN:|RANKING FINAL|CLASIFICACIÓN FINAL|RESULTADOS|RESULTADOS:|RANKING FINAL:|CLASIFICACIÓN FINAL:)(.*?)(?:JUSTIFICACIONES|JUSTIFICACIÓN|JUSTIFICACIONES:|JUSTIFICACIÓN:|COMENTARIOS|COMENTARIOS:|$)', response_text, re.DOTALL | re.IGNORECASE)
    if not ranking_match:
        print("Failed to find RANKING section - trying to extract directly from numbered lines")
        # If no explicit ranking section, try to identify lines with rankings directly
        ranking_section = response_text
    else:
        ranking_section = ranking_match.group(1).strip()
        print("Found ranking section:\n" + ranking_section)
    
    # Extract justifications section with more flexible regex
    justifications_match = re.search(r'(?:JUSTIFICACIONES|JUSTIFICACIÓN|JUSTIFICACIONES:|JUSTIFICACIÓN:|COMENTARIOS|COMENTARIOS:|RAZONES|RAZONES:|EXPLICACIÓN|EXPLICACIÓN:)(.*?)$', response_text, re.DOTALL | re.IGNORECASE)
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
            
        # Try multiple patterns to extract place and submission ID
        rank_patterns = [
            # 1. TEXTO #1
            r'(?:^|\s)(\d+)[\.:\)]?\s*(?:\[?(?:TEXTO|TEXTO #|TEXT|SUBMISSION)?\s*(?:#|No\.|Número|Number)?\s*(\d+))', 
            # 2. 1. [123]
            r'(?:^|\s)(\d+)[\.:\)]?\s*\[?(\d+)\]?',
            # 3. First place: Text 123
            r'(?:First|1st|Second|2nd|Third|3rd)(?:\s+place)?:\s*(?:Text|Texto|Submission)?\s*(?:#|No\.)?(\d+)',
            # 4. Any sequence with digit-digit pattern
            r'(?:^|\s|\[)(\d+)[^\d]+(\d+)(?:\s|$|\.|\)|\])'
        ]
        
        place = None
        submission_id = None
        
        for pattern in rank_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # For the special "First/Second/Third place" pattern
                if "First" in pattern or "1st" in pattern:
                    submission_id = match.group(1)
                    if "First" in line or "1st" in line:
                        place = 1
                    elif "Second" in line or "2nd" in line:
                        place = 2
                    elif "Third" in line or "3rd" in line:
                        place = 3
                else:
                    place = int(match.group(1))
                    submission_id = match.group(2)
                
                if place and submission_id:
                    break
        
        if place and submission_id:
            print(f"Found ranking: Place {place}, Submission ID {submission_id}")
            
            if submission_id in submissions_by_id:
                rankings[place] = submission_id
            else:
                print(f"Warning: Submission ID {submission_id} not found in available submissions")
    
    # Parse justifications - more flexible approach
    justifications = {}
    
    # Look for patterns like "1.", "Texto #1:", etc. in justifications section
    current_place = None
    current_justification = []
    
    for line in justifications_section.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Try to match various place indicator patterns
        place_patterns = [
            r'^(\d+)\.',  # Simple "1."
            r'^(?:Texto|Text|Submission)\s*(?:#|No\.|Number)?\s*(\d+):',  # "Text #1:"
            r'^(?:(?:First|1st|Second|2nd|Third|3rd)(?:\s+place)?):',  # "First place:"
            r'^(?:Rank|Ranking|Place)?\s*(?:#|No\.|Number)?\s*(\d+):',  # "Rank #1:"
        ]
        
        for pattern in place_patterns:
            place_match = re.match(pattern, line, re.IGNORECASE)
            if place_match:
                # Save previous justification if exists
                if current_place is not None and current_justification:
                    justifications[current_place] = ' '.join(current_justification)
                    current_justification = []
                
                # Handle special cases for text patterns
                if "First" in pattern or "1st" in pattern:
                    if "First" in line or "1st" in line:
                        current_place = 1
                    elif "Second" in line or "2nd" in line:
                        current_place = 2
                    elif "Third" in line or "3rd" in line:
                        current_place = 3
                else:
                    # For numeric patterns
                    current_place = int(place_match.group(1))
                    
                # Extract text after the place indicator
                remainder = line[place_match.end():].strip()
                if remainder:
                    current_justification.append(remainder)
                    
                break  # Found a match, stop checking patterns
                
        # If no place pattern was found, add line to current justification
        if current_place is not None:
            found_pattern = False
            for pattern in place_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    found_pattern = True
                    break
            
            if not found_pattern:
                current_justification.append(line)
    
    # Save the last justification
    if current_place is not None and current_justification:
        justifications[current_place] = ' '.join(current_justification)
    
    # Create result tuples
    for place, submission_id in rankings.items():
        comment = justifications.get(place, "")
        results.append((submission_id, place, comment))
    
    print(f"Parsed {len(results)} rankings from AI response")
    return results

def run_ai_evaluation(contest_id, judge_id):
    """Run an AI evaluation for a contest using the specified judge."""
    try:
        # Get the contest, judge, and submissions
        contest = db.session.get(Contest, contest_id)
        judge = db.session.get(User, judge_id)
        
        if not contest or not judge:
            return {
                'success': False,
                'message': f"Contest ID {contest_id} or Judge ID {judge_id} not found."
            }
        
        if not judge.is_ai_judge():
            return {
                'success': False,
                'message': f"Judge {judge.username} is not an AI judge."
            }
        
        # Check if the judge is assigned to this contest
        judge_contest_assignment = db.session.execute(
            db.select(contest_judges).where(
                contest_judges.c.contest_id == contest_id,
                contest_judges.c.user_id == judge_id
            )
        ).first()
        
        if not judge_contest_assignment:
            return {
                'success': False,
                'message': f"Judge {judge.username} is not assigned to this contest."
            }
        
        # Get the AI model from the association table
        ai_model_id = judge_contest_assignment.ai_model
        
        if not ai_model_id:
            return {
                'success': False, 
                'message': f"No AI model specified for judge {judge.username} in this contest."
            }
        
        # Get submissions for this contest
        submissions = db.session.scalars(
            db.select(Submission).where(Submission.contest_id == contest_id)
        ).all()
        
        if not submissions:
            return {
                'success': False,
                'message': f"No submissions found for contest ID {contest_id}."
            }
        
        # Check for existing evaluation to avoid duplicates
        existing_evaluation = db.session.scalar(
            db.select(AIEvaluation).where(
                AIEvaluation.contest_id == contest_id,
                AIEvaluation.judge_id == judge_id
            )
        )
        
        if existing_evaluation:
            return {
                'success': False,
                'message': f"An evaluation already exists for this judge and contest."
            }
        
        # Construct the prompt
        prompt = construct_prompt(contest, judge, submissions)
        
        # Call the AI API
        api_result = call_ai_api(prompt, ai_model_id)
        
        if not api_result['success']:
            return {
                'success': False,
                'message': f"Error calling AI API: {api_result['response_text']}"
            }
        
        # Parse the response
        parsed_results = parse_ai_response(api_result['response_text'], submissions)
        
        # Create an AIEvaluation record
        evaluation = AIEvaluation(
            contest_id=contest_id,
            judge_id=judge_id,
            ai_model=ai_model_id,
            full_prompt=prompt,
            response_text=api_result['response_text'],
            prompt_tokens=api_result['prompt_tokens'],
            completion_tokens=api_result['completion_tokens'],
            cost=api_result['cost']
        )
        
        db.session.add(evaluation)
        
        # Create Vote records for each ranked submission
        votes_created = 0
        for submission_id, place, comment in parsed_results:
            # Skip if the submission ID doesn't exist
            if not db.session.get(Submission, submission_id):
                continue
                
            vote = Vote(
                judge_id=judge_id,
                submission_id=submission_id,
                place=place,
                comment=comment
            )
            db.session.add(vote)
            votes_created += 1
        
        # Commit all changes
        db.session.commit()
        
        return {
            'success': True,
            'message': f"AI evaluation completed successfully. Created {votes_created} vote records.",
            'evaluation_id': evaluation.id,
            'cost': api_result['cost']
        }
    
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'message': f"Error running AI evaluation: {str(e)}"
        } 