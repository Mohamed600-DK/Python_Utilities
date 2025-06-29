# Standard library or always-safe imports
from .Base_Processing import Base_process
from .Base_Threading import Base_Thread
from .files_handler import get_root_path, get_direct_download_link,set_paths,set_namespace,get_paths,get_namespace
from .logger import LOGGER, LOG_LEVEL
__all__ = [
    "Base_process",
    "Base_Thread",
    "get_root_path",
    "get_direct_download_link",
    "LOGGER",
    "LOG_LEVEL",
    "set_paths",
    "set_namespace","get_paths","get_namespace"
]
# GPU Monitoring
try:
    from .GPUs_Monitor import get_available_gpu_index
    __all__.append("get_available_gpu_index")
except ImportError:
    def get_available_gpu_index():
        from .GPUs_Monitor import get_available_gpu_index as fn
        return fn
    __all__.append("get_available_gpu_index")
# Image Preprocessing
try:
    from .image_preprocessing import (
        crop_image_bbox,
        crop_image_center,
        encoded64image2cv2
    )
    __all__.extend(["crop_image_bbox", "crop_image_center", "encoded64image2cv2"])
except ImportError:
    def get_crop_image_bbox():
        from .image_preprocessing import crop_image_bbox
        return crop_image_bbox
    def get_crop_image_center():
        from .image_preprocessing import crop_image_center
        return crop_image_center
    def get_encoded64image2cv2():
        from .image_preprocessing import encoded64image2cv2
        return encoded64image2cv2
    __all__.extend(["get_crop_image_bbox", "get_crop_image_center", "get_encoded64image2cv2"])
# Redis Handler
try:
    from .RedisHandler import RedisHandler
    __all__.append("RedisHandler")
except ImportError:
    def get_redis_handler():
        from .RedisHandler import RedisHandler
        return RedisHandler
    __all__.append("get_redis_handler")