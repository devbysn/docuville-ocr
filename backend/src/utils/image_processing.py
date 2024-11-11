# src/utils/image_processing.py
import cv2
import numpy as np
from PIL import Image
import io

def preprocess_image(image_bytes: bytes) -> np.ndarray:
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Get original dimensions
    height, width = img.shape[:2]
    
    # Resize if image is too large (keeping aspect ratio)
    max_dimension = 1800
    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        img = cv2.resize(img, None, fx=scale, fy=scale)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Noise removal
    kernel = np.ones((1, 1), np.uint8)
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    # Deskew image
    coords = np.column_stack(np.where(opening > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    center = (width // 2, height // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        opening, M, (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    
    # Increase contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(rotated)
    
    # Additional denoising
    denoised = cv2.fastNlMeansDenoising(enhanced)
    
    return denoised

def process_document_image(image_bytes: bytes) -> Image.Image:
    # Preprocess using OpenCV
    processed_array = preprocess_image(image_bytes)
    
    # Convert to PIL Image
    pil_image = Image.fromarray(processed_array)
    
    # Increase resolution for better OCR
    scale_factor = 2
    width, height = pil_image.size
    pil_image = pil_image.resize(
        (width * scale_factor, height * scale_factor),
        Image.Resampling.LANCZOS
    )
    
    return pil_image