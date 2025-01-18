from .logger import AzureLogger, LogLevel
from .models import LogEntry
from .interfaces import LoggerInterface, StorageInterface
from .storage import AzureTableStorage

__all__ = ['AzureLogger', 'LogLevel', 'LogEntry', 'LoggerInterface', 'StorageInterface','AzureTableStorage']
__version__ = '1.0.0'