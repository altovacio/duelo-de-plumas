import markdown
from flask import Blueprint, current_app
from datetime import datetime, timezone
import locale
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for older Python versions if needed, though zoneinfo is standard >= 3.9
    # from backports.zoneinfo import ZoneInfo # Or handle differently
    ZoneInfo = None # Indicate zoneinfo is not available

# Create a blueprint for filters
filters_bp = Blueprint('filters', __name__)

# Define Mexico City timezone
MEXICO_CITY_TZ = ZoneInfo("America/Mexico_City") if ZoneInfo else None

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
    Format a date in a human-readable format, converting from UTC to Mexico City time.

    Parameters:
    date (datetime): The UTC date to format
    with_time (bool): Whether to include the time

    Returns:
    str: A formatted date string in Mexico City time (e.g., "24 de Julio de 2024 - 10:30 CST")
    """
    if not date or not MEXICO_CITY_TZ:
        # Return original formatting or empty if date is None or zoneinfo is not available
        return date.strftime('%Y-%m-%d %H:%M UTC') if date and with_time else (date.strftime('%Y-%m-%d UTC') if date else "")

    try:
        # Assume input 'date' is naive but represents UTC
        if date.tzinfo is None:
            date_utc = date.replace(tzinfo=timezone.utc)
        else:
            # If it's already aware, ensure it's UTC before converting
            date_utc = date.astimezone(timezone.utc)

        # Convert to Mexico City time
        date_mc = date_utc.astimezone(MEXICO_CITY_TZ)

        # Set locale to Spanish for month names
        try:
            # Try common Spanish locale names
            locale.setlocale(locale.LC_TIME, 'es_MX.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
            except locale.Error:
                 try:
                     locale.setlocale(locale.LC_TIME, 'Spanish_Mexico') # Windows locale name
                 except locale.Error:
                     pass # Use default locale if Spanish is unavailable

        # Format based on whether we want time included
        if with_time:
            # Include time and timezone abbreviation (e.g., CST/CDT)
            return date_mc.strftime('%d de %B de %Y - %H:%M %Z')
        else:
            # Just the date
            return date_mc.strftime('%d de %B de %Y')
    except Exception as e:
        # Log error or handle gracefully
        current_app.logger.error(f"Error formatting date {date}: {e}")
        # Fallback formatting
        return str(date) + " (Error formatting)" 