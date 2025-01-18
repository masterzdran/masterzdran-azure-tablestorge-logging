from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

@dataclass
class LogEntry:
    log_level: str
    timestamp: datetime
    trace_id: str
    logger_name: str
    location: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'PartitionKey': self.trace_id,
            'RowKey': f"{self.timestamp.isoformat()}_{self.log_level}",
            'LogLevel': self.log_level,
            'Timestamp': self.timestamp.isoformat(),
            'TraceId': self.trace_id,
            'LoggerName': self.logger_name,
            'Location': self.location,
            'Message': self.message,
            'Metadata': str(self.metadata) if self.metadata else None
        }