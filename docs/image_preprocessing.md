# image_preprocessing.py

Image processing utilities for cropping and format conversion operations.

## Functions

### `crop_image_bbox(image, face_bbox, box_size=280)`
- Crops a square region centered on a bounding box
- **Parameters:**
  - `image`: Input image as numpy array or cv2.Mat
  - `face_bbox`: List [x1, y1, x2, y2] defining the bounding box
  - `box_size`: Size of the square crop (default: 280)
- **Returns:** Cropped image as PIL Image
- Ensures the crop stays within image boundaries

### `crop_image_center(frame, crop_width=None, crop_height=None)`
- Crops a region from the center of an image
- **Parameters:**
  - `frame`: Input image/frame
  - `crop_width`: Width of crop (default: original width)
  - `crop_height`: Height of crop (default: original width)
- **Returns:** Cropped frame
- Automatically handles boundary constraints

### `encoded64image2cv2(ImageBase64: str)`
- Converts a base64 encoded image string to OpenCV format
- **Parameters:**
  - `ImageBase64`: Base64 encoded image string
- **Returns:** OpenCV image (cv2.Mat) or None if input is None
- Handles the complete decode pipeline from base64 to cv2 format

## Usage Example

```python
import cv2
from common_utilities import crop_image_bbox, crop_image_center, encoded64image2cv2

# Load an image
image = cv2.imread("photo.jpg")

# Crop around a detected face
face_bbox = [100, 100, 200, 200]  # x1, y1, x2, y2
cropped_face = crop_image_bbox(image, face_bbox, box_size=224)

# Crop center region
center_crop = crop_image_center(image, crop_width=300, crop_height=300)

# Convert base64 to cv2
base64_string = "your_base64_image_string"
cv2_image = encoded64image2cv2(base64_string)
```

## Requirements

- `opencv-python>=4.11.0.86` - Computer vision library
- `Pillow>=11.2.1` - Python Imaging Library
- `numpy>=2.2.6` - Numerical computing library

## Installation

```python
from common_utilities import crop_image_bbox, crop_image_center, encoded64image2cv2
```

---
[Back to Main README](../README.md)
