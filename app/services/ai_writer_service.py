"""
Service module for AI writers in Duelo de Plumas.

This module provides functionality for:
- Connecting to AI model APIs (OpenAI, Anthropic)
- Formatting prompts for text generation
- Using AI writers to generate submissions for contests
"""

import os
import re
import json
import openai
import anthropic
import tiktoken
from app import db
from app.models import Contest, Submission, AIWriter, AIWritingRequest
from app.config.ai_judge_params import AI_MODELS, API_PRICING, DEFAULT_AI_MODEL

# Initialize API clients
openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
anthropic_client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

# Base instruction prompt for all AI writers
BASE_INSTRUCTION_PROMPT = """
<MISION>
Eres un escritor creativo participando en un concurso de escritura. Tu tarea es escribir un texto original basado en la descripción del concurso y acorde a tu personalidad y estilo literario definido.
</MISION>

<TAREA>
Por favor, crea un texto literario original que:
1. Responda a la temática y descripción del concurso proporcionado
2. Refleje tu estilo y personalidad como escritor
3. Sea creativo, coherente y de calidad literaria

El texto debe tener un título ya proporcionado y un cuerpo que constituya la obra principal.
</TAREA>

<FORMATO_DE_RESPUESTA>
Por favor, entrega tu texto creativo directamente, sin comentarios adicionales, explicaciones o metacomunicación.
Simplemente escribe el texto creativo que será enviado al concurso.
</FORMATO_DE_RESPUESTA>
"""

def get_model_info(model_id):
    """Get model information by ID."""
    for model in AI_MODELS:
        if model['id'] == model_id:
            return model
    # Default to first model if not found
    return next((m for m in AI_MODELS if m['id'] == DEFAULT_AI_MODEL), AI_MODELS[0])

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

def calculate_cost(model_info, prompt_tokens, completion_tokens):
    """Calculate the cost of an API call in USD."""
    pricing = API_PRICING.get(model_info['provider'], {}).get(model_info['api_name'], {'input': 0, 'output': 0})
    input_cost = (prompt_tokens / 1000) * pricing['input']
    output_cost = (completion_tokens / 1000) * pricing['output']
    return input_cost + output_cost

def construct_prompt(contest, ai_writer, title):
    """Construct the full prompt for the AI writer."""
    # Get the base instruction prompt
    instruction_prompt = BASE_INSTRUCTION_PROMPT
    
    # Get the writer's personality prompt
    personality_prompt = ai_writer.personality_prompt or ""
    
    # Combine the prompts with context about the contest
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

def call_ai_api(prompt, model_id):
    """Call the appropriate AI API with the prompt."""
    model_info = get_model_info(model_id)
    
    try:
        if model_info['provider'] == 'openai':
            response = openai_client.chat.completions.create(
                model=model_info['api_name'],
                messages=[{"role": "system", "content": prompt}],
                temperature=0.7  # Higher temperature for more creative output
            )
            response_text = response.choices[0].message.content
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            
        elif model_info['provider'] == 'anthropic':
            response = anthropic_client.messages.create(
                model=model_info['api_name'],
                max_tokens=4000,  # Allow for longer responses for creative writing
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7  # Higher temperature for more creative output
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

def generate_text(contest_id, ai_writer_id, model_id, title):
    """
    Generate a text using an AI writer and submit it to a contest.
    
    Args:
        contest_id: ID of the contest
        ai_writer_id: ID of the AI writer
        model_id: ID of the AI model to use
        title: Title for the generated text
        
    Returns:
        A dictionary with status and message
    """
    try:
        # Get the contest and AI writer
        contest = db.session.get(Contest, contest_id)
        ai_writer = db.session.get(AIWriter, ai_writer_id)
        
        if not contest:
            return {"success": False, "message": "Contest not found"}
        
        if not ai_writer:
            return {"success": False, "message": "AI Writer not found"}
        
        # Check if contest is open
        if contest.status != 'open':
            return {"success": False, "message": "Contest is not open for submissions"}
        
        # Construct the prompt
        prompt = construct_prompt(contest, ai_writer, title)
        
        # Call the AI API
        api_result = call_ai_api(prompt, model_id)
        
        if not api_result['success']:
            return {"success": False, "message": f"Error calling AI API: {api_result['response_text']}"}
        
        # Create a submission
        submission = Submission(
            author_name=f"{ai_writer.name} (IA)",
            title=title,
            text_content=api_result['response_text'],
            contest_id=contest.id,
            is_ai_generated=True,
            ai_writer_id=ai_writer.id
        )
        
        db.session.add(submission)
        
        # Record the AI writing request
        writing_request = AIWritingRequest(
            contest_id=contest.id,
            ai_writer_id=ai_writer.id,
            ai_model=model_id,
            full_prompt=prompt,
            response_text=api_result['response_text'],
            prompt_tokens=api_result['prompt_tokens'],
            completion_tokens=api_result['completion_tokens'],
            cost=api_result['cost'],
            timestamp=submission.submission_date
        )
        
        db.session.add(writing_request)
        
        # Link the submission to the writing request
        writing_request.submission_id = submission.id
        
        db.session.commit()
        
        return {
            "success": True, 
            "message": f"Text generated and submitted successfully",
            "submission_id": submission.id,
            "text": api_result['response_text']
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"Error generating text: {e}")
        return {"success": False, "message": f"Error generating text: {str(e)}"} 