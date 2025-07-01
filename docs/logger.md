# logger.py

A High level logging class with colored output, file logging, and custom filtering capabilities.

## Classes and Enums

### `LOG_LEVEL` (Enum)
- Defines logging levels: DEBUG, INFO, ERROR, CRITICAL, WARNING

### `Stream__ColoredFormatter`
- Formatter for colored console output
- Provides color-coded log levels for better readability

### `File__ColoredFormatter`
- Formatter for colored file output (though colors may not display in files)

### `loggingFilter`
- Custom filter that allows only DEBUG and ERROR logs
- Used for file logging to reduce log volume

## `LOGGER` Class

Main logging class that provides unified logging functionality.

### Methods

#### `__init__(logger_name)`
- Initializes a logger with the specified name
- **Parameters:**
  - `logger_name`: Name for the logger instance

#### `create_File_logger(logs_name: str)`
- Creates a file handler for logging to files
- **Parameters:**
  - `logs_name`: Name for the log file
- **Features:** Custom filtering (DEBUG and ERROR only), timestamped format

#### `create_Stream_logger()`
- Creates a console handler for colored terminal output
- **Features:** Colored output, INFO level and above

#### `write_logs(logs_message, logs_level: LOG_LEVEL)`
- Writes a log message with the specified level
- **Parameters:**
  - `logs_message`: Message to log
  - `logs_level`: LOG_LEVEL enum value

## Usage Example

```python
from common_utilities import LOGGER, LOG_LEVEL

# Create logger
logger = LOGGER("MyApplication")

# Setup file and console logging
logger.create_File_logger("app_logs")
logger.create_Stream_logger()

# Log messages
logger.write_logs("Application started", LOG_LEVEL.INFO)
logger.write_logs("Debug information", LOG_LEVEL.DEBUG)
logger.write_logs("An error occurred", LOG_LEVEL.ERROR)
```

## Color Scheme

The logger uses the following color scheme for different log levels:
- **DEBUG**: Cyan
- **INFO**: Green
- **WARNING**: Yellow
- **ERROR**: Red
- **CRITICAL**: Magenta

## File Logging

File logs include only DEBUG and ERROR levels to keep log files focused on important information while reducing noise.

## Installation

```python
from common_utilities import LOGGER, LOG_LEVEL
```

---
[Back to Main README](../README.md)
