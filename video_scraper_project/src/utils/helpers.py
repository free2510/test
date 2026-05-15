# -*- coding: utf-8 -*-
"""
Utility helper functions for the Video Scraper project.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Optional, Any, Dict

from config.settings import LOG_LEVEL, LOG_FORMAT


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    Sanitize filename by removing invalid characters and limiting length.
    
    Args:
        filename: Original filename
        max_length: Maximum length of filename (excluding extension)
    
    Returns:
        Sanitized filename
    """
    # Remove .mp4 extension if present for processing
    name_without_ext = filename.replace('.mp4', '').strip()
    
    # Keep only alphanumeric, spaces, underscores, dots, and Arabic characters
    # Arabic Unicode range: \u0600-\u06FF
    sanitized = ""
    for char in name_without_ext:
        if char.isalnum() or char in (' ', '.', '_') or '\u0600' <= char <= '\u06FF':
            sanitized += char
    
    # Replace multiple spaces with single space
    sanitized = ' '.join(sanitized.split())
    
    # Replace spaces with underscores for file system compatibility
    sanitized = sanitized.replace(' ', '_')
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Add .mp4 extension
    return f"{sanitized}.mp4"


def setup_logging(name: str = __name__, level: str = None, log_format: str = None) -> logging.Logger:
    """
    Setup and return a logger instance.
    
    Args:
        name: Logger name
        level: Logging level (default from config)
        log_format: Log format string (default from config)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level or LOG_LEVEL))
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(log_format or LOG_FORMAT))
        logger.addHandler(handler)
    
    return logger


def load_json_file(filepath: str) -> Optional[Any]:
    """
    Load data from a JSON file.
    
    Args:
        filepath: Path to JSON file
    
    Returns:
        Loaded data or None if file doesn't exist or error occurs
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not load JSON file {filepath}: {e}")
    return None


def save_json_file(filepath: str, data: Any) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        filepath: Path to JSON file
        data: Data to save
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Could not save JSON file {filepath}: {e}")
        return False
