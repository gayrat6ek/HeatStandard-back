"""Language utilities for multi-language support."""
from enum import Enum


class Language(str, Enum):
    """Supported languages."""
    UZBEK = "uz"
    RUSSIAN = "ru"
    ENGLISH = "en"


def get_translated_field(obj, field_base: str, language: Language) -> str:
    """
    Get translated field value based on language.
    
    Args:
        obj: Database model object
        field_base: Base field name (e.g., 'name', 'description')
        language: Target language
        
    Returns:
        Translated field value
    """
    field_name = f"{field_base}_{language.value}"
    return getattr(obj, field_name, None)


def set_translated_fields(data: dict, field_base: str, value: str) -> dict:
    """
    Set all language fields with the same value (for initial data).
    
    Args:
        data: Dictionary to update
        field_base: Base field name
        value: Value to set for all languages
        
    Returns:
        Updated dictionary
    """
    for lang in Language:
        data[f"{field_base}_{lang.value}"] = value
    return data
