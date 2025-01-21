from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.exceptions import ResourceNotFoundError
from azure.data.tables import TableClient, TableServiceClient
import pytest_asyncio

from masterzdran_azure_tablestorage_logging import AzureLogger, LogLevel
from masterzdran_azure_tablestorage_logging.interfaces import StorageInterface
from masterzdran_azure_tablestorage_logging.storage import AzureTableStorage

# Storage Test Fixtures
@pytest_asyncio.fixture
def mock_table_client():
    """
    Fixture for mocking TableClient.
    """
    client = MagicMock(spec=TableClient)
    client.create_entity = AsyncMock()
    client.query_entities = MagicMock()
    return client


@pytest_asyncio.fixture
def mock_table_service():
    """
    Fixture for mocking TableServiceClient.
    """
    service = MagicMock(spec=TableServiceClient)
    service.get_table_client = MagicMock()
    return service


@pytest_asyncio.fixture
async def azure_storage(mock_table_service, mock_table_client):
    """
    Fixture for initializing AzureTableStorage with mocked services.
    """
    with patch(
        "masterzdran_azure_tablestorage_logging.storage.TableServiceClient.from_connection_string",
        return_value=mock_table_service,
    ):
        mock_table_service.get_table_client.return_value = mock_table_client
        storage = AzureTableStorage(
            connection_string="DefaultEndpointsProtocol=https;AccountName=devstoreaccount1;AccountKey=key;",
            table_name="logs",
        )
        return storage, mock_table_client


class MockStorage(StorageInterface):
    """
    Mock implementation of StorageInterface for testing.
    """

    def __init__(self):
        self.store_log = AsyncMock()
        self.get_logs = AsyncMock()
        self.get_log_entry = AsyncMock()

    async def store_log(self, partition_key: str, row_key: str, data: dict) -> None:
        if not data or "Message" not in data:
            raise ValueError("Invalid log data")
        self.store_log.call_args = ((), {"partition_key": partition_key, "row_key": row_key, "data": data})

    def get_logs(
        self,
        page_size: int = 50,
        continuation_token: Optional[str] = None,
        order_by: str = "Timestamp",
        ascending: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        self.get_logs.call_args = ((), {"page_size": page_size, "continuation_token": continuation_token, "order_by": order_by, "ascending": ascending, "filters": filters})
        return [], None

    def get_log_entry(
        self, partition_key: str, row_key: str
    ) -> Optional[Dict[str, Any]]:
        pass


@pytest_asyncio.fixture
def mock_storage():
    """
    Fixture for initializing MockStorage.
    """
    return MockStorage()


@pytest_asyncio.fixture
def logger(mock_storage):
    """
    Fixture for initializing AzureLogger with MockStorage.
    """
    return AzureLogger(
        storage=mock_storage,
        logger_name="test_logger",
        default_trace_id="test-trace-id",
    )


# Storage Tests
@pytest.mark.asyncio
async def test_storage_initialization(azure_storage):
    """
    Test AzureTableStorage initialization.
    """
    storage, _ = azure_storage
    assert storage.table_name == "logs"
    assert storage.table_client is not None


@pytest.mark.asyncio
async def test_storage_connection_validation():
    """
    Test AzureTableStorage connection string and table name validation.
    """
    with pytest.raises(ValueError, match="Connection string cannot be empty"):
        AzureTableStorage(connection_string="", table_name="logs")

    with pytest.raises(ValueError, match="Table name cannot be empty"):
        AzureTableStorage(
            connection_string="DefaultEndpointsProtocol=https;AccountName=devstoreaccount1;AccountKey=key;",
            table_name="",
        )


@pytest.mark.asyncio
async def test_storage_store_log_basic(azure_storage):
    """
    Test storing a basic log entry in AzureTableStorage.
    """
    storage, mock_client = azure_storage

    test_data = {
        "LogLevel": "INFO",
        "Message": "Test message",
        "Timestamp": datetime.utcnow().isoformat(),
        "TraceId": "test-trace",
        "LoggerName": "test_logger",
        "Location": "test_location",
    }

    await storage.store_log(
        partition_key="test-trace", row_key="2024-01-17T12:00:00_INFO", data=test_data
    )

    mock_client.create_entity.assert_called_once()
    call_args = mock_client.create_entity.call_args[1]
    assert call_args["entity"]["PartitionKey"] == "test-trace"
    assert call_args["entity"]["RowKey"] == "2024-01-17T12:00:00_INFO"
    assert call_args["entity"]["LogLevel"] == "INFO"
    assert call_args["entity"]["Message"] == "Test message"


@pytest.mark.asyncio
async def test_storage_store_log_with_metadata(azure_storage):
    """
    Test storing a log entry with metadata in AzureTableStorage.
    """
    storage, mock_client = azure_storage

    metadata = {"user_id": "123", "action": "login"}
    test_data = {
        "LogLevel": "INFO",
        "Message": "Test with metadata",
        "Timestamp": datetime.utcnow().isoformat(),
        "TraceId": "test-trace",
        "LoggerName": "test_logger",
        "Location": "test_location",
        "Metadata": metadata,
    }

    await storage.store_log(
        partition_key="test-trace", row_key="2024-01-17T12:00:00_INFO", data=test_data
    )

    call_args = mock_client.create_entity.call_args[1]
    assert "user_id" in call_args["entity"]["Metadata"]
    assert "action" in call_args["entity"]["Metadata"]


@pytest.mark.asyncio
async def test_storage_store_log_with_special_characters(azure_storage):
    """
    Test storing a log entry with special characters in AzureTableStorage.
    """
    storage, mock_client = azure_storage

    test_data = {
        "LogLevel": "INFO",
        "Message": "Test message with special chars: !@#$%^&*()",
        "Timestamp": datetime.utcnow().isoformat(),
        "TraceId": "test-trace",
        "LoggerName": "test_logger",
        "Location": "test_location",
    }

    await storage.store_log(
        partition_key="test-trace", row_key="2024-01-17T12:00:00_INFO", data=test_data
    )

    call_args = mock_client.create_entity.call_args[1]
    assert call_args["entity"]["Message"] == test_data["Message"]


@pytest.mark.asyncio
async def test_storage_store_log_data_validation(azure_storage):
    """
    Test data validation when storing a log entry in AzureTableStorage.
    """
    storage, _ = azure_storage

    # Test with empty data
    with pytest.raises(ValueError):
        await storage.store_log(partition_key="test-trace", row_key="test-key", data={})

    # Test with None data
    with pytest.raises(ValueError):
        await storage.store_log(
            partition_key="test-trace", row_key="test-key", data=None
        )

    # Test with invalid data types
    with pytest.raises(ValueError):
        await storage.store_log(
            partition_key="test-trace",
            row_key="test-key",
            data={"invalid_type": object()},
        )




@pytest.mark.asyncio
async def test_logger_error_handling(logger, mock_storage):
    """
    Test error handling in AzureLogger.
    """
    mock_storage.store_log.side_effect = Exception("Storage error")

    with pytest.raises(Exception, match="Storage error"):
        await logger.info("Test message")



@pytest.mark.asyncio
async def test_get_logs_invalid_parameters(azure_storage):
    """
    Test invalid parameters when retrieving logs from AzureTableStorage.
    """
    storage, _ = azure_storage

    # Test invalid page size
    with pytest.raises(ValueError, match="Page size must be positive"):
        await storage.get_logs(page_size=0)

    # Test invalid order_by field
    with pytest.raises(ValueError, match="Invalid order_by field"):
        await storage.get_logs(order_by="InvalidField")

    # Test invalid filter value type
    with pytest.raises(ValueError, match="Invalid filter value type"):
        await storage.get_logs(filters={"LogLevel": object()})


@pytest.mark.asyncio
async def test_get_log_entry_invalid_keys(azure_storage):
    """
    Test invalid partition key and row key when retrieving a log entry from AzureTableStorage.
    """
    storage, _ = azure_storage

    with pytest.raises(ValueError, match="Partition key cannot be empty"):
        await storage.get_log_entry("", "row_key")

    with pytest.raises(ValueError, match="Row key cannot be empty"):
        await storage.get_log_entry("partition_key", "")

    with pytest.raises(ValueError, match="Partition key cannot be empty"):
        await storage.get_log_entry(None, "row_key")

