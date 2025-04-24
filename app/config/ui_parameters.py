"""
UI Parameters for Duelo de Plumas platform.
This file contains styling and layout parameters that can be easily modified.
"""

# Color scheme parameters
COLORS = {
    'primary': '#5e6b4c',       # Forest green as primary color 
    'primary_dark': '#44513a',  # Darker shade of forest green
    'secondary': '#a07d41',     # Warm amber/gold as secondary
    'text': '#35302a',          # Deep brown for text
    'text_light': '#665e54',    # Lighter brown for secondary text
    'background': '#f7f5f0',    # Soft cream background
    'card_bg': '#ffffff',       # White card background
    'border': '#e0d8c9',        # Beige border color
    'success': '#6b8e4e',       # Muted green for success
    'warning': '#c9a459',       # Gold/amber for warning
    'error': '#a3423c',         # Earthy red for error
    'info': '#607b8d',          # Muted blue-gray for info
}

# Typography parameters
TYPOGRAPHY = {
    'heading_font': "'Playfair Display', 'Georgia', serif",  # Literary serif font for headings
    'body_font': "'Source Sans Pro', 'Helvetica Neue', sans-serif",  # Clean sans-serif for body
    'base_size': '16px',        # Base font size
    'line_height': '1.6',       # Line height
}

# Layout parameters
LAYOUT = {
    'max_width': '1120px',      # Max content width (golden ratio for 16:9 screens)
    'border_radius': '4px',     # More subtle border radius
    'spacing_unit': '8px',      # Base spacing unit
    'card_padding': '24px',     # Card padding
    'section_spacing': '32px',  # Space between sections
}

# Date format
DATE_FORMATS = {
    'short': '%d/%m/%Y',        # Short date format
    'long': '%d de %B de %Y',   # Long date format with month name
    'with_time': '%d/%m/%Y %H:%M',  # Date with time
}

# Contest card parameters
CONTEST_CARD = {
    'max_description_chars': 150,  # Maximum characters for description preview
    'show_participant_count': True, # Whether to show participant count
    'show_submission_count': True,  # Whether to show submission count
} 