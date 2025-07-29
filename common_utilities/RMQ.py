import pika
import pickle as pkl
import aio_pika
import pika.adapters.blocking_connection
import pika.exceptions
from typing import List, Union, Callable, Optional, Awaitable
from urllib.parse import urlparse
import time
import traceback
import asyncio

class Sync_RMQ:
    def __init__(self, connection_url: str, exchange_name: str = "", exchange_type: str = "direct"):
        parsed = urlparse(f"//{connection_url}" if "://" not in connection_url else connection_url)
        
        # Connection parameters with proper settings
        self.__rmq_connection_parameters = pika.ConnectionParameters(
            host=parsed.hostname,
            port=parsed.port or 5672,
            connection_attempts=3,
            retry_delay=2,
            socket_timeout=10,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        # Exchange configuration
        self.exchange_name = exchange_name  # Empty string means default exchange
        self.exchange_type = exchange_type  # direct, topic, fanout, headers
        self.exchange_durable = True
        
        # Configuration
        self.max_retries = 3
        self.retry_delay = 1
        self.prefetch_count = 10
        self.durable_queues = False
        self.persistent_messages = False
        # Connection objects
        self.producer_connection = None
        self.consumer_connection = None
        self.channel_producer = None
        self.channel_consumer = None
        
        
        # Consumer callbacks storage
        self._consumer_callbacks = []
        self._declared_queues = {}

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.close()

    def __del__(self):
        """Destructor with cleanup"""
        self.close()

    def close(self):
        """Close all connections and channels"""
        try:
            if self.channel_producer and not self.channel_producer.is_closed:
                self.channel_producer.close()
            if self.channel_consumer and not self.channel_consumer.is_closed:
                self.channel_consumer.close()
            if self.producer_connection and not self.producer_connection.is_closed:
                self.producer_connection.close()
            if self.consumer_connection and not self.consumer_connection.is_closed:
                self.consumer_connection.close()
        except Exception as e:
            print(f"Error closing RMQ connections: {e}")
        finally:
            self.producer_connection = None
            self.consumer_connection = None
            self.channel_producer = None
            self.channel_consumer = None
            self._declared_queues.clear()

    def _create_connection(self, connection_type: str = "producer"):
        """Create connection with retry logic"""
        for attempt in range(self.max_retries):
            try:
                connection = pika.BlockingConnection(self.__rmq_connection_parameters)
                channel = connection.channel()
                channel.basic_qos(prefetch_count=self.prefetch_count)
                
                # Declare exchange if not using default
                if self.exchange_name:
                    channel.exchange_declare(
                        exchange=self.exchange_name,
                        exchange_type=self.exchange_type,
                        durable=self.exchange_durable
                    )
                    print(f"Exchange '{self.exchange_name}' declared (type: {self.exchange_type})")
                
                print(f"RMQ {connection_type} connection established (attempt {attempt + 1})")
                return connection, channel
                
            except pika.exceptions.AMQPConnectionError as e:
                print(f"RMQ {connection_type} connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    print(f"Failed to establish RMQ {connection_type} connection after {self.max_retries} attempts")
                    raise
            except Exception as e:
                print(f"Unexpected error creating RMQ {connection_type} connection: {e}")
                raise

    def _ensure_producer_connection(self):
        """Ensure producer connection is active"""
        if (not self.producer_connection or 
            self.producer_connection.is_closed or 
            not self.channel_producer or 
            self.channel_producer.is_closed):
            
            try:
                if self.producer_connection and not self.producer_connection.is_closed:
                    self.producer_connection.close()
            except:
                pass
            
            self.producer_connection, self.channel_producer = self._create_connection("producer")

    def _ensure_consumer_connection(self):
        """Ensure consumer connection is active"""
        if (not self.consumer_connection or 
            self.consumer_connection.is_closed or 
            not self.channel_consumer or 
            self.channel_consumer.is_closed):
            
            try:
                if self.consumer_connection and not self.consumer_connection.is_closed:
                    self.consumer_connection.close()
            except:
                pass
            
            self.consumer_connection, self.channel_consumer = self._create_connection("consumer")

    def create_queues(self, queues: Union[List[str], str], routing_key: str = None, exchange_name: str = None, durable: bool = None, queue_arguments: dict = None):
        """Declare queues only (no exchange setup)"""
        if self.channel_producer is None:
            raise Exception("No producer connection available. Call create_producer() first.")
        
        # Use provided settings or fall back to class defaults
        exchange = exchange_name if exchange_name is not None else self.exchange_name
        queue_durable = durable if durable is not None else self.durable_queues
        
        # Declare queues
        queue_list = queues if isinstance(queues, list) else [queues]
        for queue_name in queue_list:
            try:
                self.channel_producer.queue_declare(
                    queue=queue_name,
                    durable=queue_durable,
                    arguments=queue_arguments
                )
                
                # Bind queue to exchange if using custom exchange
                if exchange:
                    binding_key = routing_key or queue_name
                    self.channel_producer.queue_bind(
                        exchange=exchange,
                        queue=queue_name,
                        routing_key=binding_key
                    )
                    print(f"Queue '{queue_name}' bound to exchange '{exchange}' with routing key '{binding_key}'")
                else:
                    print(f"Queue '{queue_name}' declared (durable={queue_durable})")
                self._declared_queues[queue_name] = True  # Store queue name for sync version
            except Exception as e:
                print(f"Failed to declare queue '{queue_name}': {e}")
                raise

    def create_producer(self, exchange_name: str = None, exchange_type: str = None):
        """Create producer connection and setup exchange"""
        self._ensure_producer_connection()
        
        # Use provided exchange settings or fall back to class defaults
        exchange = exchange_name if exchange_name is not None else self.exchange_name
        ex_type = exchange_type if exchange_type is not None else self.exchange_type
        
        # Declare exchange if specified
        if exchange:
            try:
                self.channel_producer.exchange_declare(
                    exchange=exchange,
                    exchange_type=ex_type,
                    durable=self.exchange_durable
                )
                print(f"Producer exchange '{exchange}' declared (type: {ex_type})")
            except Exception as e:
                print(f"Failed to declare producer exchange '{exchange}': {e}")
                raise
        
        print(f"Producer connection established")

    def create_consumer(self, exchange_name: str = None, exchange_type: str = None):
        """Create consumer connection and setup exchange"""
        self._ensure_consumer_connection()
        
        # Use provided exchange settings or fall back to class defaults
        exchange = exchange_name if exchange_name is not None else self.exchange_name
        ex_type = exchange_type if exchange_type is not None else self.exchange_type
        
        # Declare exchange if specified
        if exchange:
            try:
                self.channel_consumer.exchange_declare(
                    exchange=exchange,
                    exchange_type=ex_type,
                    durable=self.exchange_durable
                )
                print(f"Consumer exchange '{exchange}' declared (type: {ex_type})")
            except Exception as e:
                print(f"Failed to declare consumer exchange '{exchange}': {e}")
                raise
        
        print(f"Consumer connection established")

    def publish_data(self, data, queue_name: str=None, routing_key: str = None, exchange_name: str = None):
        """Publish data to queue with retry logic and custom routing"""
        for attempt in range(self.max_retries):
            try:
                if self.channel_producer is None:
                    self.create_producer()
                
                # Ensure connection is still active
                self._ensure_producer_connection()
                
                properties = pika.BasicProperties(
                    delivery_mode=2 if self.persistent_messages else 1
                )
                
                # Use provided exchange or class default or default exchange
                exchange = exchange_name if exchange_name is not None else (self.exchange_name if self.exchange_name else "")
                routing = routing_key or queue_name
                
                self.channel_producer.basic_publish(
                    exchange=exchange,
                    routing_key=routing,
                    body=pkl.dumps(data),
                    properties=properties
                )
                
                if exchange:
                    print(f"Published message to exchange '{exchange}' with routing key '{routing}'")
                else:
                    print(f"Published message to queue '{queue_name}'")
                return True
                
            except (pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError) as e:
                print(f"RMQ publish attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    # Force reconnection on next attempt
                    self.channel_producer = None
                    continue
                else:
                    print(f"Failed to publish after {self.max_retries} attempts")
                    raise
            except Exception as e:
                print(f"Error publishing message: {e}")
                raise
        
        return False

    def consume_messages(self, func=None, queue_name=None):
        """Decorator for message handlers with improved error handling"""
        if self.channel_consumer is None:
            self.create_consumer()
        def decorator(inner_func: Callable):
            def callback(ch, method, properties, body: bytes):
                try:
                    payload:dict = pkl.loads(body)
                    # Pass payload as first argument, then original args and kwargs
                    result = inner_func(payload)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    print(f"Message processed successfully from queue '{queue_name}'")
                    return result
                except pkl.UnpicklingError as e:
                    print(f"Failed to deserialize message from queue '{queue_name}': {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                except Exception as e:
                    print(f"Error handling message from queue '{queue_name}': {e}")
                    print(traceback.format_exc())
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            self.channel_consumer.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=False
            )
                
            self._consumer_callbacks.append((queue_name, inner_func))
            return callback

        return decorator(func) if func else decorator

    def start_consuming(self):
        """Start consuming with proper error handling"""
        print(f"Consumer channel exists: {self.channel_consumer is not None}")
        print(f"Consumer channel closed: {self.channel_consumer.is_closed if self.channel_consumer else 'N/A'}")
        print(f"Registered callbacks: {len(self._consumer_callbacks)}")
        print(f"Declared queues: {list(self._declared_queues.keys())}")
        
        if not self.channel_consumer:
            print("No consumer channel available. Call create_consumer() first.")
            return

        if not self._consumer_callbacks:
            print("No consumer callbacks registered. Use @rmq.consume_messages() decorator first.")
            return
            
        # Validate that all queues used in callbacks have been declared
        callback_queues = [queue_name for queue_name, _ in self._consumer_callbacks]
        undeclared_queues = [q for q in callback_queues if q not in self._declared_queues]
        if undeclared_queues:
            print(f"Warning: Some queues used in callbacks were not explicitly declared: {undeclared_queues}")
            print("Consider calling create_queues() first for better queue management.")
            
        print("Starting RMQ message consumption...")        
        try:
            self.channel_consumer.start_consuming()
        except KeyboardInterrupt:
            print("Consumption interrupted by user")
            self.channel_consumer.stop_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Connection lost during consumption: {e}")
            raise
        except Exception as e:
            print(f"Error during consumption: {e}")
            print(traceback.format_exc())
            raise
        finally:
            print("RMQ consumption stopped")

    def stop_consuming(self):
        """Stop consuming messages"""
        if self.channel_consumer:
            try:
                self.channel_consumer.stop_consuming()
                print("RMQ consumption stopped")
            except Exception as e:
                print(f"Error stopping consumption: {e}")

    def get_declared_queues(self) -> list:
        """Get list of declared queue names"""
        return list(self._declared_queues.keys())

    def is_queue_declared(self, queue_name: str) -> bool:
        """Check if a queue has been declared"""
        return queue_name in self._declared_queues

    def is_connected(self) -> bool:
        """Check if connections are active"""
        try:
            producer_ok = (self.producer_connection and 
                         not self.producer_connection.is_closed and
                         self.channel_producer and 
                         not self.channel_producer.is_closed)
            
            consumer_ok = (self.consumer_connection and 
                         not self.consumer_connection.is_closed and
                         self.channel_consumer and 
                         not self.channel_consumer.is_closed)
            
            return producer_ok or consumer_ok
        except:
            return False
#-----------------------------------------------------------------------------------------------------------------------------------#
class Async_RMQ:
    def __init__(self, connection_url: str, exchange_name: str = "", exchange_type: str = "direct"):
        parsed = urlparse(f"//{connection_url}" if "://" not in connection_url else connection_url)
        self.connection_url = f"amqp://{parsed.hostname}:{parsed.port or 5672}"

        # Exchange configuration
        self.exchange_name = exchange_name  # Empty string means default exchange
        self.exchange_type = exchange_type  # direct, topic, fanout, headers
        self.exchange_durable = True

        # Connection objects
        self.producer_connection: Optional[aio_pika.RobustConnection] = None
        self.consumer_connection: Optional[aio_pika.RobustConnection] = None
        self.producer_channel: Optional[aio_pika.abc.AbstractChannel] = None
        self.consumer_channel: Optional[aio_pika.abc.AbstractChannel] = None

        # Configuration
        self.max_retries = 3
        self.retry_delay = 1
        self.prefetch_count = 10
        self.durable_queues = False
        self.persistent_messages = False

        # Consumer callbacks storage
        self._consumer_callbacks = []  # Stores (queue_name, callback) for registration before consuming
        self._declared_queues={}
    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup"""
        await self.close()

    def __del__(self):
        """Destructor with cleanup"""
        # Note: Cannot call async close() in __del__, so we try basic cleanup
        try:
            if hasattr(self, 'producer_connection') and self.producer_connection:
                self.producer_connection = None
            if hasattr(self, 'consumer_connection') and self.consumer_connection:
                self.consumer_connection = None
            if hasattr(self, 'producer_channel') and self.producer_channel:
                self.producer_channel = None
            if hasattr(self, 'consumer_channel') and self.consumer_channel:
                self.consumer_channel = None
        except:
            pass

    async def close(self):
        """Close all connections and channels"""
        try:
            if self.producer_channel and not self.producer_channel.is_closed:
                await self.producer_channel.close()
            if self.consumer_channel and not self.consumer_channel.is_closed:
                await self.consumer_channel.close()
            if self.producer_connection and not self.producer_connection.is_closed:
                await self.producer_connection.close()
            if self.consumer_connection and not self.consumer_connection.is_closed:
                await self.consumer_connection.close()
        except Exception as e:
            print(f"Error closing async RMQ connections: {e}")
        finally:
            self.producer_connection = None
            self.consumer_connection = None
            self.producer_channel = None
            self.consumer_channel = None
            self._declared_queues.clear()

    async def _ensure_producer_connection(self):
        """Ensure producer connection is active"""
        if (not self.producer_connection or 
            self.producer_connection.is_closed or 
            not self.producer_channel or 
            self.producer_channel.is_closed):
            
            try:
                if self.producer_connection and not self.producer_connection.is_closed:
                    await self.producer_connection.close()
            except:
                pass
            
            await self.__connect_producer()

    async def _ensure_consumer_connection(self):
        """Ensure consumer connection is active"""
        if (not self.consumer_connection or 
            self.consumer_connection.is_closed or 
            not self.consumer_channel or 
            self.consumer_channel.is_closed):
            
            try:
                if self.consumer_connection and not self.consumer_connection.is_closed:
                    await self.consumer_connection.close()
            except:
                pass
            
            await self.__connect_consumer()

    async def __connect_producer(self):
        """Connect producer with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if not self.producer_connection:
                    self.producer_connection = await aio_pika.connect_robust(self.connection_url)
                    self.producer_channel = await self.producer_connection.channel()
                    await self.producer_channel.set_qos(prefetch_count=self.prefetch_count)
                    
                    # Declare exchange if not using default
                    if self.exchange_name:
                        await self.producer_channel.declare_exchange(
                            name=self.exchange_name,
                            type=getattr(aio_pika.ExchangeType, self.exchange_type.upper()),
                            durable=self.exchange_durable
                        )
                        print(f"Async exchange '{self.exchange_name}' declared (type: {self.exchange_type})")
                    
                    print(f"Async RMQ producer connection established (attempt {attempt + 1})")
                    return
            except Exception as e:
                print(f"Async RMQ producer connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    print(f"Failed to establish async RMQ producer connection after {self.max_retries} attempts")
                    raise

    async def __connect_consumer(self):
        """Connect consumer with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if not self.consumer_connection:
                    self.consumer_connection = await aio_pika.connect_robust(self.connection_url)
                    self.consumer_channel = await self.consumer_connection.channel()
                    await self.consumer_channel.set_qos(prefetch_count=self.prefetch_count)
                    
                    # Declare exchange if not using default
                    if self.exchange_name:
                        await self.consumer_channel.declare_exchange(
                            name=self.exchange_name,
                            type=getattr(aio_pika.ExchangeType, self.exchange_type.upper()),
                            durable=self.exchange_durable
                        )
                        print(f"Async exchange '{self.exchange_name}' declared (type: {self.exchange_type})")
                    
                    print(f"Async RMQ consumer connection established (attempt {attempt + 1})")
                    return
            except Exception as e:
                print(f"Async RMQ consumer connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    print(f"Failed to establish async RMQ consumer connection after {self.max_retries} attempts")
                    raise

    async def create_queues(self, queues: Union[List[str], str], routing_key: str = None, exchange_name: str = None, durable: bool = None, queue_arguments: dict = None):
        """Declare queues only (no exchange setup)"""
        if self.producer_channel is None:
            raise Exception("No producer connection available. Call create_producer() first.")
        
        # Use provided settings or fall back to class defaults
        exchange = exchange_name if exchange_name is not None else self.exchange_name
        queue_durable = durable if durable is not None else self.durable_queues
        
        # Declare queues
        queue_list = queues if isinstance(queues, list) else [queues]
        for queue_name in queue_list:
            try:
                queue = await self.producer_channel.declare_queue(
                    queue_name, 
                    durable=queue_durable,
                    arguments=queue_arguments
                    
                )
                
                # Bind queue to exchange if using custom exchange
                if exchange:
                    binding_key = routing_key or queue_name
                    await queue.bind(exchange, routing_key=binding_key)
                    print(f"Async queue '{queue_name}' bound to exchange '{exchange}' with routing key '{binding_key}'")
                else:
                    print(f"Async queue '{queue_name}' declared (durable={queue_durable})")
                self._declared_queues[queue_name]=queue
            except Exception as e:
                print(f"Failed to declare async queue '{queue_name}': {e}")
                raise

    async def create_producer(self, exchange_name: str = None, exchange_type: str = None):
        """Create producer connection and setup exchange"""
        await self._ensure_producer_connection()
        
        # Use provided exchange settings or fall back to class defaults
        exchange = exchange_name if exchange_name is not None else self.exchange_name
        ex_type = exchange_type if exchange_type is not None else self.exchange_type
        
        # Declare exchange if specified
        if exchange:
            try:
                await self.producer_channel.declare_exchange(
                    name=exchange,
                    type=getattr(aio_pika.ExchangeType, ex_type.upper()),
                    durable=self.exchange_durable
                )
                print(f"Async producer exchange '{exchange}' declared (type: {ex_type})")
            except Exception as e:
                print(f"Failed to declare async producer exchange '{exchange}': {e}")
                raise
        
        print(f"Async producer connection established")

    async def create_consumer(self, exchange_name: str = None, exchange_type: str = None):
        """Create consumer connection and setup exchange"""
        await self._ensure_consumer_connection()
        
        # Use provided exchange settings or fall back to class defaults
        exchange = exchange_name if exchange_name is not None else self.exchange_name
        ex_type = exchange_type if exchange_type is not None else self.exchange_type
        
        # Declare exchange if specified
        if exchange:
            try:
                await self.consumer_channel.declare_exchange(
                    name=exchange,
                    type=getattr(aio_pika.ExchangeType, ex_type.upper()),
                    durable=self.exchange_durable
                )
                print(f"Async consumer exchange '{exchange}' declared (type: {ex_type})")
            except Exception as e:
                print(f"Failed to declare async consumer exchange '{exchange}': {e}")
                raise
        
        print(f"Async consumer connection established")

    async def publish_data(self, data, queue_name: str, routing_key: str = None, exchange_name: str = None):
        """Publish data to queue with retry logic and custom routing"""
        for attempt in range(self.max_retries):
            try:
                if self.producer_channel is None:
                    await self.create_producer()
                
                # Ensure connection is still active
                await self._ensure_producer_connection()
                
                message = aio_pika.Message(
                    body=pkl.dumps(data),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT if self.persistent_messages else aio_pika.DeliveryMode.NOT_PERSISTENT
                )
                
                # Use provided exchange or class default or default exchange
                exchange = exchange_name if exchange_name is not None else (self.exchange_name if self.exchange_name else "")
                
                if exchange:
                    exchange_obj = await self.producer_channel.get_exchange(exchange)
                    routing = routing_key or queue_name
                    await exchange_obj.publish(message, routing_key=routing)
                    print(f"Published async message to exchange '{exchange}' with routing key '{routing}'")
                else:
                    await self.producer_channel.default_exchange.publish(
                        message,
                        routing_key=queue_name
                    )
                    print(f"Published async message to queue '{queue_name}'")
                
                return True
                
            except Exception as e:
                print(f"Async RMQ publish attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    # Force reconnection on next attempt
                    self.producer_connection = None
                    self.producer_channel = None
                    continue
                else:
                    print(f"Failed to async publish after {self.max_retries} attempts")
                    raise
        
        return False

    def consume_messages(self, func=None, queue_name=None):
        """Decorator for async message handlers with improved error handling"""
        def decorator(inner_func: Callable):
            async def callback(message: aio_pika.IncomingMessage):
                async with message.process(ignore_processed=True):
                    try:
                        payload: dict = pkl.loads(message.body)
                        # Pass payload as first argument
                        result = await inner_func(payload)
                        print(f"Async message processed successfully from queue '{queue_name}'")
                        return result
                    except pkl.UnpicklingError as e:
                        print(f"Failed to deserialize async message from queue '{queue_name}': {e}")
                        await message.nack(requeue=False)
                    except Exception as e:
                        print(f"Error handling async message from queue '{queue_name}': {e}")
                        print(traceback.format_exc())
                        await message.nack(requeue=True)

            self._consumer_callbacks.append((queue_name, callback))  # Store callback, not inner_func
            return callback

        return decorator(func) if func else decorator

    async def start_consuming(self):
        """Start consuming with proper error handling"""
        print(f"Async consumer channel exists: {self.consumer_channel is not None}")
        print(f"Async consumer channel closed: {self.consumer_channel.is_closed if self.consumer_channel else 'N/A'}")
        print(f"Async registered callbacks: {len(self._consumer_callbacks)}")
        
        if not self.consumer_channel:
            print("No async consumer channel available. Call create_consumer() first.")
            return

        if not self._consumer_callbacks:
            print("No async consumer callbacks registered. Use @rmq.consume_messages() decorator first.")
            return

        print("Starting async RMQ message consumption...")
        try:
            await self._ensure_consumer_connection()

            for queue_name, handler in self._consumer_callbacks:
                try:
                    # Ensure queue exists before consuming
                    if queue_name in self._declared_queues:
                        queue = self._declared_queues[queue_name]
                        await queue.consume(handler)
                        print(f"Started async consuming from queue '{queue_name}'")
                except Exception as e:
                    print(f"Error setting up async consumer for queue '{queue_name}': {e}")
                    raise

            print(" [*] Async consumer started. Waiting for messages...")
            # Keep the connection alive
            await asyncio.Event().wait()
            
        except KeyboardInterrupt:
            print("Async consumption interrupted by user")
            await self.stop_consuming()
        except Exception as e:
            print(f"Error during async consumption: {e}")
            print(traceback.format_exc())
            raise
        finally:
            print("Async RMQ consumption stopped")

    async def stop_consuming(self):
        """Stop consuming messages"""
        try:
            if self.consumer_channel and not self.consumer_channel.is_closed:
                # Cancel all consumers
                for tag in list(self.consumer_channel._consumers.keys()):
                    await self.consumer_channel.cancel(tag)
                print("Async RMQ consumption stopped")
        except Exception as e:
            print(f"Error stopping async consumption: {e}")

    def get_declared_queues(self) -> list:
        """Get list of declared queue names"""
        return list(self._declared_queues.keys())

    def is_queue_declared(self, queue_name: str) -> bool:
        """Check if a queue has been declared"""
        return queue_name in self._declared_queues

    def is_connected(self) -> bool:
        """Check if connections are active"""
        try:
            producer_ok = (self.producer_connection and 
                         not self.producer_connection.is_closed and
                         self.producer_channel and 
                         not self.producer_channel.is_closed)
            
            consumer_ok = (self.consumer_connection and 
                         not self.consumer_connection.is_closed and
                         self.consumer_channel and 
                         not self.consumer_channel.is_closed)
            
            return producer_ok or consumer_ok
        except:
            return False



