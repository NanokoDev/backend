from enum import Enum


class LogLevel(Enum):
    """LogLevel enum for logging levels"""

    CRITICAL = 50
    ERROR = 40
    WARN = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0
