# RedisHandler.py

A Redis wrapper class that provides simplified operations with automatic serialization using pickle.

## `RedisHandler` Class

Provides high-level Redis operations with automatic pickle serialization.

### Environment Variables
- `REDIS_HOSTNAME`: Redis server hostname (default: localhost)
- `REDIS_HOSTPORT`: Redis server port (default: 6379)

### Methods

#### `__init__(host="localhost", port=6379, db=0)`
- Initializes Redis connection
- Uses environment variables if available
- **Parameters:**
  - `host`: Redis server host
  - `port`: Redis server port
  - `db`: Redis database number

#### `set_value(key, value)`
- Stores a single value with automatic serialization
- **Parameters:**
  - `key`: Storage key
  - `value`: Value to store (any pickleable object)

#### `get_value(key)`
- Retrieves and deserializes a single value
- **Parameters:**
  - `key`: Storage key
- **Returns:** Deserialized value

#### `set_dict(key, value: dict)`
- Stores a dictionary as a Redis hash
- **Parameters:**
  - `key`: Hash key
  - `value`: Dictionary to store

#### `get_dict(key)`
- Retrieves a dictionary from Redis hash
- **Parameters:**
  - `key`: Hash key
- **Returns:** Dictionary with deserialized values

#### `push_to_list(key, value)`
- Appends a value to a Redis list
- **Parameters:**
  - `key`: List key
  - `value`: Value to append

#### `read_from_list(key)`
- Reads all values from a Redis list
- **Parameters:**
  - `key`: List key
- **Returns:** List of deserialized values

#### `pop_from_list(key)`
- Removes and returns the first item from a Redis list
- **Parameters:**
  - `key`: List key
- **Returns:** Deserialized value or None if list is empty

#### `publish(channel, message)`
- Publishes a message to a Redis channel
- **Parameters:**
  - `channel`: Channel name
  - `message`: Message to publish (any pickleable object)

#### `subscribe(channel)`
- Subscribes to a Redis channel
- **Parameters:**
  - `channel`: Channel name
- **Returns:** Redis pubsub object

#### `del_key(key)`
- Deletes a key from Redis
- **Parameters:**
  - `key`: Key to delete

#### `clear()`
- Clears the entire Redis database

## Usage Example

```python
from common_utilities import RedisHandler

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

## Requirements

- `redis>=6.2.0` - Python Redis client

## Features

- **Automatic Serialization**: Uses pickle to serialize/deserialize Python objects
- **Environment Configuration**: Supports Redis connection via environment variables
- **Multiple Data Types**: Supports strings, dictionaries, lists, and pub/sub messaging
- **Error Handling**: Graceful handling of Redis connection and operation errors

## Installation

```python
from common_utilities import RedisHandler
```

---
[Back to Main README](../README.md)
