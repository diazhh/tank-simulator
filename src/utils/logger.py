"""
Utility module for setting up logging.
"""
import os
import sys
from datetime import datetime
from typing import Dict

from loguru import logger


def setup_logger(config: Dict) -> None:
    """
    Set up the logger with the specified configuration.
    
    Args:
        config: Simulation configuration dictionary
    """
    # Get log level from config
    log_level = config.get('simulation', {}).get('log_level', 'INFO')
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate log file name with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(logs_dir, f'tank_simulator_{timestamp}.log')
    
    # Configure logger
    logger.remove()  # Remove default handler
    
    # Add console handler
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Add file handler
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="1 week"
    )
    
    logger.info(f"Logger initialized with level {log_level}")
    logger.info(f"Logging to {log_file}")
