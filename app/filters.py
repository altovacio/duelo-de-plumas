import markdown
from flask import Blueprint, current_app

# Create a blueprint for filters
filters_bp = Blueprint('filters', __name__)

@filters_bp.app_template_filter('markdown')
def markdown_filter(text):
    """
    Convert Markdown text to HTML.
    
    Parameters:
    text (str): The Markdown text to be converted to HTML
    
    Returns:
    str: The HTML representation of the Markdown text
    """
    if text:
        # Use the Python Markdown library to convert markdown to HTML
        # Enable extensions for tables, fenced code, and more
        extensions = [
            'markdown.extensions.extra',  # Includes tables, fenced_code, footnotes, etc.
            'markdown.extensions.codehilite',  # Code syntax highlighting
            'markdown.extensions.nl2br',  # Convert newlines to <br>
            'markdown.extensions.sane_lists',  # Better list handling
        ]
        
        return markdown.markdown(text, extensions=extensions)
    return "" 