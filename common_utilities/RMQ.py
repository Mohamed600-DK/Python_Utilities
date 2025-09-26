import os
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
from common_utilities.logger import LOGGER, LOG_LEVEL
class Sync_RMQ:
    def __init__(self, exchange_name: str = "", exchange_type: str = "direct",logger:Optional[Union[LOGGER,str]]=None):
        if isinstance(logger,str):
            self.logs = LOGGER(logger)
            self.logs.create_File_logger(f"{logger}",log_levels=["DEBUG", "INFO", "ERROR", "CRITICAL", "WARNING"])
            self.logs.create_Stream_logger(log_levels=["INFO", "ERROR", "WARNING"])
        elif isinstance(logger,LOGGER):
            self.logs=logger
        else:
            self.logs = LOGGER(None)
        connection_url: str=os.getenv("RMQ_URL", "localhost:5672")
        parsed = urlparse(f"//{connection_url}" if "://" not in connection_url else connection_url)
        credentials = None
        if parsed.username and parsed.password:
            credentials = pika.PlainCredentials(parsed.username, parsed.password)
        else:
            credentials = pika.PlainCredentials("guest", "guest")
        # Minimal connection parameters - server controls all settings
        self.__rmq_connection_parameters = pika.ConnectionParameters(
            host=parsed.hostname,
            port=parsed.port or 5672,
            credentials=credentials
            # All other settings (heartbeat, timeouts, frame_max, etc.) controlled by server
        )
        
        # Exchange configuration
        self.exchange_name = exchange_name  # Empty string means default exchange
        self.exchange_type = exchange_type  # direct, topic, fanout, headers
        self.exchange_durable = True
        
        # Configuration - server controls most settings, minimal client overrides
        self.max_retries = int(os.getenv("RMQ_MAX_RETRIES", "3"))  # Client retry logic only
        self.retry_delay = int(os.getenv("RMQ_RETRY_DELAY", "1"))   # Client retry delay only
        # Server controls: prefetch_count, heartbeat, timeouts, frame_max, etc.
        self.durable_queues = True
        self.persistent_messages = False
        # Connection health monitoring - server controls heartbeat
        self._last_heartbeat_check = 0
        self._heartbeat_interval = 30  # Fixed 30-second interval for health checks
        self._connection_health_check_interval = 60
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
            self.logs.write_logs(f"Error closing RMQ connections: {e}", LOG_LEVEL.ERROR)
        finally:
            self.producer_connection = None
            self.consumer_connection = None
            self.channel_producer = None
            self.channel_consumer = None
            self._declared_queues.clear()

    def _health_check_connection(self, connection_type: str = "producer"):
        """Check connection health and heartbeat status"""
        try:
            current_time = time.time()
            if current_time - self._last_heartbeat_check < self._heartbeat_interval:
                return True
            
            if connection_type == "producer":
                if (self.producer_connection and 
                    not self.producer_connection.is_closed and 
                    self.channel_producer and 
                    not self.channel_producer.is_closed):
                    # Send a heartbeat-like operation to test connection
                    self.channel_producer.queue_declare(queue='__health_check__', passive=True, arguments={'x-expires': 1000})
                    self._last_heartbeat_check = current_time
                    return True
            else:  # consumer
                if (self.consumer_connection and 
                    not self.consumer_connection.is_closed and 
                    self.channel_consumer and 
                    not self.channel_consumer.is_closed):
                    # Test consumer connection health
                    self.channel_consumer.queue_declare(queue='__health_check__', passive=True, arguments={'x-expires': 1000})
                    self._last_heartbeat_check = current_time
                    return True
            
            return False
        except Exception as e:
            self.logs.write_logs(f"Connection health check failed for {connection_type}: {e}", LOG_LEVEL.WARNING)
            return False

    def _create_connection(self, connection_type: str = "producer"):
        """Create connection with retry logic"""
        for attempt in range(self.max_retries):
            try:
                connection = pika.BlockingConnection(self.__rmq_connection_parameters)
                channel = connection.channel()
                # Server controls prefetch_count, so no need to set it here
                # channel.basic_qos(prefetch_count=self.prefetch_count)  # Removed - server controlled
                
                # Declare exchange if not using default
                if self.exchange_name:
                    channel.exchange_declare(
                        exchange=self.exchange_name,
                        exchange_type=self.exchange_type,
                        durable=self.exchange_durable
                    )
                    self.logs.write_logs(f"Exchange '{self.exchange_name}' declared (type: {self.exchange_type})", LOG_LEVEL.INFO)
                
                self.logs.write_logs(f"RMQ {connection_type} connection established (attempt {attempt + 1})", LOG_LEVEL.DEBUG)
                return connection, channel
                
            except pika.exceptions.AMQPConnectionError as e:
                self.logs.write_logs(f"RMQ {connection_type} connection attempt {attempt + 1} failed: {e}", LOG_LEVEL.WARNING)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    self.logs.write_logs(f"Failed to establish RMQ {connection_type} connection after {self.max_retries} attempts", LOG_LEVEL.ERROR)
                    raise
            except Exception as e:
                self.logs.write_logs(f"Unexpected error creating RMQ {connection_type} connection: {e}", LOG_LEVEL.ERROR)
                raise

    def _ensure_producer_connection(self):
        """Ensure producer connection is active with health check"""
        if (not self.producer_connection or 
            self.producer_connection.is_closed or 
            not self.channel_producer or 
            self.channel_producer.is_closed 
            ):#or not self._health_check_connection("producer")):
            
            self.logs.write_logs("Recreating producer connection due to health check failure", LOG_LEVEL.INFO)
            try:
                if self.producer_connection and not self.producer_connection.is_closed:
                    self.producer_connection.close()
            except Exception as e:
                self.logs.write_logs(f"Error closing old producer connection: {e}", LOG_LEVEL.WARNING)
            
            self.producer_connection, self.channel_producer = self._create_connection("producer")

    def _ensure_consumer_connection(self):
        """Ensure consumer connection is active with health check"""
        if (not self.consumer_connection or 
            self.consumer_connection.is_closed or 
            not self.channel_consumer or 
            self.channel_consumer.is_closed ):#or not self._health_check_connection("producer")):
            
            self.logs.write_logs("Recreating consumer connection due to health check failure", LOG_LEVEL.INFO)
            try:
                if self.consumer_connection and not self.consumer_connection.is_closed:
                    self.consumer_connection.close()
            except Exception as e:
                self.logs.write_logs(f"Error closing old consumer connection: {e}", LOG_LEVEL.WARNING)
            
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
                    self.logs.write_logs(f"Queue '{queue_name}' bound to exchange '{exchange}' with routing key '{binding_key}'", LOG_LEVEL.INFO)
                else:
                    self.logs.write_logs(f"Queue '{queue_name}' declared (durable={queue_durable})", LOG_LEVEL.INFO)
                self._declared_queues[queue_name] = True  # Store queue name for sync version
            except Exception as e:
                self.logs.write_logs(f"Failed to declare queue '{queue_name}': {e}", LOG_LEVEL.ERROR)
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
                self.logs.write_logs(f"Producer exchange '{exchange}' declared (type: {ex_type})", LOG_LEVEL.INFO)
            except Exception as e:
                self.logs.write_logs(f"Failed to declare producer exchange '{exchange}': {e}", LOG_LEVEL.ERROR)
                raise
        
        self.logs.write_logs(f"Producer connection established", LOG_LEVEL.INFO)

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
                self.logs.write_logs(f"Consumer exchange '{exchange}' declared (type: {ex_type})", LOG_LEVEL.INFO)
            except Exception as e:
                self.logs.write_logs(f"Failed to declare consumer exchange '{exchange}': {e}", LOG_LEVEL.ERROR)
                raise
        
        self.logs.write_logs(f"Consumer connection established", LOG_LEVEL.INFO)

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
                    self.logs.write_logs(f"Published message to exchange '{exchange}' with routing key '{routing}'", LOG_LEVEL.INFO)
                else:
                    self.logs.write_logs(f"Published message to queue '{queue_name}'", LOG_LEVEL.INFO)
                return True
                
            except (pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError) as e:
                self.logs.write_logs(f"RMQ publish attempt {attempt + 1} failed: {e}", LOG_LEVEL.WARNING)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    # Force reconnection on next attempt
                    self.channel_producer = None
                    continue
                else:
                    self.logs.write_logs(f"Failed to publish after {self.max_retries} attempts", LOG_LEVEL.ERROR)
                    raise
            except Exception as e:
                self.logs.write_logs(f"Error publishing message: {e}", LOG_LEVEL.ERROR)
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
                    self.logs.write_logs(f"Message processed successfully from queue '{queue_name}'", LOG_LEVEL.INFO)
                    return result
                except pkl.UnpicklingError as e:
                    self.logs.write_logs(f"Failed to deserialize message from queue '{queue_name}': {e}", LOG_LEVEL.ERROR)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                except Exception as e:
                    self.logs.write_logs(f"Error handling message from queue '{queue_name}': {e}", LOG_LEVEL.ERROR)
                    self.logs.write_logs(traceback.format_exc(), LOG_LEVEL.DEBUG)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

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
        self.logs.write_logs(f"Consumer channel exists: {self.channel_consumer is not None}", LOG_LEVEL.DEBUG)
        self.logs.write_logs(f"Consumer channel closed: {self.channel_consumer.is_closed if self.channel_consumer else 'N/A'}", LOG_LEVEL.DEBUG)
        self.logs.write_logs(f"Registered callbacks: {len(self._consumer_callbacks)}", LOG_LEVEL.DEBUG)
        self.logs.write_logs(f"Declared queues: {list(self._declared_queues.keys())}", LOG_LEVEL.DEBUG)
        
        if not self.channel_consumer:
            self.logs.write_logs("No consumer channel available. Call create_consumer() first.", LOG_LEVEL.ERROR)
            return

        if not self._consumer_callbacks:
            self.logs.write_logs("No consumer callbacks registered. Use @rmq.consume_messages() decorator first.", LOG_LEVEL.ERROR)
            return
            
        # Validate that all queues used in callbacks have been declared
        callback_queues = [queue_name for queue_name, _ in self._consumer_callbacks]
        undeclared_queues = [q for q in callback_queues if q not in self._declared_queues]
        if undeclared_queues:
            self.logs.write_logs(f"Some queues used in callbacks were not explicitly declared: {undeclared_queues}", LOG_LEVEL.WARNING)
            self.logs.write_logs("Consider calling create_queues() first for better queue management.", LOG_LEVEL.WARNING)
            
        self.logs.write_logs("Starting RMQ message consumption...", LOG_LEVEL.INFO)        
        try:
            self.channel_consumer.start_consuming()
        except KeyboardInterrupt:
            self.logs.write_logs("Consumption interrupted by user", LOG_LEVEL.INFO)
            self.channel_consumer.stop_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            self.logs.write_logs(f"Connection lost during consumption: {e}", LOG_LEVEL.ERROR)
            raise
        except Exception as e:
            self.logs.write_logs(f"Error during consumption: {e}", LOG_LEVEL.ERROR)
            self.logs.write_logs(traceback.format_exc(), LOG_LEVEL.ERROR)
            raise
        finally:
            self.logs.write_logs("RMQ consumption stopped", LOG_LEVEL.INFO)

    def stop_consuming(self):
        """Stop consuming messages"""
        if self.channel_consumer:
            try:
                self.channel_consumer.stop_consuming()
                self.logs.write_logs("RMQ consumption stopped", LOG_LEVEL.INFO)
            except Exception as e:
                self.logs.write_logs(f"Error stopping consumption: {e}", LOG_LEVEL.ERROR)

    def get_declared_queues(self) -> list:
        """Get list of declared queue names"""
        return list(self._declared_queues.keys())

    def is_queue_declared(self, queue_name: str) -> bool:
        """Check if a queue has been declared"""
        return queue_name in self._declared_queues

    def is_connected(self) -> bool:
        """Check if connections are active and healthy"""
        try:
            producer_ok = (self.producer_connection and 
                         not self.producer_connection.is_closed and
                         self.channel_producer and 
                         not self.channel_producer.is_closed )#or self._health_check_connection("producer"))
            
            consumer_ok = (self.consumer_connection and 
                         not self.consumer_connection.is_closed and
                         self.channel_consumer and 
                         not self.channel_consumer.is_closed )#or self._health_check_connection("consumer"))
            
            return producer_ok or consumer_ok
        except Exception as e:
            self.logs.write_logs(f"Error checking connection health: {e}", LOG_LEVEL.WARNING)
            return False
    
    def get_connection_info(self) -> dict:
        """Get detailed connection information for debugging"""
        return {
            "producer_connected": self.producer_connection and not self.producer_connection.is_closed,
            "consumer_connected": self.consumer_connection and not self.consumer_connection.is_closed,
            "producer_channel_open": self.channel_producer and not self.channel_producer.is_closed,
            "consumer_channel_open": self.channel_consumer and not self.channel_consumer.is_closed,
            "last_heartbeat_check": self._last_heartbeat_check,
            "heartbeat_interval": self._heartbeat_interval,
            "prefetch_count": self.prefetch_count,
            "declared_queues": list(self._declared_queues.keys())
        }
#-----------------------------------------------------------------------------------------------------------------------------------#
class Async_RMQ:
    def __init__(self, exchange_name: str = "", exchange_type: str = "direct",logger:Optional[Union[LOGGER,str]]=None):
        if isinstance(logger,str):
            self.logs = LOGGER(logger)
            self.logs.create_File_logger(f"{logger}")
            self.logs.create_Stream_logger()
        elif isinstance(logger,LOGGER):
            self.logs=logger
        else:
            self.logs = LOGGER(None)
        connection_url: str=os.getenv("RMQ_URL", "localhost:5672")
        self.__parsed = urlparse(f"//{connection_url}" if "://" not in connection_url else connection_url)
        self.__credentials = None
        if self.__parsed.username and self.__parsed.password:
            self.__credentials = pika.PlainCredentials(self.__parsed.username, self.__parsed.password)
            print(f"Using credentials: {self.__credentials.username} / {self.__credentials.password}")
        # Exchange configuration
        self.exchange_name = exchange_name  # Empty string means default exchange
        self.exchange_type = exchange_type  # direct, topic, fanout, headers
        self.exchange_durable = True

        # Connection objects
        self.producer_connection: Optional[aio_pika.RobustConnection] = None
        self.consumer_connection: Optional[aio_pika.RobustConnection] = None
        self.producer_channel: Optional[aio_pika.abc.AbstractChannel] = None
        self.consumer_channel: Optional[aio_pika.abc.AbstractChannel] = None

        # Configuration - server controls connection settings, minimal client config
        self.max_retries = int(os.getenv("RMQ_MAX_RETRIES", "3"))  # Client retry logic only
        self.retry_delay = int(os.getenv("RMQ_RETRY_DELAY", "1"))   # Client retry delay only
        # Server controls: prefetch_count, heartbeat, timeouts, frame_max, etc.
        self.durable_queues = True
        self.persistent_messages = False
        # Connection health monitoring - server controls all connection parameters
        self._last_heartbeat_check = 0
        self._heartbeat_interval = 30  # Fixed interval for health checks only

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
            self.logs.write_logs(f"Error closing async RMQ connections: {e}", LOG_LEVEL.ERROR)
        finally:
            self.producer_connection = None
            self.consumer_connection = None
            self.producer_channel = None
            self.consumer_channel = None
            self._declared_queues.clear()

    async def _health_check_connection(self, connection_type: str = "producer"):
        """Async connection health check"""
        try:
            current_time = time.time()
            if current_time - self._last_heartbeat_check < self._heartbeat_interval:
                return True
            
            if connection_type == "producer":
                if (self.producer_connection and 
                    not self.producer_connection.is_closed and 
                    self.producer_channel and 
                    not self.producer_channel.is_closed):
                    # Test connection with a lightweight operation
                    await asyncio.wait_for(
                        self.producer_channel.declare_queue('__health_check__', passive=True, arguments={'x-expires': 1000}),
                        timeout=5.0
                    )
                    self._last_heartbeat_check = current_time
                    return True
            else:  # consumer
                if (self.consumer_connection and 
                    not self.consumer_connection.is_closed and 
                    self.consumer_channel and 
                    not self.consumer_channel.is_closed):
                    await asyncio.wait_for(
                        self.consumer_channel.declare_queue('__health_check__', passive=True, arguments={'x-expires': 1000}),
                        timeout=5.0
                    )
                    self._last_heartbeat_check = current_time
                    return True
            
            return False
        except (asyncio.TimeoutError, Exception) as e:
            self.logs.write_logs(f"Async connection health check failed for {connection_type}: {e}", LOG_LEVEL.WARNING)
            return False

    async def _ensure_producer_connection(self):
        """Ensure producer connection is active with async health check"""
        if (not self.producer_connection or 
            self.producer_connection.is_closed or 
            not self.producer_channel or 
            self.producer_channel.is_closed ):#or not await self._health_check_connection("producer")):
            
            self.logs.write_logs("Recreating async producer connection due to health check failure", LOG_LEVEL.INFO)
            try:
                if self.producer_connection and not self.producer_connection.is_closed:
                    await self.producer_connection.close()
            except Exception as e:
                self.logs.write_logs(f"Error closing old async producer connection: {e}", LOG_LEVEL.WARNING)
            
            await self.__connect_producer()

    async def _ensure_consumer_connection(self):
        """Ensure consumer connection is active with async health check"""
        if (not self.consumer_connection or 
            self.consumer_connection.is_closed or 
            not self.consumer_channel or 
            self.consumer_channel.is_closed):#or not await self._health_check_connection("consumer")):
            
            self.logs.write_logs("Recreating async consumer connection due to health check failure", LOG_LEVEL.INFO)
            try:
                if self.consumer_connection and not self.consumer_connection.is_closed:
                    await self.consumer_connection.close()
            except Exception as e:
                self.logs.write_logs(f"Error closing old async consumer connection: {e}", LOG_LEVEL.WARNING)
            
            await self.__connect_consumer()

    async def __connect_producer(self):
        """Connect producer with retry logic and proper heartbeat settings"""
        for attempt in range(self.max_retries):
            try:
                if not self.producer_connection:
                    # Minimal connection - server controls all connection settings
                    self.producer_connection = await aio_pika.connect_robust(
                        host=self.__parsed.hostname,
                        port=self.__parsed.port,
                        login=self.__credentials.username if self.__credentials else "guest",
                        password=self.__credentials.password if self.__credentials else "guest"
                        # All other settings controlled by server (heartbeat, timeouts, etc.)
                    )
                    self.producer_channel = await self.producer_connection.channel()
                    # Server controls prefetch_count via consumer_prefetch setting
                    # await self.producer_channel.set_qos(prefetch_count=self.prefetch_count)  # Removed
                    
                    # Declare exchange if not using default
                    if self.exchange_name:
                        await self.producer_channel.declare_exchange(
                            name=self.exchange_name,
                            type=getattr(aio_pika.ExchangeType, self.exchange_type.upper()),
                            durable=self.exchange_durable
                        )
                        self.logs.write_logs(f"Async exchange '{self.exchange_name}' declared (type: {self.exchange_type})", LOG_LEVEL.INFO)
                    
                    self.logs.write_logs(f"Async RMQ producer connection established (attempt {attempt + 1})", LOG_LEVEL.INFO)
                    return
            except Exception as e:
                self.logs.write_logs(f"Async RMQ producer connection attempt {attempt + 1} failed: {e}", LOG_LEVEL.WARNING)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logs.write_logs(f"Failed to establish async RMQ producer connection after {self.max_retries} attempts", LOG_LEVEL.ERROR)
                    raise

    async def __connect_consumer(self):
        """Connect consumer with retry logic and proper heartbeat settings"""
        for attempt in range(self.max_retries):
            try:
                if not self.consumer_connection:
                    # Minimal connection - server controls all connection settings
                    self.consumer_connection = await aio_pika.connect_robust(
                        host=self.__parsed.hostname,
                        port=self.__parsed.port,
                        login=self.__credentials.username if self.__credentials else "guest",
                        password=self.__credentials.password if self.__credentials else "guest"
                        # All other settings controlled by server (heartbeat, timeouts, etc.)
                    )
                    self.consumer_channel = await self.consumer_connection.channel()
                    # Server controls prefetch_count via consumer_prefetch setting
                    # await self.consumer_channel.set_qos(prefetch_count=self.prefetch_count)  # Removed
                    
                    # Declare exchange if not using default
                    if self.exchange_name:
                        await self.consumer_channel.declare_exchange(
                            name=self.exchange_name,
                            type=getattr(aio_pika.ExchangeType, self.exchange_type.upper()),
                            durable=self.exchange_durable
                        )
                        self.logs.write_logs(f"Async exchange '{self.exchange_name}' declared (type: {self.exchange_type})", LOG_LEVEL.INFO)
                    
                    self.logs.write_logs(f"Async RMQ consumer connection established (attempt {attempt + 1})", LOG_LEVEL.INFO)
                    return
            except Exception as e:
                self.logs.write_logs(f"Async RMQ consumer connection attempt {attempt + 1} failed: {e}", LOG_LEVEL.WARNING)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logs.write_logs(f"Failed to establish async RMQ consumer connection after {self.max_retries} attempts", LOG_LEVEL.ERROR)
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
                    self.logs.write_logs(f"Async queue '{queue_name}' bound to exchange '{exchange}' with routing key '{binding_key}'", LOG_LEVEL.INFO)
                else:
                    self.logs.write_logs(f"Async queue '{queue_name}' declared (durable={queue_durable})", LOG_LEVEL.INFO)
                self._declared_queues[queue_name]=queue
            except Exception as e:
                self.logs.write_logs(f"Failed to declare async queue '{queue_name}': {e}", LOG_LEVEL.ERROR)
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
                self.logs.write_logs(f"Async producer exchange '{exchange}' declared (type: {ex_type})", LOG_LEVEL.INFO)
            except Exception as e:
                self.logs.write_logs(f"Failed to declare async producer exchange '{exchange}': {e}", LOG_LEVEL.ERROR)
                raise
        
        self.logs.write_logs(f"Async producer connection established", LOG_LEVEL.INFO)

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
                self.logs.write_logs(f"Async consumer exchange '{exchange}' declared (type: {ex_type})", LOG_LEVEL.INFO)
            except Exception as e:
                self.logs.write_logs(f"Failed to declare async consumer exchange '{exchange}': {e}", LOG_LEVEL.ERROR)
                raise
        
        self.logs.write_logs(f"Async consumer connection established", LOG_LEVEL.INFO)

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
                    self.logs.write_logs(f"Published async message to exchange '{exchange}' with routing key '{routing}'", LOG_LEVEL.INFO)
                else:
                    await self.producer_channel.default_exchange.publish(
                        message,
                        routing_key=queue_name
                    )
                    self.logs.write_logs(f"Published async message to queue '{queue_name}'", LOG_LEVEL.INFO)
                
                return True
                
            except Exception as e:
                self.logs.write_logs(f"Async RMQ publish attempt {attempt + 1} failed: {e}", LOG_LEVEL.WARNING)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    # Force reconnection on next attempt
                    self.producer_connection = None
                    self.producer_channel = None
                    continue
                else:
                    self.logs.write_logs(f"Failed to async publish after {self.max_retries} attempts", LOG_LEVEL.ERROR)
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
                        self.logs.write_logs(f"Async message processed successfully from queue '{queue_name}'", LOG_LEVEL.INFO)
                        return result
                    except pkl.UnpicklingError as e:
                        self.logs.write_logs(f"Failed to deserialize async message from queue '{queue_name}': {e}", LOG_LEVEL.ERROR)
                        await message.nack(requeue=False)
                    except Exception as e:
                        self.logs.write_logs(f"Error handling async message from queue '{queue_name}': {e}", LOG_LEVEL.ERROR)
                        self.logs.write_logs(traceback.format_exc(), LOG_LEVEL.DEBUG)
                        await message.nack(requeue=True)

            self._consumer_callbacks.append((queue_name, callback))  # Store callback, not inner_func
            return callback

        return decorator(func) if func else decorator

    async def start_consuming(self):
        """Start consuming with proper error handling"""
        self.logs.write_logs(f"Async consumer channel exists: {self.consumer_channel is not None}", LOG_LEVEL.DEBUG)
        self.logs.write_logs(f"Async consumer channel closed: {self.consumer_channel.is_closed if self.consumer_channel else 'N/A'}", LOG_LEVEL.DEBUG)
        self.logs.write_logs(f"Async registered callbacks: {len(self._consumer_callbacks)}", LOG_LEVEL.DEBUG)
        
        if not self.consumer_channel:
            self.logs.write_logs("No async consumer channel available. Call create_consumer() first.", LOG_LEVEL.ERROR)
            return

        if not self._consumer_callbacks:
            self.logs.write_logs("No async consumer callbacks registered. Use @rmq.consume_messages() decorator first.", LOG_LEVEL.ERROR)
            return

        self.logs.write_logs("Starting async RMQ message consumption...", LOG_LEVEL.INFO)
        try:
            await self._ensure_consumer_connection()

            for queue_name, handler in self._consumer_callbacks:
                try:
                    # Ensure queue exists before consuming
                    if queue_name in self._declared_queues:
                        queue = self._declared_queues[queue_name]
                        await queue.consume(handler)
                        self.logs.write_logs(f"Started async consuming from queue '{queue_name}'", LOG_LEVEL.INFO)
                except Exception as e:
                    self.logs.write_logs(f"Error setting up async consumer for queue '{queue_name}': {e}", LOG_LEVEL.ERROR)
                    raise

            self.logs.write_logs(" [*] Async consumer started. Waiting for messages...", LOG_LEVEL.INFO)
            # Keep the connection alive
            await asyncio.Event().wait()
            
        except KeyboardInterrupt:
            self.logs.write_logs("Async consumption interrupted by user", LOG_LEVEL.INFO)
            await self.stop_consuming()
        except Exception as e:
            self.logs.write_logs(f"Error during async consumption: {e}", LOG_LEVEL.ERROR)
            self.logs.write_logs(traceback.format_exc(), LOG_LEVEL.DEBUG)
            raise
        finally:
            self.logs.write_logs("Async RMQ consumption stopped", LOG_LEVEL.INFO)

    async def stop_consuming(self):
        """Stop consuming messages"""
        try:
            if self.consumer_channel and not self.consumer_channel.is_closed:
                # Close the consumer channel to stop all consumers
                await self.consumer_channel.close()
                self.logs.write_logs("Async RMQ consumption stopped", LOG_LEVEL.INFO)
        except Exception as e:
            self.logs.write_logs(f"Error stopping async consumption: {e}", LOG_LEVEL.ERROR)

    def get_declared_queues(self) -> list:
        """Get list of declared queue names"""
        return list(self._declared_queues.keys())

    def is_queue_declared(self, queue_name: str) -> bool:
        """Check if a queue has been declared"""
        return queue_name in self._declared_queues

    async def is_connected(self) -> bool:
        """Check if async connections are active and healthy"""
        try:
            producer_ok = (self.producer_connection and 
                         not self.producer_connection.is_closed and
                         self.producer_channel and 
                         not self.producer_channel.is_closed )#and await self._health_check_connection("producer"))
            
            consumer_ok = (self.consumer_connection and 
                         not self.consumer_connection.is_closed and
                         self.consumer_channel and 
                         not self.consumer_channel.is_closed )#and await self._health_check_connection("consumer"))
            
            return producer_ok or consumer_ok
        except Exception as e:
            self.logs.write_logs(f"Error checking async connection health: {e}", LOG_LEVEL.WARNING)
            return False
    
    async def get_connection_info(self) -> dict:
        """Get detailed async connection information for debugging"""
        return {
            "producer_connected": self.producer_connection and not self.producer_connection.is_closed,
            "consumer_connected": self.consumer_connection and not self.consumer_connection.is_closed,
            "producer_channel_open": self.producer_channel and not self.producer_channel.is_closed,
            "consumer_channel_open": self.consumer_channel and not self.consumer_channel.is_closed,
            "last_heartbeat_check": self._last_heartbeat_check,
            "heartbeat_interval": self._heartbeat_interval,
            "declared_queues": list(self._declared_queues.keys()),
            "note": "All connection settings controlled by RabbitMQ server"
        }



