#!/usr/bin/env python3.10


from typing import Union,List
import cv2
from PIL import Image
import numpy as np
import base64
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def crop_image_bbox(image:Union[np.ndarray,cv2.typing.MatLike],face_bbox:List[int],box_size:int=280) -> Image.Image:
    """
    Crops an area of the image centered on the face bounding box, using a specified square box size.
    The bounding box is defined by its top-left and bottom-right corners.

    Parameters:
    - image: The input image (numpy array).
    - bbox: A tuple or list (x1, y1, x2, y2) representing the bounding box corners of the face.
    - box_size: The size (width and height) of the square box for cropping.

    Returns:
    - Cropped image (numpy array) of the specified square box size centered on the face bbox.
    """
    x1, y1, x2, y2 = face_bbox
    # Calculate the center of the face bounding box
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    # Calculate the square box coordinates
    x_start = max(0, cx - box_size // 2)
    y_start = max(0, cy - box_size // 2)
    x_end = min(image.shape[1], cx + box_size // 2)
    y_end = min(image.shape[0], cy + box_size // 2)
    # Crop and return the image
    cropped_image = image[y_start:y_end, x_start:x_end]
    return cropped_image
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def crop_image_center(frame,crop_width=None,crop_height=None):
    # Get the frame dimensions
    frame_height, frame_width = frame.shape[:2]
    if(not crop_width):
        crop_width=frame_width
    if(not crop_height):
        crop_height=frame_width
    # Calculate the center of the frame
    center_x, center_y = frame_width // 2, frame_height // 2
    # Calculate the top-left and bottom-right points for the crop
    x1 = max(0, center_x - crop_width // 2)
    y1 = max(0, center_y - crop_height // 2)
    x2 = min(frame_width, center_x + crop_width // 2)
    y2 = min(frame_height, center_y + crop_height // 2)
    # Crop the frame
    cropped_frame = frame[y1:y2, x1:x2]
    return cropped_frame
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def encoded64image2cv2(ImageBase64:str)->cv2.Mat:
    if  ImageBase64 is None:
        return None
    image_decode = base64.b64decode(ImageBase64)
    np_arr = np.frombuffer(image_decode, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return image