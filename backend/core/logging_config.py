import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict
import os
from logging.handlers import RotatingFileHandler


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info']:
                log_data[key] = value
        
        return json.dumps(log_data)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for development"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class LoggingConfig:
    """Centralized logging configuration"""
    
    @staticmethod
    def setup_logging():
        """Configure application logging"""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_format = os.getenv('LOG_FORMAT', 'json').lower()
        log_file_path = os.getenv('LOG_FILE_PATH', '/var/log/pairly/app.log')
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        if log_format == 'json':
            console_handler.setFormatter(JSONFormatter())
        else:
            console_formatter = ColoredConsoleFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler with rotation (if path is writable)
        try:
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            file_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=100 * 1024 * 1024,  # 100MB
                backupCount=5
            )
            file_handler.setFormatter(JSONFormatter())
            root_logger.addHandler(file_handler)
        except (OSError, PermissionError):
            # Silently skip file logging if can't write
            pass
        
        # Silence noisy third-party loggers
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('botocore').setLevel(logging.WARNING)
        logging.getLogger('stripe').setLevel(logging.WARNING)
        
        return root_logger
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger for a specific module"""
        return logging.getLogger(name)


# Initialize logging on module import
LoggingConfig.setup_logging()
