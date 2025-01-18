"""
Azure Table Storage logging module.
Provides methods to interact with Azure Table Storage for storing and retrieving logs.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.data.tables import TableServiceClient

from .interfaces import StorageInterface


class AzureTableStorage(StorageInterface):
    """
    AzureTableStorage is a class that provides methods to interact with Azure Table Storage.
    It implements the StorageInterface for storing and retrieving logs.
    """

    def __init__(self, connection_string: str, table_name: str):
        """
        Initialize the AzureTableStorage instance.

        :param connection_string: The connection string to the Azure Storage account.
        :param table_name: The name of the table to store logs.
        :raises ValueError: If connection_string or table_name is empty.
        """
        if not connection_string:
            raise ValueError("Connection string cannot be empty")
        if not table_name:
            raise ValueError("Table name cannot be empty")

        self.table_service_client = TableServiceClient.from_connection_string(
            connection_string
        )
        self.table_client = self.table_service_client.get_table_client(
            table_name=table_name
        )
        self.table_name = table_name
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        """
        Create the table if it does not already exist.
        """
        try:
            self.table_service_client.create_table(self.table_name)
        except ResourceExistsError:
            pass

    def _build_filter_string(self, filters: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Build an OData filter string from a dictionary of filters.

        :param filters: A dictionary of filters where keys are field names and values are the values to filter by.
        :return: An OData filter string or None if no filters are provided.
        :raises ValueError: If a filter value type is invalid.
        """
        if not filters:
            return None

        conditions = []
        for field, value in filters.items():
            if isinstance(value, str):
                conditions.append(f"{field} eq '{value}'")
            elif isinstance(value, (int, float)):
                conditions.append(f"{field} eq {value}")
            elif isinstance(value, bool):
                conditions.append(f"{field} eq {str(value).lower()}")
            else:
                raise ValueError(f"Invalid filter value type for field {field}")

        return " and ".join(conditions)

    async def store_log(self, partition_key: str, row_key: str, data: Dict[str, Any]):
        """
        Store a log entry in the table.

        :param partition_key: The partition key for the log entry.
        :param row_key: The row key for the log entry.
        :param data: A dictionary containing the log data.
        :raises ValueError: If partition_key, row_key, or data is invalid.
        :raises Exception: If storing the log entry fails.
        """
        if not partition_key:
            raise ValueError("Partition key cannot be empty")
        if not row_key:
            raise ValueError("Row key cannot be empty")
        if not data or "Message" not in data:
            raise ValueError("Invalid log data")

        entity = {
            "PartitionKey": partition_key,
            "RowKey": row_key,
            "LogLevel": data.get("LogLevel"),
            "Message": data.get("Message"),
            "Timestamp": data.get("Timestamp"),
            "TraceId": data.get("TraceId"),
            "LoggerName": data.get("LoggerName"),
            "Location": data.get("Location"),
            "Metadata": json.dumps(
                data.get("Metadata")
            ),  # Serialize Metadata to JSON string
        }

        try:
            self.table_client.create_entity(entity=entity)
        except Exception as e:
            raise Exception(f"Failed to store log: {str(e)}") from e

    async def get_logs(
        self,
        page_size: int = 50,
        continuation_token: Optional[str] = None,
        order_by: str = "Timestamp",
        ascending: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Retrieve logs from the table.

        :param page_size: The number of logs to retrieve per page.
        :param continuation_token: The token to continue retrieving logs from where the last query left off.
        :param order_by: The field to order the logs by.
        :param ascending: Whether to order the logs in ascending order.
        :param filters: A dictionary of filters to apply to the query.
        :return: A tuple containing a list of logs and an optional continuation token.
        :raises ValueError: If page_size is not positive or order_by is invalid.
        """
        if page_size <= 0:
            raise ValueError("Page size must be positive")

        valid_fields = {
            "Timestamp",
            "LogLevel",
            "TraceId",
            "LoggerName",
            "Location",
            "Message",
        }
        if order_by not in valid_fields:
            raise ValueError(f"Invalid order_by field. Must be one of {valid_fields}")

        # Build query parameters
        params = {"results_per_page": page_size}

        # Build filter string
        filter_string = self._build_filter_string(filters)
        if not filter_string:
            filter_string = "PartitionKey ne ''"  # Example filter to match all entities

        # Add select statement to include all columns
        params["select"] = [
            "PartitionKey",
            "RowKey",
            "LogLevel",
            "Timestamp",
            "TraceId",
            "LoggerName",
            "Location",
            "Message",
            "Metadata",
        ]

        # Execute query
        query_result = self.table_client.query_entities(
            query_filter=filter_string, **params
        )

        # Process results
        logs = []
        async for entity in query_result:
            logs.append(dict(entity))

        # Sort results
        logs.sort(key=lambda x: x.get(order_by, ""), reverse=not ascending)

        # Get continuation token for next page
        next_token = (
            getattr(query_result, "continuation_token", None)
            if len(logs) == page_size
            else None
        )

        return logs, next_token

    async def get_log_entry(
        self, partition_key: str, row_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single log entry from the table.

        :param partition_key: The partition key of the log entry.
        :param row_key: The row key of the log entry.
        :return: A dictionary containing the log entry or None if not found.
        :raises ValueError: If partition_key or row_key is empty.
        """
        if not partition_key:
            raise ValueError("Partition key cannot be empty")
        if not row_key:
            raise ValueError("Row key cannot be empty")

        try:
            entity = await self.table_client.get_entity(
                partition_key=partition_key, row_key=row_key
            )
            return dict(entity)
        except ResourceNotFoundError:
            return None
