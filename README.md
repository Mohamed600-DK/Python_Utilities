# Python Utilities

A collection of custom Python utility classes and functions designed to streamline common development tasks across different projects. This repository includes utilities for multiprocessing, threading, file handling, GPU monitoring, image preprocessing, logging, and Redis operations.

## Installation

### Option 1: Install via pip (Recommended)

Install the package directly from the repository:

```bash
pip install git+https://github.com/Mohamed600-DK/Python_Utilities.git
```

### Option 2: Install via uv (Fast Python Package Manager)

If you're using [uv](https://github.com/astral-sh/uv), you can install it with:

```bash
uv add git+https://github.com/Mohamed600-DK/Python_Utilities.git
```

### Option 3: Development Installation

For development or if you want to modify the code:

```bash
git clone https://github.com/Mohamed600-DK/Python_Utilities.git
cd Python_Utilities
pip install -e .  
```

or with uv:

```bash
git clone https://github.com/Mohamed600-DK/Python_Utilities.git
cd Python_Utilities
uv pip install -e .
```

### Option 4: Clone as Submodule

To use this repository as a git submodule in your project:

```bash
git clone https://github.com/Mohamed600-DK/Python_Utilities.git common
```

or

```bash
git clone https://github.com/Mohamed600-DK/Python_Utilities.git utilities/common
```

## Requirements

The package automatically installs the following dependencies:
- `numpy>=2.2.6` for numerical operations
- `opencv-python>=4.11.0.86` for image preprocessing
- `Pillow>=11.2.1` for image handling
- `pynvml>=12.0.0` for GPU monitoring
- `redis>=6.2.0` for Redis operations

**Python Version**: Requires Python 3.10 or higher

## Quick Start

After installation, you can import and use the utilities:

```python
from common_utilities import LOGGER, LOG_LEVEL, Base_process, get_available_gpu_index

# Create a logger
logger = LOGGER("MyApp")
logger.create_Stream_logger()
logger.write_logs("Hello from common utilities!", LOG_LEVEL.INFO)

# Check for available GPU
gpu_index = get_available_gpu_index()
if gpu_index is not None:
    print(f"Available GPU: {gpu_index}")
```

## Modules Overview

### Base_Processing.py

A robust multiprocessing framework that provides an abstract base class for creating and managing multiprocess applications with shared data, events, and notifications.

#### `Base_process` Class

An abstract base class that extends `multiprocessing.Process` to provide enhanced multiprocessing capabilities.

**Methods:**

- **`__init__(process_name: str, process_arg: Tuple=None)`**
  - Initializes a new process with a given name and optional arguments
  - Parameters:
    - `process_name`: String identifier for the process
    - `process_arg`: Optional tuple of arguments to pass to the process

- **`Start_process()`**
  - Starts the process execution

- **`Stop_process()`**
  - Sets the stop flag to gracefully terminate the process

- **`Join_process()`**
  - Waits for the process to complete

- **`run(*process_arg)`** *(Abstract)*
  - Must be implemented by subclasses to define the process logic

**Class Methods for Shared Resources:**

- **`set_sherd_variables(sherd_process_data, sherd_process_notification, sherd_process_data_evens)`**
  - Sets up shared variables for inter-process communication
  - Parameters:
    - `sherd_process_data`: Dictionary of shared data structures
    - `sherd_process_notification`: Dictionary of condition objects
    - `sherd_process_data_evens`: Dictionary of event objects

- **`get_processes_data(data_name: str)`**
  - Retrieves data from shared storage (thread-safe)
  - Returns: Data value or None if queue is empty

- **`save_processes_data(data_name: str, data_value: Any)`**
  - Saves data to shared storage (thread-safe)
  - Supports dictionaries, lists, sets, and queues

- **`get_processes_events(event_name: str)`**
  - Returns a multiprocessing Event object for synchronization

- **`create_processes_events(event_name: str)`**
  - Creates a new Event if it doesn't exist

- **`get_processes_notifications(notify_name: str)`**
  - Returns a multiprocessing Condition object for notifications

- **`create_processes_notifications(notification_name: str)`**
  - Creates a new Condition object if it doesn't exist

**Usage Example:**
```python
from Base_Processing import Base_process

class MyProcess(Base_process):
    def run(self, *args):
        while not self.stop_process:
            # Your process logic here
            data = self.get_processes_data("input_queue")
            if data:
                # Process the data
                self.save_processes_data("output_queue", processed_data)

# Initialize shared resources
shared_data = {"input_queue": Queue(), "output_queue": Queue()}
shared_events = {}
shared_notifications = {}
Base_process.set_sherd_variables(shared_data, shared_notifications, shared_events)

# Create and start process
process = MyProcess("worker_process")
process.Start_process()
```

### Base_Threading.py

A simplified threading framework that provides an abstract base class for creating thread-based applications with shared resources.

#### `Base_Thread` Class

An abstract base class for creating and managing threaded applications.

**Class Attributes:**
- `threads_events`: Dictionary of threading Event objects
- `threads_notifications`: Dictionary of threading Condition objects  
- `threads_data`: Dictionary of Queue objects for thread communication

**Methods:**

- **`__init__(thread_name: str, thread_arg: Tuple=())`**
  - Initializes a new thread with a given name and optional arguments
  - Parameters:
    - `thread_name`: String identifier for the thread
    - `thread_arg`: Optional tuple of arguments to pass to the thread

- **`Start_thread()`**
  - Starts the thread execution

- **`Stop_thread()`**
  - Sets the stop flag to gracefully terminate the thread

- **`Join_thread()`**
  - Waits for the thread to complete

- **`run()`** *(Abstract)*
  - Must be implemented by subclasses to define the thread logic

**Usage Example:**
```python
from Base_Threading import Base_Thread

class MyThread(Base_Thread):
    def run(self):
        while not self.stop_thread:
            # Your thread logic here
            pass

# Create and start thread
thread = MyThread("worker_thread")
thread.Start_thread()
```

### files_handler.py

Utility functions for file path management, Google Drive link conversion, and logging file creation.

#### Functions

- **`get_root_path(APP_HEAD="main.py")`**
  - Walks up the directory tree to find the project root
  - Parameters:
    - `APP_HEAD`: Marker file to identify the root directory (default: "main.py")
  - Returns: Path to the root directory
  - Uses LRU cache for performance

- **`set_paths(APP_PATHS)`**
  - Updates the global application paths dictionary
  - Parameters:
    - `APP_PATHS`: Dictionary containing application path mappings

- **`get_paths()`**
  - Returns the current application paths dictionary
  - Uses LRU cache for performance

- **`set_namespace(namespace)`**
  - Sets a global namespace for organizing logs and files
  - Parameters:
    - `namespace`: String identifier for the namespace

- **`get_namespace()`**
  - Returns the current namespace
  - Uses LRU cache for performance

- **`get_direct_download_link(sharing_link)`**
  - Converts a Google Drive sharing link to a direct download link
  - Parameters:
    - `sharing_link`: Google Drive sharing URL
  - Returns: Direct download URL
  - Raises: ValueError if file ID cannot be extracted

- **`create_logfile(log_name)`**
  - Creates a log file in the designated logs directory
  - Parameters:
    - `log_name`: Name for the log file (without extension)
  - Returns: Full path to the created log file
  - Automatically creates directory structure if needed

**Usage Example:**
```python
from files_handler import get_root_path, set_paths, create_logfile

# Get project root
root = get_root_path("app.py")

# Set application paths
set_paths({"LOGS_ROOT_PATH": "/var/logs"})

# Create a log file
log_path = create_logfile("application")

# Convert Google Drive link
direct_link = get_direct_download_link("https://drive.google.com/file/d/1ABC123/view")
```

### GPUs_Monitor.py

GPU monitoring utilities for finding available GPU resources based on memory usage.

#### Functions

- **`get_available_gpu_index(current_gpu_index=0, threshold=0.8)`**
  - Finds the first available GPU with memory usage below the threshold
  - Parameters:
    - `current_gpu_index`: Starting GPU index to check (default: 0)
    - `threshold`: Memory usage threshold (0.0-1.0, default: 0.8)
  - Returns: GPU index if available, None if no GPU meets criteria
  - Requires: `pynvml` library for NVIDIA GPU monitoring

**Usage Example:**
```python
from GPUs_Monitor import get_available_gpu_index

# Find GPU with less than 80% memory usage
gpu_index = get_available_gpu_index()
if gpu_index is not None:
    print(f"Available GPU: {gpu_index}")
    # Set your ML framework to use this GPU
else:
    print("No available GPU found")

# Find GPU starting from index 1 with 50% threshold
gpu_index = get_available_gpu_index(current_gpu_index=1, threshold=0.5)
```

### image_preprocessing.py

Image processing utilities for cropping and format conversion operations.

#### Functions

- **`crop_image_bbox(image, face_bbox, box_size=280)`**
  - Crops a square region centered on a bounding box
  - Parameters:
    - `image`: Input image as numpy array or cv2.Mat
    - `face_bbox`: List [x1, y1, x2, y2] defining the bounding box
    - `box_size`: Size of the square crop (default: 280)
  - Returns: Cropped image as PIL Image
  - Ensures the crop stays within image boundaries

- **`crop_image_center(frame, crop_width=None, crop_height=None)`**
  - Crops a region from the center of an image
  - Parameters:
    - `frame`: Input image/frame
    - `crop_width`: Width of crop (default: original width)
    - `crop_height`: Height of crop (default: original width)
  - Returns: Cropped frame
  - Automatically handles boundary constraints

- **`encoded64image2cv2(ImageBase64: str)`**
  - Converts a base64 encoded image string to OpenCV format
  - Parameters:
    - `ImageBase64`: Base64 encoded image string
  - Returns: OpenCV image (cv2.Mat) or None if input is None
  - Handles the complete decode pipeline from base64 to cv2 format

**Usage Example:**
```python
import cv2
from image_preprocessing import crop_image_bbox, crop_image_center, encoded64image2cv2

# Load an image
image = cv2.imread("photo.jpg")

# Crop around a detected face
face_bbox = [100, 100, 200, 200]  # x1, y1, x2, y2
cropped_face = crop_image_bbox(image, face_bbox, box_size=224)

# Crop center region
center_crop = crop_image_center(image, crop_width=300, crop_height=300)

# Convert base64 to cv2
base64_string = "your_base64_image_string"
cv2_image = encoded64image2cv2(base64_string)
```

### logger.py

A comprehensive logging system with colored output, file logging, and custom filtering capabilities.

#### Classes and Enums

- **`LOG_LEVEL` (Enum)**
  - Defines logging levels: DEBUG, INFO, ERROR, CRITICAL, WARNING

- **`Stream__ColoredFormatter`**
  - Formatter for colored console output
  - Provides color-coded log levels for better readability

- **`File__ColoredFormatter`**
  - Formatter for colored file output (though colors may not display in files)

- **`loggingFilter`**
  - Custom filter that allows only DEBUG and ERROR logs
  - Used for file logging to reduce log volume

#### `LOGGER` Class

Main logging class that provides unified logging functionality.

**Methods:**

- **`__init__(logger_name)`**
  - Initializes a logger with the specified name
  - Parameters:
    - `logger_name`: Name for the logger instance

- **`create_File_logger(logs_name: str)`**
  - Creates a file handler for logging to files
  - Parameters:
    - `logs_name`: Name for the log file
  - Features: Custom filtering (DEBUG and ERROR only), timestamped format

- **`create_Stream_logger()`**
  - Creates a console handler for colored terminal output
  - Features: Colored output, INFO level and above

- **`write_logs(logs_message, logs_level: LOG_LEVEL)`**
  - Writes a log message with the specified level
  - Parameters:
    - `logs_message`: Message to log
    - `logs_level`: LOG_LEVEL enum value

**Usage Example:**
```python
from logger import LOGGER, LOG_LEVEL

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

### RedisHandler.py

A Redis wrapper class that provides simplified operations with automatic serialization using pickle.

#### `RedisHandler` Class

Provides high-level Redis operations with automatic pickle serialization.

**Environment Variables:**
- `REDIS_HOSTNAME`: Redis server hostname (default: localhost)
- `REDIS_HOSTPORT`: Redis server port (default: 6379)

**Methods:**

- **`__init__(host="localhost", port=6379, db=0)`**
  - Initializes Redis connection
  - Uses environment variables if available
  - Parameters:
    - `host`: Redis server host
    - `port`: Redis server port
    - `db`: Redis database number

- **`set_value(key, value)`**
  - Stores a single value with automatic serialization
  - Parameters:
    - `key`: Storage key
    - `value`: Value to store (any pickleable object)

- **`get_value(key)`**
  - Retrieves and deserializes a single value
  - Parameters:
    - `key`: Storage key
  - Returns: Deserialized value

- **`set_dict(key, value: dict)`**
  - Stores a dictionary as a Redis hash
  - Parameters:
    - `key`: Hash key
    - `value`: Dictionary to store

- **`get_dict(key)`**
  - Retrieves a dictionary from Redis hash
  - Parameters:
    - `key`: Hash key
  - Returns: Dictionary with deserialized values

- **`push_to_list(key, value)`**
  - Appends a value to a Redis list
  - Parameters:
    - `key`: List key
    - `value`: Value to append

- **`read_from_list(key)`**
  - Reads all values from a Redis list
  - Parameters:
    - `key`: List key
  - Returns: List of deserialized values

- **`pop_from_list(key)`**
  - Removes and returns the first item from a Redis list
  - Parameters:
    - `key`: List key
  - Returns: Deserialized value or None if list is empty

- **`publish(channel, message)`**
  - Publishes a message to a Redis channel
  - Parameters:
    - `channel`: Channel name
    - `message`: Message to publish (any pickleable object)

- **`subscribe(channel)`**
  - Subscribes to a Redis channel
  - Parameters:
    - `channel`: Channel name
  - Returns: Redis pubsub object

- **`del_key(key)`**
  - Deletes a key from Redis
  - Parameters:
    - `key`: Key to delete

- **`clear()`**
  - Clears the entire Redis database

**Usage Example:**
```python
from RedisHandler import RedisHandler

# Initialize Redis handler
redis_handler = RedisHandler()

# Store and retrieve simple values
redis_handler.set_value("user_id", 12345)
user_id = redis_handler.get_value("user_id")

# Work with dictionaries
user_data = {"name": "John", "age": 30}
redis_handler.set_dict("user:123", user_data)
retrieved_data = redis_handler.get_dict("user:123")

# Work with lists
redis_handler.push_to_list("tasks", "task1")
redis_handler.push_to_list("tasks", "task2")
all_tasks = redis_handler.read_from_list("tasks")
next_task = redis_handler.pop_from_list("tasks")

# Pub/Sub messaging
redis_handler.publish("notifications", {"type": "alert", "message": "System update"})
pubsub = redis_handler.subscribe("notifications")
```

## Contributing

Feel free to contribute to this repository by adding new utilities or improving existing ones. 

Here's how you can contribute:

### Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Python_Utilities.git
   cd Python_Utilities
   ```

3. **Create a development environment**:
   
   Using pip
   ```bash
   pip install -e .
   ```
   Using uv (recommended for faster development)
   ```bash
   uv sync 
   ```

4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## License

This project is licensed under the terms specified in the LICENSE file.
