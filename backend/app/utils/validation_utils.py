from typing import List, Dict, Any
import re

def validate_text_length(text: str, min_length: int = 1, max_length: int = 50000) -> bool:
    """
    Validate text length.
    
    Args:
        text: The text to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        True if the text length is valid, False otherwise
    """
    return min_length <= len(text) <= max_length

def validate_title(title: str, min_length: int = 3, max_length: int = 200) -> bool:
    """
    Validate a title.
    
    Args:
        title: The title to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        True if the title is valid, False otherwise
    """
    return validate_text_length(title, min_length, max_length)

def validate_content(content: str, min_length: int = 10, max_length: int = 50000) -> bool:
    """
    Validate content.
    
    Args:
        content: The content to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        True if the content is valid, False otherwise
    """
    return validate_text_length(content, min_length, max_length)

def sanitize_input(text: str) -> str:
    """
    Sanitize input text to remove potentially harmful content.
    This is a basic implementation; in a production environment,
    a more robust solution like bleach would be recommended.
    
    Args:
        text: The text to sanitize
        
    Returns:
        Sanitized text
    """
    # Remove script tags, event handlers, and other potentially harmful content
    sanitized = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
    sanitized = re.sub(r'<.*?on\w+\s*=.*?>', '', sanitized, flags=re.DOTALL)
    
    return sanitized 