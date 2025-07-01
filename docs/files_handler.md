# files_handler.py

Utility functions for file path management, Google Drive link conversion, and logging file creation.

## Functions

### `get_root_path(APP_HEAD="main.py")`
- Walks up the directory tree to find the project root
- **Parameters:**
  - `APP_HEAD`: Marker file to identify the root directory (default: "main.py")
- **Returns:** Path to the root directory
- Uses LRU cache for performance

### `set_paths(APP_PATHS)`
- Updates the global application paths dictionary
- **Parameters:**
  - `APP_PATHS`: Dictionary containing application path mappings

### `get_paths()`
- Returns the current application paths dictionary
- Uses LRU cache for performance

### `set_namespace(namespace)`
- Sets a global namespace for organizing logs and files
- **Parameters:**
  - `namespace`: String identifier for the namespace

### `get_namespace()`
- Returns the current namespace
- Uses LRU cache for performance

### `get_direct_download_link(sharing_link)`
- Converts a Google Drive sharing link to a direct download link
- **Parameters:**
  - `sharing_link`: Google Drive sharing URL
- **Returns:** Direct download URL
- **Raises:** ValueError if file ID cannot be extracted

### `create_logfile(log_name)`
- Creates a log file in the designated logs directory
- **Parameters:**
  - `log_name`: Name for the log file (without extension)
- **Returns:** Full path to the created log file
- Automatically creates directory structure if needed

## Usage Example

```python
from common_utilities import get_root_path, set_paths, get_direct_download_link

# Get project root
root = get_root_path("app.py")

# Set application paths
set_paths({"LOGS_ROOT_PATH": "/var/logs"})

# Create a log file
log_path = create_logfile("application")

# Convert Google Drive link
direct_link = get_direct_download_link("https://drive.google.com/file/d/1ABC123/view")
```

## Installation

```python
from common_utilities import get_root_path, set_paths, get_direct_download_link
```

---
[Back to Main README](../README.md)
