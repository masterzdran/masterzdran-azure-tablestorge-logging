import json
from typing import Dict, Any, List, Optional, Tuple
from azure.data.tables import TableServiceClient, TableClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

from .interfaces import StorageInterface


class AzureTableStorage(StorageInterface):
    def __init__(self, connection_string: str, table_name: str):
        if not connection_string:
            raise ValueError("Connection string cannot be empty")
        if not table_name:
            raise ValueError("Table name cannot be empty")
        
        self.table_service_client = TableServiceClient.from_connection_string(connection_string)
        self.table_client = self.table_service_client.get_table_client(table_name=table_name)
        self.table_name = table_name
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        try:
            self.table_service_client.create_table(self.table_name)
        except ResourceExistsError:
            pass

    def _build_filter_string(self, filters: Optional[Dict[str, Any]]) -> Optional[str]:
        """Build OData filter string from dictionary of filters."""
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
        if not partition_key:
            raise ValueError("Partition key cannot be empty")
        if not row_key:
            raise ValueError("Row key cannot be empty")
        if not data or 'Message' not in data:
            raise ValueError("Invalid log data")

        entity = {
            'PartitionKey': partition_key,
            'RowKey': row_key,
            'LogLevel': data.get('LogLevel'),
            'Message': data.get('Message'),
            'Timestamp': data.get('Timestamp'),
            'TraceId': data.get('TraceId'),
            'LoggerName': data.get('LoggerName'),
            'Location': data.get('Location'),
            'Metadata': json.dumps(data.get('Metadata'))  # Serialize Metadata to JSON string
        }

        try:
            self.table_client.create_entity(entity=entity)
        except Exception as e:
            raise Exception(f"Failed to store log: {str(e)}")

    async def get_logs(
        self,
        page_size: int = 50,
        continuation_token: Optional[str] = None,
        order_by: str = "Timestamp",
        ascending: bool = False,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        if page_size <= 0:
            raise ValueError("Page size must be positive")
            
        valid_fields = {'Timestamp', 'LogLevel', 'TraceId', 'LoggerName', 'Location', 'Message'}
        if order_by not in valid_fields:
            raise ValueError(f"Invalid order_by field. Must be one of {valid_fields}")

        # Build query parameters
        params = {
            'results_per_page': page_size
        }
        
        # Build filter string
        filter_string = self._build_filter_string(filters)
        if not filter_string:
            filter_string = "PartitionKey ne ''"

            
        # Add select statement to include all columns
        params['select'] = ['PartitionKey', 'RowKey', 'LogLevel', 'Timestamp', 
                          'TraceId', 'LoggerName', 'Location', 'Message', 'Metadata']

        # # Execute query
        # query_result = self.table_client.query_entities(**params)
        # Execute query
        query_result = self.table_client.query_entities(query_filter=filter_string, **params)
        
        # Process results
        logs = []
        for entity in query_result:
            logs.append(dict(entity))
            
        # Sort results
        logs.sort(
            key=lambda x: x.get(order_by, ''),
            reverse=not ascending
        )
        
        # Get continuation token for next page
        next_token = getattr(query_result, 'continuation_token', None) if len(logs) == page_size else None
        
        return logs, next_token
    
    async def get_log_entry(
        self,
        partition_key: str,
        row_key: str
    ) -> Optional[Dict[str, Any]]:
        if not partition_key:
            raise ValueError("Partition key cannot be empty")
        if not row_key:
            raise ValueError("Row key cannot be empty")

        try:
            entity = await self.table_client.get_entity(
                partition_key=partition_key,
                row_key=row_key
            )
            return dict(entity)
        except ResourceNotFoundError:
            return None