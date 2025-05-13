import os
import logging

from logging.handlers import RotatingFileHandler

log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()

logging.basicConfig(
    level = logging.WARNING
)

def setup_logging(logger_name = None):
    logger = logging.getLogger(logger_name)

    logger.setLevel(log_level)

    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    log_handler = RotatingFileHandler(
        'logs/app.log', maxBytes = 10 * 1024 * 1024, backupCount = 5)
    
    log_handler.setLevel(log_level)

    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    log_handler.setFormatter(log_formatter)
    
    logger.addHandler(log_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_formatter)

    logger.addHandler(console_handler)

    return logger
