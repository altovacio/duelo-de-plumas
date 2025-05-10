import markdown
import bleach
from bleach.sanitizer import ALLOWED_TAGS, ALLOWED_ATTRIBUTES

# Extend the allowed HTML tags for markdown rendering
EXTENDED_ALLOWED_TAGS = ALLOWED_TAGS + [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'p', 'a', 'ul', 'ol', 'nl', 'li',
    'b', 'i', 'strong', 'em', 'strike', 'abbr', 'code',
    'hr', 'br', 'div', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'pre', 'img'
]

# Extend the allowed attributes
EXTENDED_ALLOWED_ATTRIBUTES = {**ALLOWED_ATTRIBUTES, **{
    'a': ['href', 'title', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'abbr': ['title'],
}}

def markdown_to_html(markdown_text: str) -> str:
    """
    Convert markdown text to safe HTML.
    
    Args:
        markdown_text: Text in markdown format
        
    Returns:
        Safe HTML string
    """
    # Convert Markdown to HTML
    html = markdown.markdown(markdown_text, extensions=['extra', 'codehilite'])
    
    # Sanitize HTML to prevent XSS attacks
    sanitized_html = bleach.clean(
        html,
        tags=EXTENDED_ALLOWED_TAGS,
        attributes=EXTENDED_ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    return sanitized_html

def validate_markdown(markdown_text: str) -> bool:
    """
    Validate if the text is valid markdown without dangerous content.
    
    Args:
        markdown_text: Text to validate
        
    Returns:
        True if the text is valid markdown, False otherwise
    """
    try:
        html = markdown_to_html(markdown_text)
        return True
    except Exception:
        return False 