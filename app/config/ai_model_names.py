"""
Friendly names for AI models.

This file is designed to be easy to edit when new models are added.
It contains a mapping from model identifier to a human-readable name.
"""

# Map from model ID to friendly display name
MODEL_FRIENDLY_NAMES = {
    # Claude models
    'claude-3-5-haiku-latest': 'Claude 3.5 Haiku',
    'claude-3-7-sonnet-latest': 'Claude 3.7 Sonnet',
    'claude-3-opus-latest': 'Claude 3 Opus',
    'claude-3-sonnet-latest': 'Claude 3 Sonnet',
    'claude-3-haiku-latest': 'Claude 3 Haiku',
    
    # OpenAI models
    'gpt-4o': 'GPT-4o',
    'gpt-4o-mini': 'GPT-4o Mini',
    'gpt-4': 'GPT-4',
    'gpt-4-turbo': 'GPT-4 Turbo',
    
    # Meta models
    'meta-llama-3.2-90b': 'Llama 3.2 90B',
    'meta-llama-3.3-70b': 'Llama 3.3 70B',
    
    # Google models
    'gemini-1.5-pro-latest': 'Gemini 1.5 Pro',
    'gemini-1.5-flash-latest': 'Gemini 1.5 Flash',
}

def get_friendly_model_name(model_id):
    """
    Get the friendly display name for a model ID.
    
    Args:
        model_id (str): The identifier of the AI model
        
    Returns:
        str: The friendly display name, or the original model_id if no friendly name is defined
    """
    return MODEL_FRIENDLY_NAMES.get(model_id, model_id) 