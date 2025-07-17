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
- `pika>=1.3.0` for RabbitMQ synchronous messaging
- `aio-pika>=9.0.0` for RabbitMQ asynchronous messaging

**Python Version**: Requires Python 3.10 or higher

## Quick Start

After installation, you can import and use the utilities:

```python
from common_utilities import LOGGER, LOG_LEVEL, Base_process, get_available_gpu_index, Sync_RMQ, Async_RMQ

# Create a logger
logger = LOGGER("MyApp")
logger.create_Stream_logger()
logger.write_logs("Hello from common utilities!", LOG_LEVEL.INFO)

# Check for available GPU
gpu_index = get_available_gpu_index()
if gpu_index is not None:
    print(f"Available GPU: {gpu_index}")

# RabbitMQ example
with Sync_RMQ("localhost:5672") as rmq:
    rmq.create_producer()
    rmq.create_queues("my_queue")
    rmq.publish_data({"message": "Hello RabbitMQ!"}, queue_name="my_queue")
```

## Modules Overview

This repository contains the following utility modules. Click on each module name to view detailed documentation:

### [Base_Processing.py](docs/Base_Processing.md)

### [Base_Threading.py](docs/Base_Threading.md)

### [files_handler.py](docs/files_handler.md)

### [GPUs_Monitor.py](docs/GPUs_Monitor.md)

### [image_preprocessing.py](docs/image_preprocessing.md)

### [logger.py](docs/logger.md)

### [RedisHandler.py](docs/RedisHandler.md)

### [RMQ.py](docs/RMQ.md)

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
