# GPUs_Monitor.py

GPU monitoring utilities for finding available GPU resources based on memory usage.

## Functions

### `get_available_gpu_index(current_gpu_index=0, threshold=0.8)`
- Finds the first available GPU with memory usage below the threshold
- **Parameters:**
  - `current_gpu_index`: Starting GPU index to check (default: 0)
  - `threshold`: Memory usage threshold (0.0-1.0, default: 0.8)
- **Returns:** GPU index if available, None if no GPU meets criteria
- **Requires:** `pynvml` library for NVIDIA GPU monitoring

## Usage Example

```python
from common_utilities import get_available_gpu_index

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

## Requirements

- `pynvml>=12.0.0` - NVIDIA Management Library for Python

## Installation

```python
from common_utilities import get_available_gpu_index
```

---
[Back to Main README](../README.md)
