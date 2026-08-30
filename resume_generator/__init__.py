"""JSON 驱动的 DOCX 简历生成器。"""

__version__ = "1.1.0"

from .models import Contact, Entry, FieldError, Name, Section
from .renderer import render_resume
from .service import render_json_file_to_docx, render_json_to_docx
from .validator import load_json, parse_json, parse_locale, validate_json

__all__ = [
    "Contact",
    "Entry",
    "FieldError",
    "Name",
    "Section",
    "__version__",
    "load_json",
    "parse_json",
    "parse_locale",
    "render_json_file_to_docx",
    "render_json_to_docx",
    "render_resume",
    "validate_json",
]
