import os
from functools import lru_cache
import re


__APP_DIRS_PATHS={}
__NAMESPACES=None
@lru_cache(maxsize=1)
def get_root_path(APP_HEAD="main.py"):
    """
    Walks up the directory tree from the current file until it finds the marker file or directory.
    Returns the directory containing the marker, or the current file's parent if not found.
    """
    current_dir = os.path.abspath(os.path.dirname(__file__))
    root_dir = os.path.abspath(os.sep)
    while True:
        marker_path = os.path.join(current_dir, APP_HEAD)
        if os.path.exists(marker_path):
            return current_dir
        if current_dir == root_dir:
            # Marker not found, fallback to previous behavior
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        current_dir = os.path.dirname(current_dir)


def set_paths(APP_PATHS):
    __APP_DIRS_PATHS.update(APP_PATHS)

@lru_cache(maxsize=1)
def get_paths():
    return __APP_DIRS_PATHS


def set_namespace(namespace):
    global __NAMESPACES
    __NAMESPACES=namespace

@lru_cache(maxsize=1)
def get_namespace():
    return __NAMESPACES

def get_direct_download_link(sharing_link):
    # Extract the file ID from the sharing link
    file_id_match = re.search(r"/d/([a-zA-Z0-9_-]+)", sharing_link)
    if file_id_match:
        file_id = file_id_match.group(1)
    else:
        raise ValueError("Could not extract file ID from the provided link.")
    
    # Construct the direct download link
    direct_link = f"https://drive.google.com/uc?id={file_id}&export=download"
    return direct_link 


def create_logfile(log_name):
    if __NAMESPACES:
        logs_dir=os.path.join(__APP_DIRS_PATHS["LOGS_ROOT_PATH"],__NAMESPACES,"logs")
    else:
        logs_dir=os.path.join(__APP_DIRS_PATHS["LOGS_ROOT_PATH"],"logs")

    os.makedirs(logs_dir,exist_ok=True)
    file_path=os.path.join(logs_dir,f"{log_name}.log")
    if os.path.exists(file_path):
        os.remove(file_path)
    return file_path