import pytest
import os
from langflix.core.video.text_utils import get_text_pixel_width, wrap_text_to_pixel_width, scale_font_to_fit
from langflix.config.font_utils import get_platform_default_font

@pytest.fixture
def default_font():
    """Retrieve a valid font on the system, otherwise pytest.skip."""
    font_path = get_platform_default_font()
    if not font_path or not os.path.exists(font_path):
        pytest.skip("No valid system font found for exact pixel width tests")
    return font_path

def test_get_text_pixel_width_with_font(default_font):
    text = "Hello World"
    width = get_text_pixel_width(text, default_font, 48)
    assert width > 0
    # Width should be reasonably large for 48pt font
    assert width > 50

def test_get_text_pixel_width_fallback():
    # Invalid font path triggers fallback
    width = get_text_pixel_width("Test", "/invalid/path.ttf", 20)
    # length 4 * (20 * 0.6) = 4 * 12 = 48
    assert width == 48

def test_wrap_text_to_pixel_width(default_font):
    # Short text, should not wrap
    text = "Hello World"
    # A huge bounds
    wrapped = wrap_text_to_pixel_width(text, default_font, 20, 5000)
    assert wrapped == "Hello World"
    
    # Needs wrapping
    text_long = "This is a very long sentence that needs to be wrapped properly."
    font_size = 40
    # Measure "This is a very" to set a realistic tight bounds
    tiny_bound = get_text_pixel_width("This is a very", default_font, font_size) + 10
    
    wrapped = wrap_text_to_pixel_width(text_long, default_font, font_size, tiny_bound)
    assert "\n" in wrapped
    assert len(wrapped.split("\n")) > 1

def test_wrap_text_preserves_newlines(default_font):
    text = "Hello\nWorld"
    wrapped = wrap_text_to_pixel_width(text, default_font, 20, 5000)
    assert wrapped == "Hello\nWorld"

def test_scale_font_to_fit(default_font):
    long_word = "Supercalifragilisticexpialidocious"
    base_size = 100
    max_width = 200 # Very small width constraint
    
    # Should scale down to fit the bounds
    new_size = scale_font_to_fit(long_word, default_font, base_size, max_width, min_font_size=10)
    assert new_size < base_size
    assert new_size >= 10
