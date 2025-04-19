"""
Configuration parameters for AI judges in Duelo de Plumas.

This file contains the configuration settings for AI judges, including:
- Available AI models
- Base instruction prompts
- Formatting settings
- Token limits and constraints
"""

# Available AI models for judges
AI_MODELS = [
    {
        'id': 'gpt-4-turbo',
        'name': 'GPT-4 Turbo',
        'provider': 'openai',
        'max_tokens': 128000,
        'api_name': 'gpt-4-turbo-preview'
    },
    {
        'id': 'gpt-4', 
        'name': 'GPT-4',
        'provider': 'openai',
        'max_tokens': 8192,
        'api_name': 'gpt-4'
    },
    {
        'id': 'gpt-3.5-turbo',
        'name': 'GPT-3.5 Turbo',
        'provider': 'openai',
        'max_tokens': 16385,
        'api_name': 'gpt-3.5-turbo'
    },
    {
        'id': 'claude-3-opus', 
        'name': 'Claude 3 Opus',
        'provider': 'anthropic',
        'max_tokens': 200000,
        'api_name': 'claude-3-opus-20240229'
    },
    {
        'id': 'claude-3-sonnet', 
        'name': 'Claude 3 Sonnet',
        'provider': 'anthropic',
        'max_tokens': 200000,
        'api_name': 'claude-3-sonnet-20240229'
    },
    {
        'id': 'claude-3-haiku', 
        'name': 'Claude 3 Haiku',
        'provider': 'anthropic',
        'max_tokens': 200000,
        'api_name': 'claude-3-haiku-20240307'
    }
]

# Base instruction prompt for all AI judges
BASE_INSTRUCTION_PROMPT = """
Eres un juez literario para un concurso de escritura. Tu tarea es evaluar los textos presentados y determinar su ranking según su calidad literaria.

Por favor, lee cuidadosamente todos los textos, y luego:

1. Asigna un primer lugar (1), segundo lugar (2) y tercer lugar (3) basado en la calidad literaria de los textos.
2. Opcionalmente, puedes asignar una Mención Honorífica (4) a un texto adicional que consideres meritorio.
3. Proporciona una breve justificación para cada lugar asignado.

INSTRUCCIONES IMPORTANTES:
- Debes asignar exactamente un primer, un segundo y un tercer lugar (siempre que haya al menos tres textos).
- No debes asignar más de un texto a cada posición (1, 2, 3).
- Puedes asignar una Mención Honorífica (4) a un solo texto adicional.
- Usa criterios literarios profesionales en tu evaluación.
- Juzga cada texto por sus propios méritos literarios.

Por favor, entrega tu evaluación en el siguiente formato:

RANKING:
1. [ID del texto] - [Título del texto]
2. [ID del texto] - [Título del texto]
3. [ID del texto] - [Título del texto]
4. [ID del texto] - [Título del texto] (Mención Honorífica, opcional)

JUSTIFICACIONES:
1. [Breve justificación del primer lugar]
2. [Breve justificación del segundo lugar]
3. [Breve justificación del tercer lugar]
4. [Breve justificación de la Mención Honorífica] (si corresponde)
"""

# Maximum number of tokens allowed for personality prompt
MAX_PERSONALITY_PROMPT_TOKENS = 1000

# Pricing for API calls (USD per 1000 tokens)
# These rates can be updated as pricing changes
API_PRICING = {
    'openai': {
        'gpt-4-turbo-preview': {'input': 0.01, 'output': 0.03},
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015}
    },
    'anthropic': {
        'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075},
        'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015},
        'claude-3-haiku-20240307': {'input': 0.00025, 'output': 0.00125}
    }
}

# Default model to use if none is specified
DEFAULT_AI_MODEL = 'gpt-3.5-turbo' 