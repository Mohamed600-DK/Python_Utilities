# RMQ.py

RabbitMQ client library providing both synchronous and asynchronous messaging capabilities with exchange-based routing, queue management, and robust error handling.

## Classes

### `Sync_RMQ`
Synchronous RabbitMQ client for message publishing and consuming.

#### Constructor
```python
Sync_RMQ(connection_url: str, exchange_name: str = "", exchange_type: str = "direct")
```

- **Parameters:**
  - `connection_url`: RabbitMQ connection URL (e.g., "localhost:5672")
  - `exchange_name`: Name of the exchange (empty string for default exchange)
  - `exchange_type`: Type of exchange ("direct", "topic", "fanout", "headers")

#### Configuration Properties
- `max_retries`: Maximum connection retry attempts (default: 3)
- `retry_delay`: Delay between retry attempts in seconds (default: 1)
- `prefetch_count`: Number of messages to prefetch (default: 10)
- `durable_queues`: Whether queues should be durable (default: False)
- `persistent_messages`: Whether messages should be persistent (default: False)
- `exchange_durable`: Whether exchange should be durable (default: True)

#### Methods

##### `create_producer(exchange_name: str = None, exchange_type: str = None)`
Creates a producer connection and sets up the exchange.

##### `create_consumer(exchange_name: str = None, exchange_type: str = None)`
Creates a consumer connection and sets up the exchange.

##### `create_queues(queues: Union[List[str], str], routing_key: str = None, exchange_name: str = None, durable: bool = None)`
Declares queues and binds them to exchanges.

- **Parameters:**
  - `queues`: Queue name(s) as string or list of strings
  - `routing_key`: Routing key for binding (defaults to queue name)
  - `exchange_name`: Exchange to bind to (uses class default if None)
  - `durable`: Queue durability (uses class default if None)

##### `publish_data(data, queue_name: str = None, routing_key: str = None, exchange_name: str = None)`
Publishes data to a queue with retry logic.

- **Parameters:**
  - `data`: Data to publish (will be pickled)
  - `queue_name`: Target queue name
  - `routing_key`: Custom routing key
  - `exchange_name`: Target exchange (uses class default if None)

##### `consume_messages(func=None, queue_name=None)`
Decorator for message handlers with error handling.

- **Parameters:**
  - `func`: Handler function (optional for decorator usage)
  - `queue_name`: Queue to consume from

##### `start_consuming()`
Starts consuming messages from registered queues.

##### `stop_consuming()`
Stops consuming messages.

##### `close()`
Closes all connections and channels.

##### `is_connected() -> bool`
Checks if connections are active.

##### `get_declared_queues() -> list`
Returns list of declared queue names.

##### `is_queue_declared(queue_name: str) -> bool`
Checks if a queue has been declared.

#### Context Manager Support
The class supports context manager usage:
```python
with Sync_RMQ("localhost:5672") as rmq:
    # Use rmq instance
    pass
```

### `Async_RMQ`
Asynchronous RabbitMQ client for message publishing and consuming.

#### Constructor
```python
Async_RMQ(connection_url: str, exchange_name: str = "", exchange_type: str = "direct")
```

Same parameters as `Sync_RMQ`.

#### Methods
All methods are asynchronous versions of the `Sync_RMQ` methods:

##### `async create_producer(exchange_name: str = None, exchange_type: str = None)`
##### `async create_consumer(exchange_name: str = None, exchange_type: str = None)`
##### `async create_queues(queues: Union[List[str], str], routing_key: str = None, exchange_name: str = None, durable: bool = None)`
##### `async publish_data(data, queue_name: str, routing_key: str = None, exchange_name: str = None)`
##### `consume_messages(func=None, queue_name=None)`
Decorator for async message handlers.

##### `async start_consuming()`
##### `async stop_consuming()`
##### `async close()`

#### Async Context Manager Support
```python
async with Async_RMQ("localhost:5672") as rmq:
    # Use rmq instance
    pass
```

## Usage Examples

### Synchronous Usage

#### Basic Publisher
```python
from common_utilities.RMQ import Sync_RMQ

# Create RMQ instance
rmq = Sync_RMQ("localhost:5672", exchange_name="my_exchange", exchange_type="direct")

# Create producer and queues
rmq.create_producer()
rmq.create_queues(["task_queue", "result_queue"])

# Publish data
rmq.publish_data({"message": "Hello World"}, queue_name="task_queue")

# Clean up
rmq.close()
```

#### Basic Consumer
```python
from common_utilities.RMQ import Sync_RMQ

# Create RMQ instance
rmq = Sync_RMQ("localhost:5672", exchange_name="my_exchange", exchange_type="direct")

# Create consumer and queues
rmq.create_consumer()
rmq.create_queues(["task_queue"])

# Define message handler
@rmq.consume_messages(queue_name="task_queue")
def handle_message(payload):
    print(f"Received: {payload}")
    return "processed"

# Start consuming
rmq.start_consuming()
```

#### Using Context Manager
```python
from common_utilities.RMQ import Sync_RMQ

with Sync_RMQ("localhost:5672") as rmq:
    rmq.create_producer()
    rmq.create_queues("my_queue")
    rmq.publish_data({"task": "process_data"}, queue_name="my_queue")
```

### Asynchronous Usage

#### Basic Async Publisher
```python
import asyncio
from common_utilities.RMQ import Async_RMQ

async def main():
    rmq = Async_RMQ("localhost:5672", exchange_name="async_exchange")
    
    await rmq.create_producer()
    await rmq.create_queues(["async_queue"])
    
    await rmq.publish_data({"async_message": "Hello Async World"}, queue_name="async_queue")
    
    await rmq.close()

asyncio.run(main())
```

#### Basic Async Consumer
```python
import asyncio
from common_utilities.RMQ import Async_RMQ

async def main():
    rmq = Async_RMQ("localhost:5672", exchange_name="async_exchange")
    
    await rmq.create_consumer()
    await rmq.create_queues(["async_queue"])
    
    @rmq.consume_messages(queue_name="async_queue")
    async def handle_async_message(payload):
        print(f"Async received: {payload}")
        await asyncio.sleep(1)  # Simulate async processing
        return "async_processed"
    
    await rmq.start_consuming()

asyncio.run(main())
```

#### Using Async Context Manager
```python
import asyncio
from common_utilities.RMQ import Async_RMQ

async def main():
    async with Async_RMQ("localhost:5672") as rmq:
        await rmq.create_producer()
        await rmq.create_queues("async_queue")
        await rmq.publish_data({"task": "async_process"}, queue_name="async_queue")

asyncio.run(main())
```

## Exchange Types

### Direct Exchange
- Routes messages to queues based on exact routing key match
- Default exchange type

### Topic Exchange
- Routes messages based on routing key patterns with wildcards
- Supports `*` (single word) and `#` (multiple words) wildcards

### Fanout Exchange
- Broadcasts messages to all bound queues
- Ignores routing key

### Headers Exchange
- Routes messages based on message headers instead of routing key

## Error Handling

Both classes provide robust error handling:

- **Connection Recovery**: Automatic reconnection on connection failures
- **Retry Logic**: Configurable retry attempts for publishing and connection
- **Message Acknowledgment**: Proper message acknowledgment with requeue on errors
- **Graceful Shutdown**: Clean connection and channel closure
- **Logging**: Comprehensive logging of operations and errors

## Dependencies

- `pika`: Synchronous RabbitMQ client
- `aio-pika`: Asynchronous RabbitMQ client
- `pickle`: Message serialization

## Installation

```bash
pip install pika aio-pika
```

## Best Practices

1. **Use Context Managers**: Always use context managers for automatic cleanup
2. **Configure Durability**: Set appropriate durability settings for production
3. **Handle Exceptions**: Implement proper exception handling in message handlers
4. **Monitor Connections**: Use `is_connected()` to monitor connection status
5. **Declare Queues**: Always declare queues before consuming or publishing
6. **Use Exchanges**: Leverage exchanges for flexible routing patterns
7. **Set QoS**: Configure appropriate prefetch counts for consumers
