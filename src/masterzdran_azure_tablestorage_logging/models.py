"""
Models for Azure Table Storage logging module.
"""

from typing import Any, Dict


class LogEntry:
    """
    LogEntry is a class that represents a log entry.
    """

    def __init__(self, partition_key: str, row_key: str, data: Dict[str, Any]):
        """
        Initialize the LogEntry instance.

        :param partition_key: The partition key for the log entry.
        :param row_key: The row key for the log entry.
        :param data: A dictionary containing the log data.
        """
        self.partition_key = partition_key
        self.row_key = row_key
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the log entry to a dictionary.

        :return: A dictionary representation of the log entry.
        """
        return {"PartitionKey": self.partition_key, "RowKey": self.row_key, **self.data}

    def get_partition_key(self) -> str:
        """
        Get the partition key of the log entry.

        :return: The partition key of the log entry.
        """
        return self.partition_key
