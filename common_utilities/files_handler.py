import os
from functools import lru_cache
import re
import json
import io
import orjson
from typing import Dict, Union

__APP_DIRS_PATHS={}
__NAMESPACES=None
@lru_cache(maxsize=1)
def get_root_path(start=__file__,APP_HEAD="main.py"):
    """
    Walks up the directory tree from the current file until it finds the marker file or directory.
    Returns the directory containing the marker, or the current file's parent if not found.
    """
    root_dir=os.getenv("APP_ROOT",None)
    if root_dir is not None and os.path.exists(root_dir):
        return root_dir
    current_dir = os.path.abspath(os.path.dirname(start))
    root_dir = os.path.abspath(os.sep)
    while True:
        marker_path = os.path.join(current_dir, APP_HEAD)
        if os.path.exists(marker_path):
            return current_dir
        if current_dir == root_dir:
            # Marker not found, fallback to previous behavior
            return os.path.dirname(os.path.dirname(os.path.abspath(start)))
        current_dir = os.path.dirname(current_dir)
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def set_paths(APP_PATHS):
    __APP_DIRS_PATHS.update(APP_PATHS)
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
@lru_cache(maxsize=1)
def get_paths():
    return __APP_DIRS_PATHS
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def set_namespace(namespace):
    global __NAMESPACES
    __NAMESPACES=namespace
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
@lru_cache(maxsize=1)
def get_namespace():
    return __NAMESPACES
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
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
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def create_logfile(log_name):
    log_path=__APP_DIRS_PATHS["LOGS_ROOT_PATH"] if "LOGS_ROOT_PATH" in __APP_DIRS_PATHS and __APP_DIRS_PATHS["LOGS_ROOT_PATH"] is not None else os.getenv("LOGS_ROOT_PATH",None)
    if log_path is None:
        raise ValueError("LOGS_ROOT_PATH is not set in 'APP_DIRS_PATHS' or in 'env' variables.")
    
    if __NAMESPACES:
        logs_dir=os.path.join(log_path,__NAMESPACES,"logs")
    else:
        logs_dir=os.path.join(log_path,"logs")

    os.makedirs(logs_dir,exist_ok=True)
    file_path=os.path.join(logs_dir,f"{log_name}.log")
    if os.path.exists(file_path):
        os.remove(file_path)
    return file_path
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def write_json(write_data, file_path):
    """
    Writes data to a JSON file using optimized serialization.

    Args:
        write_data: The data to serialize and save.
        file_path: Path to the file where data will be written.
    """
    # Open the file in binary write mode using BufferedWriter for optimized writing
    with io.BufferedWriter(open(file_path, "wb")) as json_f:
        
        # Use orjson to serialize the data with an indentation of 2 spaces for readability
        json_data = orjson.dumps(write_data, option=orjson.OPT_INDENT_2)
        
        # Write the serialized data to the file
        json_f.write(json_data)
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def read_json(file_path) -> Dict:
    """
    Reads and deserializes data from a JSON file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        Dict: Parsed JSON data or an empty dictionary if file does not exist or is empty.
    """
    # Check if the file exists, and if not, create an empty file
    if not os.path.exists(file_path):
        with open(file_path, "w") as json_f:
            json_f=json.dump({"clients":[]},json_f)
    # Open the file in binary read mode using BufferedReader for efficient reading
    with io.BufferedReader(open(file_path, "rb")) as json_f:
        # Read the content of the file
        read_data = json_f.read()
        # If the file is not empty, deserialize the JSON data; otherwise, return an empty dictionary
        return json.loads(read_data) if read_data else {"clients":[]}