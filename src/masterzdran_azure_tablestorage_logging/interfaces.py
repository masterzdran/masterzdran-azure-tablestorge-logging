"""
Interfaces for Azure Table Storage logging module.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class StorageInterface(ABC):
    """
    Abstract base class for storage interfaces.
    """

    @abstractmethod
    async def store_log(self, partition_key: str, row_key: str, data: Dict[str, Any]):
        """
        Store a log entry in the storage.

        :param partition_key: The partition key for the log entry.
        :param row_key: The row key for the log entry.
        :param data: A dictionary containing the log data.
        """
        raise NotImplementedError

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
        Retrieve logs from the storage.

        :param page_size: The number of logs to retrieve per page.
        :param continuation_token: The token to continue retrieving logs from where the
                                    last query left off.
        :param order_by: The field to order the logs by.
        :param ascending: Whether to order the logs in ascending order.
        :param filters: A dictionary of filters to apply to the query.
        :return: A tuple containing a list of logs and an optional continuation token.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_log_entry(
        self, partition_key: str, row_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single log entry from the storage.

        :param partition_key: The partition key of the log entry.
        :param row_key: The row key of the log entry.
        :return: A dictionary containing the log entry or None if not found.
        """
        raise NotImplementedError
