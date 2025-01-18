"""
Azure Table Storage logging module initialization.
"""

from .logger import AzureLogger, LogLevel
from .storage import AzureTableStorage

__all__ = ["AzureLogger", "LogLevel", "AzureTableStorage"]
