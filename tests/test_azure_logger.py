from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.exceptions import ResourceNotFoundError
from azure.data.tables import TableClient, TableServiceClient

from masterzdran_azure_tablestorage_logging import AzureLogger, LogLevel
from masterzdran_azure_tablestorage_logging.interfaces import StorageInterface
from masterzdran_azure_tablestorage_logging.storage import AzureTableStorage


# Storage Test Fixtures
@pytest.fixture
def mock_table_client():
    client = MagicMock(spec=TableClient)
    client.create_entity = AsyncMock()
    client.query_entities = MagicMock()
    return client


@pytest.fixture
def mock_table_service():
    service = MagicMock(spec=TableServiceClient)
    service.get_table_client = MagicMock()
    return service


@pytest.fixture
async def azure_storage(mock_table_service, mock_table_client):
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
    def __init__(self):
        self.store_log = AsyncMock()
        self.get_logs = AsyncMock()
        self.get_log_entry = AsyncMock()

    async def store_log(self, partition_key: str, row_key: str, data: dict) -> None:
        if not data or "Message" not in data:
            raise ValueError("Invalid log data")

    async def get_logs(
        self,
        page_size: int = 50,
        continuation_token: Optional[str] = None,
        order_by: str = "Timestamp",
        ascending: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        pass

    async def get_log_entry(
        self, partition_key: str, row_key: str
    ) -> Optional[Dict[str, Any]]:
        pass


@pytest.fixture
def mock_storage():
    return MockStorage()


@pytest.fixture
def logger(mock_storage):
    return AzureLogger(
        storage=mock_storage,
        logger_name="test_logger",
        default_trace_id="test-trace-id",
    )


# Storage Tests
@pytest.mark.asyncio
async def test_storage_initialization(azure_storage):
    storage, _ = await azure_storage
    assert storage.table_name == "logs"
    assert storage.table_client is not None


@pytest.mark.asyncio
async def test_storage_connection_validation():
    with pytest.raises(ValueError, match="Connection string cannot be empty"):
        AzureTableStorage(connection_string="", table_name="logs")

    with pytest.raises(ValueError, match="Table name cannot be empty"):
        AzureTableStorage(
            connection_string="DefaultEndpointsProtocol=https;AccountName=devstoreaccount1;AccountKey=key;",
            table_name="",
        )


@pytest.mark.asyncio
async def test_storage_store_log_basic(azure_storage):
    storage, mock_client = await azure_storage

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
    storage, mock_client = await azure_storage

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
    storage, mock_client = await azure_storage

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
    storage, mock_client = await azure_storage

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
async def test_logger_levels(logger, mock_storage):
    message = "Test message"

    await logger.debug(message)
    assert "DEBUG" in mock_storage.store_log.call_args[1]["data"]["LogLevel"]

    await logger.info(message)
    assert "INFO" in mock_storage.store_log.call_args[1]["data"]["LogLevel"]

    await logger.warning(message)
    assert "WARNING" in mock_storage.store_log.call_args[1]["data"]["LogLevel"]

    await logger.error(message)
    assert "ERROR" in mock_storage.store_log.call_args[1]["data"]["LogLevel"]

    await logger.critical(message)
    assert "CRITICAL" in mock_storage.store_log.call_args[1]["data"]["LogLevel"]


@pytest.mark.asyncio
async def test_logger_trace_id_handling(logger, mock_storage):
    message = "Test with custom trace"
    custom_trace = "custom-trace-id"

    await logger.info(message, trace_id=custom_trace)
    _, kwargs = mock_storage.store_log.call_args
    assert kwargs["data"]["TraceId"] == custom_trace

    await logger.info(message)  # Using default trace_id
    _, kwargs = mock_storage.store_log.call_args
    assert kwargs["data"]["TraceId"] == "test-trace-id"


@pytest.mark.asyncio
async def test_logger_error_handling(logger, mock_storage):
    mock_storage.store_log.side_effect = Exception("Storage error")

    with pytest.raises(Exception, match="Storage error"):
        await logger.info("Test message")


@pytest.mark.asyncio
async def test_logger_input_validation(logger):
    # Test empty message
    with pytest.raises(ValueError, match="Message cannot be empty"):
        await logger.info("")

    # Test None message
    with pytest.raises(ValueError, match="Message cannot be empty"):
        await logger.info(None)

    # Test invalid trace_id
    with pytest.raises(ValueError, match="Trace ID cannot be empty"):
        await logger.info("Test", trace_id="")


@pytest.mark.asyncio
async def test_get_logs_pagination(azure_storage):
    storage, mock_client = await azure_storage

    # Prepare mock data
    mock_entries = [
        {
            "PartitionKey": "trace1",
            "RowKey": "2024-01-17T12:00:00_INFO",
            "LogLevel": "INFO",
            "Message": "Test message 1",
            "Timestamp": "2024-01-17T12:00:00",
            "TraceId": "trace1",
            "LoggerName": "test_logger",
            "Location": "test_location",
        },
        {
            "PartitionKey": "trace1",
            "RowKey": "2024-01-17T12:01:00_INFO",
            "LogLevel": "INFO",
            "Message": "Test message 2",
            "Timestamp": "2024-01-17T12:01:00",
            "TraceId": "trace1",
            "LoggerName": "test_logger",
            "Location": "test_location",
        },
    ]

    # Configure mock
    mock_query_result = AsyncMock()
    mock_query_result.__aiter__.return_value = mock_entries
    mock_query_result.continuation_token = "next_page_token"
    mock_client.query_entities.return_value = mock_query_result

    # Get first page with explicit ascending order
    logs, next_token = await storage.get_logs(page_size=2, ascending=True)

    # Verify results
    assert len(logs) == 2
    assert logs[0]["Message"] == "Test message 1"
    assert logs[1]["Message"] == "Test message 2"
    assert next_token == "next_page_token"

    # Test descending order
    logs, next_token = await storage.get_logs(page_size=2, ascending=False)

    # Verify results are in reverse order
    assert len(logs) == 2
    assert logs[0]["Message"] == "Test message 2"
    assert logs[1]["Message"] == "Test message 1"
    assert next_token == "next_page_token"


@pytest.mark.asyncio
async def test_get_logs_with_filters(azure_storage):
    storage, mock_client = await azure_storage

    # Configure mock
    mock_query_result = AsyncMock()
    mock_query_result.__aiter__.return_value = []
    mock_query_result.continuation_token = None
    mock_client.query_entities.return_value = mock_query_result

    # Test with multiple filters
    filters = {"LogLevel": "ERROR", "TraceId": "trace1", "LoggerName": "test_logger"}

    await storage.get_logs(filters=filters)

    # Verify filter string construction
    call_args = mock_client.query_entities.call_args[1]
    filter_str = call_args["filter"]

    assert "LogLevel eq 'ERROR'" in filter_str
    assert "TraceId eq 'trace1'" in filter_str
    assert "LoggerName eq 'test_logger'" in filter_str


@pytest.mark.asyncio
async def test_get_logs_ordering(azure_storage):
    storage, mock_client = await azure_storage

    # Prepare mock data
    mock_entries = [
        {"Timestamp": "2024-01-17T12:00:00", "Message": "Message 1"},
        {"Timestamp": "2024-01-17T12:01:00", "Message": "Message 2"},
    ]

    mock_query_result = AsyncMock()
    mock_query_result.__aiter__.return_value = mock_entries
    mock_query_result.continuation_token = None
    mock_client.query_entities.return_value = mock_query_result

    # Test ascending order
    logs_asc, _ = await storage.get_logs(order_by="Timestamp", ascending=True)
    assert logs_asc[0]["Timestamp"] < logs_asc[1]["Timestamp"]

    # Test descending order
    logs_desc, _ = await storage.get_logs(order_by="Timestamp", ascending=False)
    assert logs_desc[0]["Timestamp"] > logs_desc[1]["Timestamp"]


@pytest.mark.asyncio
async def test_get_log_entry_success(azure_storage):
    storage, mock_client = await azure_storage

    # Prepare mock data
    mock_entry = {
        "PartitionKey": "trace1",
        "RowKey": "2024-01-17T12:00:00_INFO",
        "LogLevel": "INFO",
        "Message": "Test message",
        "Timestamp": "2024-01-17T12:00:00",
        "TraceId": "trace1",
        "LoggerName": "test_logger",
        "Location": "test_location",
    }

    mock_client.get_entity = AsyncMock(return_value=mock_entry)

    # Test successful retrieval
    result = await storage.get_log_entry("trace1", "2024-01-17T12:00:00_INFO")

    assert result == mock_entry
    mock_client.get_entity.assert_called_once_with(
        partition_key="trace1", row_key="2024-01-17T12:00:00_INFO"
    )


@pytest.mark.asyncio
async def test_get_log_entry_not_found(azure_storage):
    storage, mock_client = await azure_storage

    mock_client.get_entity = AsyncMock(side_effect=ResourceNotFoundError())

    result = await storage.get_log_entry("trace1", "non_existent")

    assert result is None
    mock_client.get_entity.assert_called_once_with(
        partition_key="trace1", row_key="non_existent"
    )


@pytest.mark.asyncio
async def test_get_logs_invalid_parameters(azure_storage):
    storage, _ = await azure_storage

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
    storage, _ = await azure_storage

    with pytest.raises(ValueError, match="Partition key cannot be empty"):
        await storage.get_log_entry("", "row_key")

    with pytest.raises(ValueError, match="Row key cannot be empty"):
        await storage.get_log_entry("partition_key", "")

    with pytest.raises(ValueError, match="Partition key cannot be empty"):
        await storage.get_log_entry(None, "row_key")
