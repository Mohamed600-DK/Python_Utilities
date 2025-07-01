# Base_Processing.py

A Script provides an abstract base class for creating and managing multiprocess applications with shared data, events, and notifications.

## `Base_process` Class

An abstract base class that extends `multiprocessing.Process` to provide enhanced multiprocessing capabilities.

### Methods

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

### Class Methods for Shared Resources

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

### Usage Example

```python
from common_utilities import Base_process

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

---
[Back to Main README](../README.md)
