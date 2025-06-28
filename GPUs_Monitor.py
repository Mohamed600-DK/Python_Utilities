import pynvml


def get_available_gpu_index(current_gpu_index=0, threshold=0.8):
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        for i in range(current_gpu_index, device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                used_ratio = mem_info.used / mem_info.total
                if used_ratio < threshold:
                        return i
        return None