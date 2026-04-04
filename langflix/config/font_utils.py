"""Font utility functions for platform-specific font detection.

Uses Noto Sans font family as the universal default to prevent tofu (□□□) rendering.
Noto = "No Tofu" - designed by Google to cover all Unicode characters.
"""

import os
import platform
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Noto Sans font paths on Linux/Docker (installed via apt)
NOTO_SANS_CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
NOTO_SANS_REGULAR = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
NOTO_SANS_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"

# CJK language codes
CJK_LANGUAGES = {'ko', 'ja', 'zh', 'korean', 'japanese', 'chinese'}

def normalize_language_code(language_str: Optional[str]) -> Optional[str]:
    """Map full language names to 2-letter ISO codes"""
    if not language_str:
        return None
    lang = language_str.lower().strip()
    mapping = {
        'korean': 'ko', 'japanese': 'ja', 'chinese': 'zh',
        'spanish': 'es', 'english': 'en', 'french': 'fr', 'german': 'de'
    }
    return mapping.get(lang, lang)

def check_universal_font() -> str:
    """Check if the user dropped a universal.ttf font in assets/fonts/"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        for filename in ["universal.ttf", "universal.ttc"]:
            universal_path = os.path.join(project_root, "assets", "fonts", filename)
            if os.path.exists(universal_path):
                return universal_path
    except Exception:
        pass
    return ""


def _find_first_existing(*paths: str) -> str:
    """Return the first path that exists, or empty string."""
    for p in paths:
        if p and os.path.exists(p):
            return p
    return ""


def get_platform_default_font() -> str:
    """Get appropriate default font based on platform."""
    system = platform.system()

    # First check for universal font
    univ_font = check_universal_font()
    if univ_font:
        return univ_font

    if system == "Darwin":
        return _find_first_existing(
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        )
    elif system == "Linux":
        return _find_first_existing(
            NOTO_SANS_CJK,
            NOTO_SANS_REGULAR,
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        )
    elif system == "Windows":
        return _find_first_existing(
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/malgun.ttf",
        )
    return ""


def _get_noto_font_for_language(language_code: Optional[str], bold: bool = False) -> str:
    """Get appropriate Noto Sans font for a language on Linux/Docker.
    Noto Sans CJK actually includes Latin-1 and Latin-2, meaning it covers Spanish/English.
    Using it as the default prevents missing character boxes for mixed text."""
    # We prioritize CJK since it inherently contains comprehensive Latin support!
    if bold:
        return _find_first_existing(NOTO_SANS_BOLD, NOTO_SANS_CJK, NOTO_SANS_REGULAR)
    return _find_first_existing(NOTO_SANS_CJK, NOTO_SANS_REGULAR)


def get_font_file_for_language(language_code: Optional[str] = None, use_case: str = "default") -> str:
    """
    Get font file path for the given language.

    Resolution order:
    1. Per-language config from settings (if font file exists)
    2. Platform-specific universal font (Noto Sans on Linux, Arial Unicode on macOS)
    3. Platform default fallback
    """
    system = platform.system()
    is_bold_use_case = use_case in ("title", "educational_slide", "keywords")
    language_code = normalize_language_code(language_code)

    # 0. Check custom universal super-font
    univ_font = check_universal_font()
    if univ_font:
        return univ_font
        
    # Try configured fonts first (from default.yaml)
    try:
        from langflix import settings
        language_fonts_config = settings.get_language_fonts_config()

        def resolve_font(config_section, key):
            if not config_section or key not in config_section:
                return None
            font_rel_path = config_section[key]
            if "assets/fonts" in font_rel_path:
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                abs_path = os.path.join(project_root, font_rel_path)
                if os.path.exists(abs_path):
                    return abs_path
            if os.path.exists(font_rel_path):
                return font_rel_path
            return None

        # language -> use_case -> language -> default -> global -> use_case -> global -> default
        if language_code and language_code in language_fonts_config:
            font = resolve_font(language_fonts_config[language_code], use_case)
            if font:
                return font
            font = resolve_font(language_fonts_config[language_code], "default")
            if font:
                return font
        if "default" in language_fonts_config:
            font = resolve_font(language_fonts_config["default"], use_case)
            if font:
                return font
            font = resolve_font(language_fonts_config["default"], "default")
            if font:
                return font
    except Exception as e:
        logger.debug(f"Config font lookup failed: {e}")

    # Platform-specific universal fonts
    if system == "Linux":
        font = _get_noto_font_for_language(language_code, bold=is_bold_use_case)
        if font:
            return font
    elif system == "Darwin":
        # macOS: Arial Unicode supports virtually everything
        font = _find_first_existing(
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
        )
        if font:
            return font

    return get_platform_default_font()


def validate_spanish_font_support() -> dict:
    """Validate Spanish font support on the current system."""
    try:
        from ..core.language_config import LanguageConfig
        return LanguageConfig.validate_font_for_language('es')
    except ImportError:
        return {'validation_status': 'error', 'error': 'LanguageConfig not available'}


def get_fonts_dir() -> str:
    """Get platform-specific fonts directory for FFmpeg subtitles filter."""
    system = platform.system()
    if system == "Darwin":
        return "/System/Library/Fonts"
    elif system == "Linux":
        return "/usr/share/fonts"
    elif system == "Windows":
        return "C:/Windows/Fonts"
    return "/usr/share/fonts"


def get_font_name_for_ffmpeg(font_path: Optional[str] = None, language_code: Optional[str] = None) -> str:
    """Get font name for FFmpeg FontName parameter."""
    if font_path:
        name_map = {
            'NotoSansCJK': 'Noto Sans CJK',
            'NotoSans': 'Noto Sans',
            'AppleSDGothicNeo': 'Apple SD Gothic Neo',
            'NanumGothic': 'NanumGothic',
            'Hiragino': 'Hiragino Sans',
            'HelveticaNeue': 'Helvetica Neue',
            'Arial Unicode': 'Arial Unicode MS',
            'Arial': 'Arial',
            'DejaVuSans': 'DejaVu Sans',
        }
        for key, name in name_map.items():
            if key in font_path:
                return name

    system = platform.system()
    if system == "Darwin":
        return "Arial Unicode MS"
    elif system == "Linux":
        if language_code in CJK_LANGUAGES:
            return "Noto Sans CJK"
        return "Noto Sans"
    elif system == "Windows":
        return "Arial"
    return "Arial"
