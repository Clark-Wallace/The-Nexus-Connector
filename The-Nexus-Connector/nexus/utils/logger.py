"""Logging utilities for Nexus."""

import logging
import sys
from typing import Optional


def get_logger(name: str, verbose: bool = False) -> logging.Logger:
    """
    Get a configured logger.
    
    Args:
        name: Logger name
        verbose: Whether to enable verbose output
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        # Create handler
        handler = logging.StreamHandler(sys.stdout)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        # Set level
        level = logging.DEBUG if verbose else logging.INFO
        logger.setLevel(level)
    
    return logger