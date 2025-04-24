import markdown
from flask import Blueprint, current_app
from datetime import datetime
import locale

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

@filters_bp.app_template_filter('human_date')
def human_date_filter(date, with_time=False):
    """
    Format a date in a human-readable format.
    
    Parameters:
    date (datetime): The date to format
    with_time (bool): Whether to include the time
    
    Returns:
    str: A formatted date string
    """
    if not date:
        return ""
    
    try:
        # Set locale to Spanish
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except locale.Error:
        # Fallback if Spanish locale is not available
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES')
        except locale.Error:
            pass
    
    # Format based on whether we want time included
    if with_time:
        return date.strftime('%d de %B de %Y - %H:%M')
    else:
        return date.strftime('%d de %B de %Y') 