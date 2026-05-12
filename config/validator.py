"""
Zenith Configuration Schema Validator
======================================
Validates the zenith.yaml configuration file against the expected schema.
Ensures all required sections and keys are present.

Usage:
    from config.validator import validate_config
    config = load_zenith_config()
    errors = validate_config(config)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("zenith.config.validator")

# Required top-level sections
REQUIRED_SECTIONS = [
    "server", "voice", "llm", "personality",
    "skills", "memory", "ui"
]

# Required keys within each section
SECTION_SCHEMA = {
    "server": {
        "required": ["port"],
        "types": {"port": int},
    },
    "voice": {
        "required": ["stt_provider", "language"],
        "types": {"stt_provider": str, "language": str},
    },
    "llm": {
        "required": ["primary"],
        "types": {"primary": str},
    },
    "personality": {
        "required": ["name", "style"],
        "types": {"name": str, "style": str},
    },
    "skills": {
        "required": ["enabled"],
        "types": {"enabled": bool, "nlp_confidence_threshold": (int, float)},
    },
    "memory": {
        "required": ["db_type"],
        "types": {"db_type": str},
    },
    "ui": {
        "required": ["theme"],
        "types": {"theme": str},
    },
}

# Optional sections with their schemas
OPTIONAL_SECTION_SCHEMA = {
    "vision": {
        "sub_sections": ["ocr", "face_auth", "object_detection"],
    },
    "desktop": {
        "sub_sections": ["automation"],
    },
    "browser": {
        "sub_sections": ["automation"],
    },
    "rate_limiting": {
        "required": ["max_requests_per_minute"],
        "types": {"max_requests_per_minute": int},
    },
}


def validate_config(config: dict[str, Any]) -> list[str]:
    """
    Validate a Zenith configuration dictionary against the schema.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        List of error messages. Empty list means config is valid.
    """
    errors: list[str] = []

    if not isinstance(config, dict):
        return ["Configuration must be a dictionary"]

    # Check required sections
    for section in REQUIRED_SECTIONS:
        if section not in config:
            errors.append(f"Missing required section: '{section}'")
        elif not isinstance(config[section], dict):
            errors.append(f"Section '{section}' must be a dictionary")

    # Validate required keys within each section
    for section_name, schema in SECTION_SCHEMA.items():
        section_data = config.get(section_name)
        if not isinstance(section_data, dict):
            continue

        for key in schema.get("required", []):
            if key not in section_data:
                errors.append(f"Missing required key: '{section_name}.{key}'")
            elif key in schema.get("types", {}):
                expected_type = schema["types"][key]
                if not isinstance(section_data[key], expected_type):
                    errors.append(
                        f"Invalid type for '{section_name}.{key}': "
                        f"expected {expected_type.__name__}, got {type(section_data[key]).__name__}"
                    )

    # Validate optional sections (soft checks)
    for section_name, schema in OPTIONAL_SECTION_SCHEMA.items():
        section_data = config.get(section_name)
        if section_data is None:
            continue  # Optional sections are fine to omit

        if not isinstance(section_data, dict):
            errors.append(f"Section '{section_name}' must be a dictionary")
            continue

        # Check sub-sections
        for sub in schema.get("sub_sections", []):
            if sub in section_data and not isinstance(section_data[sub], dict):
                errors.append(f"Sub-section '{section_name}.{sub}' must be a dictionary")

        # Check required keys in optional sections
        for key in schema.get("required", []):
            if key not in section_data:
                errors.append(f"Missing key in optional section: '{section_name}.{key}'")

    # LLM provider validation
    llm_config = config.get("llm", {})
    primary = llm_config.get("primary")
    if primary and primary not in llm_config:
        errors.append(
            f"Primary LLM provider '{primary}' has no configuration in 'llm.{primary}'"
        )

    fallbacks = llm_config.get("fallback", [])
    if isinstance(fallbacks, list):
        for fb in fallbacks:
            if fb not in llm_config:
                errors.append(
                    f"Fallback LLM provider '{fb}' has no configuration in 'llm.{fb}'"
                )

    if errors:
        logger.warning("Config validation found %d issue(s)", len(errors))
        for err in errors:
            logger.warning("  - %s", err)
    else:
        logger.info("Config validation passed (all checks OK)")

    return errors
