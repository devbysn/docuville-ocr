# # src/main.py
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from api.routes import router
# import uvicorn
# from dotenv import load_dotenv
# import os

# load_dotenv()

# app = FastAPI(title="Document Processing API")

# # Configure CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"],  # Vite's default port
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(router, prefix="/api")

# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=int(os.getenv("PORT", 8000)),
#         reload=True
#     )



# main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pytesseract
from PIL import Image
import io
import re
import json
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure Tesseract path - important for MacOS
# You might need to adjust this path based on your installation
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DocumentResponse(BaseModel):
    documentType: str
    documentNumber: str
    fullName: str
    fatherName: Optional[str]
    dateOfBirth: Optional[str]
    dateOfExpiry: Optional[str]
    isValid: bool

def preprocess_image(image):
    """Preprocess image to improve OCR accuracy"""
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize while maintaining aspect ratio
    max_size = 2000
    ratio = min(max_size/image.width, max_size/image.height)
    new_size = (int(image.width * ratio), int(image.height * ratio))
    image = image.resize(new_size, Image.LANCZOS)
    
    return image

def extract_pan_details(text: str) -> dict:
    """Extract PAN card details from OCR text"""
    logger.debug(f"Raw OCR text:\n{text}")
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    logger.debug(f"Processed lines:\n{lines}")
    
    result = {
        'documentType': 'pan_card',
        'documentNumber': '',
        'fullName': '',
        'fatherName': '',
        'dateOfBirth': '',
        'isValid': False
    }
    
    # PAN number pattern: 5 alphabets + 4 numbers + 1 alphabet
    pan_pattern = r'[A-Z]{5}[0-9]{4}[A-Z]{1}'
    
    for line in lines:
        logger.debug(f"Processing line: {line}")
        
        # Extract PAN number
        pan_match = re.search(pan_pattern, line)
        if pan_match:
            result['documentNumber'] = pan_match.group()
            logger.debug(f"Found PAN number: {result['documentNumber']}")
        
        # Extract name (looking for common patterns)
        if any(keyword in line.upper() for keyword in ['NAME', 'नाम']):
            # Split on common delimiters and clean
            parts = re.split(r'[:/]', line)
            if len(parts) > 1:
                result['fullName'] = parts[1].strip()
                logger.debug(f"Found name: {result['fullName']}")
        
        # Extract father's name
        if any(keyword in line.upper() for keyword in ["FATHER", "FATHER'S", 'पिता']):
            parts = re.split(r'[:/]', line)
            if len(parts) > 1:
                result['fatherName'] = parts[1].strip()
                logger.debug(f"Found father's name: {result['fatherName']}")
        
        # Extract date of birth
        date_patterns = [
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}',
            r'\d{2}\.\d{2}\.\d{4}'
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, line)
            if date_match and not result['dateOfBirth']:
                result['dateOfBirth'] = date_match.group()
                logger.debug(f"Found DOB: {result['dateOfBirth']}")
                break
    
    # Basic validation
    result['isValid'] = bool(
        result['documentNumber'] and 
        result['fullName'] and 
        result['dateOfBirth']
    )
    
    logger.debug(f"Final extracted result: {result}")
    return result

@app.post("/api/process-document/")
async def process_document(
    file: UploadFile = File(...),
    documentType: str = "pan_card"
):
    try:
        logger.info(f"Processing document type: {documentType}")
        logger.info(f"Received file: {file.filename}")
        
        # Read and process the image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Preprocess the image
        processed_image = preprocess_image(image)
        
        # Configure Tesseract parameters
        custom_config = r'--oem 3 --psm 3'
        
        # Perform OCR
        logger.info("Starting OCR processing")
        text = pytesseract.image_to_string(
            processed_image,
            config=custom_config,
            lang='eng'  # you can add +hin for Hindi support if needed
        )
        logger.info("OCR processing completed")
        
        # Process based on document type
        if documentType == "pan_card":
            result = extract_pan_details(text)
            logger.info("Document processing completed")
            return result
        else:
            raise HTTPException(status_code=400, detail="Unsupported document type")
    
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)