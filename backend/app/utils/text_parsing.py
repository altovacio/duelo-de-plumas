import re
from typing import Tuple, Optional

def extract_title_and_content(text: str, fallback_title: Optional[str] = None) -> Tuple[str, str]:
    """
    Extract title and content from structured text output.
    
    Expected format:
    Title: [title text]
    Text: [content text]
    
    Args:
        text: The text to parse
        fallback_title: Optional fallback title if parsing fails
        
    Returns:
        Tuple of (title, content)
    """
    if not text or not text.strip():
        return fallback_title or "Untitled", ""
    
    cleaned_text = text.strip()
    
    # Try to parse the expected format: "Title: ... Text: ..."
    title_pattern = r"^Title:\s*(.+?)(?=\n|$)"
    text_pattern = r"Text:\s*(.+)$"
    
    title_match = re.search(title_pattern, cleaned_text, re.MULTILINE | re.IGNORECASE)
    content_match = re.search(text_pattern, cleaned_text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    
    if title_match and content_match:
        title = title_match.group(1).strip()
        content = content_match.group(1).strip()
        return title, content
    
    # Fallback: try to extract title from first line
    lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]
    
    if lines:
        first_line = lines[0]
        
        # Remove common prefixes
        for prefix in ["title:", "Title:", "TITLE:", "**", "*", "#"]:
            if first_line.lower().startswith(prefix.lower()):
                first_line = first_line[len(prefix):].strip()
        
        # If first line looks like a title (short, no period at end)
        if len(first_line) <= 100 and not first_line.endswith('.'):
            title = first_line
            content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
            return title, content
    
    # Final fallback: use provided fallback title or generate one
    title = fallback_title or "Generated Text"
    return title, cleaned_text


def clean_text_content(content: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        content: Raw text content
        
    Returns:
        Cleaned text content
    """
    if not content:
        return ""
    
    # Remove excessive whitespace
    cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    
    return cleaned.strip()


def validate_title(title: str) -> bool:
    """
    Validate that a title meets basic quality standards.
    
    Args:
        title: The title to validate
        
    Returns:
        True if title is valid, False otherwise
    """
    if not title or not title.strip():
        return False
    
    title = title.strip()
    
    # Check length
    if len(title) > 200 or len(title) < 1:
        return False
    
    # Check for common parsing errors
    if title.lower().startswith("text:") or title.lower().startswith("content:"):
        return False
    
    return True


def validate_content(content: str, min_length: int = 10) -> bool:
    """
    Validate that content meets basic quality standards.
    
    Args:
        content: The content to validate
        min_length: Minimum required length
        
    Returns:
        True if content is valid, False otherwise
    """
    if not content or not content.strip():
        return False
    
    content = content.strip()
    
    # Check minimum length
    if len(content) < min_length:
        return False
    
    # Check for common parsing errors
    if content.lower().startswith("title:"):
        return False
    
    return True 