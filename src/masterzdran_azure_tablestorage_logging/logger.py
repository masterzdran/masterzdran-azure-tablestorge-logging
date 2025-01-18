from datetime import datetime
import inspect
from enum import Enum
from typing import Dict, Any, Optional
import uuid
from .interfaces import LoggerInterface, StorageInterface
from .models import LogEntry

class LogLevel(Enum):
    """
    Enum representing log levels.
    """
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


class AzureLogger(LoggerInterface):
    """
    Logger implementation that stores logs in Azure Table Storage.
    """
    def __init__(self, storage: StorageInterface, logger_name: str, default_trace_id: str):
        """
        Initialize the AzureLogger.

        :param storage: The storage implementation to use for storing logs.
        :param logger_name: The name of the logger.
        :param default_trace_id: The default trace ID to use if none is provided.
        """
        self.storage = storage
        self.logger_name = logger_name
        self.default_trace_id = default_trace_id

    async def log(self, level: str, message: str, trace_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Log a message with a specific level.

        :param level: The log level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).
        :param message: The log message.
        :param trace_id: The trace ID for the log entry.
        :param metadata: Additional metadata for the log entry.
        """
        if not message:
            raise ValueError("Message cannot be empty")
        if trace_id is not None and not trace_id:
            raise ValueError("Trace ID cannot be empty")

        frame = inspect.currentframe().f_back
        location = f"{frame.f_code.co_filename}:{frame.f_lineno}"

        log_entry = {
            'LogLevel': level,
            'Message': message,
            'Timestamp': datetime.utcnow().isoformat(),
            'TraceId': trace_id or self.default_trace_id,
            'LoggerName': self.logger_name,
            'Location': location,
            'Metadata': metadata
        }
        partition_key = log_entry['TraceId']
        row_key = f"{log_entry['Timestamp']}_{level}"

        await self.storage.store_log(partition_key=partition_key, row_key=row_key, data=log_entry)

    async def debug(self, message: str, trace_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Log a debug message.

        :param message: The log message.
        :param trace_id: The trace ID for the log entry.
        :param metadata: Additional metadata for the log entry.
        """
        await self.log('DEBUG', message, trace_id, metadata)

    async def info(self, message: str, trace_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Log an info message.

        :param message: The log message.
        :param trace_id: The trace ID for the log entry.
        :param metadata: Additional metadata for the log entry.
        """
        await self.log('INFO', message, trace_id, metadata)

    async def warning(self, message: str, trace_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Log a warning message.

        :param message: The log message.
        :param trace_id: The trace ID for the log entry.
        :param metadata: Additional metadata for the log entry.
        """
        await self.log('WARNING', message, trace_id, metadata)

    async def error(self, message: str, trace_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Log an error message.

        :param message: The log message.
        :param trace_id: The trace ID for the log entry.
        :param metadata: Additional metadata for the log entry.
        """
        await self.log('ERROR', message, trace_id, metadata)

    async def critical(self, message: str, trace_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Log a critical message.

        :param message: The log message.
        :param trace_id: The trace ID for the log entry.
        :param metadata: Additional metadata for the log entry.
        """
        await self.log('CRITICAL', message, trace_id, metadata)