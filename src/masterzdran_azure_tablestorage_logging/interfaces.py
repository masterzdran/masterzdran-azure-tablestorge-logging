from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class StorageInterface(ABC):
    """
    Abstract base class for storage implementations.
    """

    @abstractmethod
    async def store_log(
        self, partition_key: str, row_key: str, data: Dict[str, Any]
    ) -> None:
        """
        Store a log entry in the storage.

        :param partition_key: The partition key for the log entry.
        :param row_key: The row key for the log entry.
        :param data: The log entry data.
        """
        pass

    @abstractmethod
    async def get_logs(
        self,
        page_size: int = 50,
        continuation_token: Optional[str] = None,
        order_by: str = "Timestamp",
        ascending: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Retrieve logs with pagination, ordering, and filtering capabilities.

        Args:
            page_size: Number of records per page
            continuation_token: Token for retrieving the next page
            order_by: Field to order results by
            ascending: Sort order (True for ascending, False for descending)
            filters: Dictionary of field-value pairs to filter results

        Returns:
            Tuple containing list of log entries and continuation token for next page
        """
        pass

    @abstractmethod
    async def get_log_entry(
        self, partition_key: str, row_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific log entry by its partition key and row key.

        Returns:
            Log entry as dictionary if found, None otherwise
        """
        pass


class LoggerInterface(ABC):
    """
    Abstract base class for logger implementations.
    """

    @abstractmethod
    async def log(self, level: str, message: str, **kwargs) -> None:
        """
        Log a message with a specific level.

        :param level: The log level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).
        :param message: The log message.
        :param kwargs: Additional keyword arguments for the log entry.
        """
        pass
