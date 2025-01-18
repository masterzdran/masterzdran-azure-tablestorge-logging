from .interfaces import LoggerInterface, StorageInterface
from .logger import AzureLogger, LogLevel
from .models import LogEntry
from .storage import AzureTableStorage

__all__ = [
    "AzureLogger",
    "LogLevel",
    "LogEntry",
    "LoggerInterface",
    "StorageInterface",
    "AzureTableStorage",
]
__version__ = "1.0.0"
