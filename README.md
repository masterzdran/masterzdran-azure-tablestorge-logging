# Masterzdran Azure Table Storage Logging

A professional Python logging module that uses Azure Table Storage for structured logging with support for trace IDs, metadata, and different log levels.

## Features

- Asynchronous logging using Azure Table Storage
- Structured logging with comprehensive metadata
- Trace ID support for request tracking
- Automatic caller location tracking
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Dependency injection for flexible storage backends
- Full type hinting support
- Comprehensive test coverage

## Installation

Install the package using pip:

```bash
pip install azure-logger
```

For development installation:

```bash
pip install -e .[dev]
```

## Quick Start

```python
from azure_logger import AzureLogger
from azure_logger.storage import AzureTableStorage

# Initialize the storage
storage = AzureTableStorage(
    connection_string="your_azure_connection_string",
    table_name="logs"
)

# Create a logger instance
logger = AzureLogger(
    storage=storage,
    logger_name="my_service"
)

# Log messages with different levels
await logger.info("Operation completed", 
    metadata={"user_id": "123", "action": "login"})
await logger.error("Operation failed",
    trace_id="custom-trace",
    metadata={"error_code": "AUTH001"})
```

## Configuration

The logger can be configured with the following parameters:

```python
logger = AzureLogger(
    storage=storage,
    logger_name="my_service",
    default_trace_id="custom-default-trace"  # Optional
)
```

## Log Levels

- DEBUG: Detailed information for debugging
- INFO: General information about program execution
- WARNING: Indicates a potential problem
- ERROR: A more serious problem
- CRITICAL: A critical problem that may prevent program execution

## Development

### Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/azure-logger.git
cd azure-logger
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e .[dev]
```

### Running Tests

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src --cov-report=html
```

### Code Quality

Run code quality checks:
```bash
black .              # Code formatting
isort .             # Import sorting
pylint src/ tests/  # Linting
mypy src/           # Type checking
```

### Building the Package

1. Install build dependencies:
```bash
pip install build wheel
```

2. Build the package:
```bash
python -m build
```

### Publishing

1. Install publishing dependencies:
```bash
pip install twine
```

2. Upload to PyPI:
```bash
twine upload dist/*
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security

For security concerns, please email masterzdran@gmail.com