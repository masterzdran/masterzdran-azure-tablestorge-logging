"""
Logger for Azure Table Storage logging module.
"""

import inspect
from datetime import datetime
from typing import Any, Dict, Optional

from .storage import AzureTableStorage


class LogLevel:
    """
    Log levels for the logger.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AzureLogger:
    """
    AzureLogger is a class that provides logging functionality using Azure Table Storage.
    """

    def __init__(
        self,
        storage: AzureTableStorage,
        logger_name: str,
        default_trace_id: Optional[str] = None,
    ):
        """
        Initialize the AzureLogger instance.

        :param storage: An instance of AzureTableStorage.
        :param logger_name: The name of the logger.
        :param default_trace_id: The default trace ID to use for log entries.
        """
        self.storage = storage
        self.logger_name = logger_name
        self.default_trace_id = default_trace_id

    async def _log(
        self,
        level: str,
        message: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log a message with the specified level.

        :param level: The log level.
        :param message: The log message.
        :param trace_id: The trace ID for the log entry.
        :param metadata: Additional metadata for the log entry.
        """
        if trace_id is None:
            trace_id = self.default_trace_id

        caller_frame = inspect.stack()[2]
        caller_module = inspect.getmodule(caller_frame[0])
        caller_location = f"{caller_module.__name__}:{caller_frame.lineno}"

        log_entry = {
            "LogLevel": level,
            "Message": message,
            "Timestamp": datetime.utcnow().isoformat(),
            "TraceId": trace_id,
            "LoggerName": self.logger_name,
            "Location": caller_location,
            "Metadata": metadata or {},
        }

        partition_key = self.logger_name
        row_key = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")

        await self.storage.store_log(partition_key, row_key, log_entry)

    async def debug(
        self,
        message: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log a debug message.

        :param message: The log message.
        :param trace_id: The trace ID for the log entry.
        :param metadata: Additional metadata for the log entry.
        """
        await self._log(LogLevel.DEBUG, message, trace_id, metadata)

    async def info(
        self,
        message: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log an info message.

        :param message: The log message.
        :param trace_id: The trace ID for the log entry.
        :param metadata: Additional metadata for the log entry.
        """
        await self._log(LogLevel.INFO, message, trace_id, metadata)

    async def warning(
        self,
        message: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log a warning message.

        :param message: The log message.
        :param trace_id: The trace ID for the log entry.
        :param metadata: Additional metadata for the log entry.
        """
        await self._log(LogLevel.WARNING, message, trace_id, metadata)

    async def error(
        self,
        message: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log an error message.

        :param message: The log message.
        :param trace_id: The trace ID for the log entry.
        :param metadata: Additional metadata for the log entry.
        """
        await self._log(LogLevel.ERROR, message, trace_id, metadata)

    async def critical(
        self,
        message: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Log a critical message.

        :param message: The log message.
        :param trace_id: The trace ID for the log entry.
        :param metadata: Additional metadata for the log entry.
        """
        await self._log(LogLevel.CRITICAL, message, trace_id, metadata)

    def get_logger_name(self) -> str:
        """
        Get the name of the logger.

        :return: The name of the logger.
        """
        return self.logger_name
