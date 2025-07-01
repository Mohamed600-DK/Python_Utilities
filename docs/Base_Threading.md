# Base_Threading.py

A Script that provides an abstract base class for creating thread-based applications with shared resources.

## `Base_Thread` Class

An abstract base class for creating and managing threaded applications.

### Class Attributes
- `threads_events`: Dictionary of threading Event objects
- `threads_notifications`: Dictionary of threading Condition objects  
- `threads_data`: Dictionary of Queue objects for thread communication

### Methods

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

### Usage Example

```python
from common_utilities import Base_Thread

class MyThread(Base_Thread):
    def run(self):
        while not self.stop_thread:
            # Your thread logic here
            pass

# Create and start thread
thread = MyThread("worker_thread")
thread.Start_thread()
```

---
[Back to Main README](../README.md)
