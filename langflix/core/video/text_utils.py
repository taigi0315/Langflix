import logging
import os
from PIL import ImageFont

logger = logging.getLogger(__name__)

def get_text_pixel_width(text: str, font_path: str, font_size: int) -> int:
    """
    Get the exact pixel width of a text string rendered with a specific font.
    If the font file cannot be loaded, falls back to a crude character count estimate.
    """
    if not text:
        return 0
        
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
            # Use getlength for accurate horizontal advance width
            return int(font.getlength(text))
    except Exception as e:
        logger.debug(f"Could not load font {font_path} for width calculation: {e}")
        
    # Crude fallback if PIL or font fails (approx 0.6 * font_size per character)
    return int(len(text) * (font_size * 0.6))

def wrap_text_to_pixel_width(text: str, font_path: str, font_size: int, max_pixel_width: int) -> str:
    """
    Wrap text so that no single line exceeds max_pixel_width when rendered.
    Preserves existing newlines in the input text.
    """
    if not text or max_pixel_width <= 0:
        return text

    # If the font cannot be loaded, fallback to crude char count
    try:
        font = None
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        logger.debug(f"wrap_text_to_pixel_width: Using crude fallback due to font error: {e}")
        
    def get_width(s: str) -> int:
        if font:
            return int(font.getlength(s))
        return int(len(s) * (font_size * 0.6))

    paragraphs = text.split('\n')
    wrapped_lines = []

    for paragraph in paragraphs:
        if not paragraph.strip():
            wrapped_lines.append("")
            continue
            
        words = paragraph.split(' ')
        current_line = []
        current_width = 0
        
        # Pre-calculate space width
        space_width = get_width(" ")

        for word in words:
            word_width = get_width(word)
            
            # If line is empty, just add the word even if it exceeds max width 
            # (scaling handles oversized single words)
            if not current_line:
                current_line.append(word)
                current_width = word_width
            else:
                # Check if adding this word exceeds max width
                if current_width + space_width + word_width <= max_pixel_width:
                    current_line.append(word)
                    current_width += space_width + word_width
                else:
                    # Line full, push current line and start new one
                    wrapped_lines.append(' '.join(current_line))
                    current_line = [word]
                    current_width = word_width
                    
        if current_line:
            wrapped_lines.append(' '.join(current_line))

    return '\n'.join(wrapped_lines)

def scale_font_to_fit(text: str, font_path: str, base_font_size: int, max_pixel_width: int, min_font_size: int = 12) -> int:
    """
    Dynamically scale down the font size if the longest word in the text (or the text as a whole
    if wrapping is disabled) exceeds the max_pixel_width.
    """
    if not text or max_pixel_width <= 0:
        return base_font_size
        
    # We mainly care about words that are unbreakable and exceed the width
    words = text.replace('\n', ' ').split()
    if not words:
        return base_font_size
        
    longest_word = max(words, key=len)
    
    current_size = base_font_size
    while current_size > min_font_size:
        width = get_text_pixel_width(longest_word, font_path, current_size)
        if width <= max_pixel_width:
            break
        current_size -= 2
        
    return max(current_size, min_font_size)
