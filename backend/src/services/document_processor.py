# # src/services/document_processor.py
# from PIL import Image
# import pytesseract
# import io
# import re
# from datetime import datetime
# from pydantic import BaseModel
# from typing import Optional, Tuple, List
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class DocumentData(BaseModel):
#     documentType: str
#     documentNumber: str
#     fullName: str
#     fathersName: Optional[str]  # Added for PAN card
#     dateOfBirth: Optional[str]  # Renamed from dateOfIssue
#     dateOfExpiry: Optional[str]
#     isValid: bool

# class DocumentProcessingError(Exception):
#     """Custom exception for document processing errors"""
#     pass

# def preprocess_image(image_bytes: bytes) -> Image.Image:
#     """
#     Preprocess the document image for better OCR results.
#     """
#     try:
#         # Convert bytes to PIL Image
#         image = Image.open(io.BytesIO(image_bytes))
        
#         # Convert to grayscale
#         image = image.convert('L')
        
#         # Enhance contrast for better text recognition
#         from PIL import ImageEnhance
#         enhancer = ImageEnhance.Contrast(image)
#         image = enhancer.enhance(1.5)  # Increase contrast
        
#         # Optional: Add denoising if needed
#         # Optional: Add thresholding if needed
        
#         return image
#     except Exception as e:
#         logger.error(f"Image preprocessing failed: {str(e)}")
#         raise DocumentProcessingError(f"Failed to preprocess image: {str(e)}")

# def extract_pan_number(text: str) -> str:
#     """
#     Extract PAN number from text.
#     PAN format: AAAAA9999A (5 letters, 4 numbers, 1 letter)
#     """
#     # Standard PAN pattern
#     pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'
#     match = re.search(pan_pattern, text)
#     if match:
#         return match.group(0)
#     return ""

# def extract_names_pan(text: str) -> Tuple[str, str]:
#     """
#     Extract name and father's name from PAN card text.
#     Returns tuple of (name, father's name)
#     """
#     name = ""
#     fathers_name = ""
    
#     lines = [line.strip() for line in text.split('\n') if line.strip()]
    
#     for i, line in enumerate(lines):
#         # Look for name indicators
#         if 'name' in line.lower() and not 'father' in line.lower():
#             # Extract name after the indicator
#             parts = line.lower().split('name')
#             if len(parts) > 1 and parts[1].strip():
#                 name = parts[1].strip().upper()
        
#         # Look for father's name indicators
#         if "father's name" in line.lower() or "father" in line.lower():
#             parts = line.lower().split('name')
#             if len(parts) > 1 and parts[1].strip():
#                 fathers_name = parts[1].strip().upper()
    
#     return name, fathers_name

# def extract_dob(text: str) -> Optional[str]:
#     """
#     Extract date of birth from PAN card text.
#     Common format: DD/MM/YYYY
#     """
#     # Look for date patterns near "Date of Birth" or "DOB"
#     dob_pattern = r'(?:Date of Birth|DOB|जन्म की तारीख).*?(\d{2}[/-]\d{2}[/-]\d{4})'
#     match = re.search(dob_pattern, text, re.IGNORECASE)
    
#     if match:
#         date_str = match.group(1)
#         try:
#             # Convert to standard format
#             date_obj = datetime.strptime(date_str, '%d/%m/%Y')
#             return date_obj.strftime('%Y-%m-%d')
#         except ValueError:
#             try:
#                 date_obj = datetime.strptime(date_str, '%d-%m-%Y')
#                 return date_obj.strftime('%Y-%m-%d')
#             except ValueError:
#                 return None
#     return None

# async def process_document_image(image_bytes: bytes, document_type: str) -> DocumentData:
#     """
#     Process document image and extract relevant information.
#     """
#     try:
#         logger.info(f"Starting document processing for type: {document_type}")
        
#         # Preprocess the image
#         pil_image = preprocess_image(image_bytes)
        
#         # Configure Tesseract with Indian language support
#         custom_config = r'--oem 3 --psm 3 -l eng+hin'
        
#         # Extract text
#         extracted_text = pytesseract.image_to_string(pil_image, config=custom_config)
#         logger.debug(f"Extracted text: {extracted_text}")
        
#         if document_type.lower() == 'pan':
#             # Extract PAN-specific information
#             doc_number = extract_pan_number(extracted_text)
#             name, fathers_name = extract_names_pan(extracted_text)
#             dob = extract_dob(extracted_text)
            
#             # PAN cards don't expire, so they're valid if they have a number
#             is_valid = bool(doc_number)
            
#             result = DocumentData(
#                 documentType='PAN',
#                 documentNumber=doc_number,
#                 fullName=name,
#                 fathersName=fathers_name,
#                 dateOfBirth=dob,
#                 dateOfExpiry=None,  # PAN cards don't expire
#                 isValid=is_valid
#             )
#         else:
#             # Handle other document types (existing code)
#             raise DocumentProcessingError(f"Unsupported document type: {document_type}")
        
#         logger.info("Document processing completed successfully")
#         return result
        
#     except Exception as e:
#         logger.error(f"Document processing failed: {str(e)}")
#         raise DocumentProcessingError(f"Failed to process document: {str(e)}")

# src/services/document_processor.py
from PIL import Image
import pytesseract
import io
import re
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Tuple, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentData(BaseModel):
    documentType: str
    documentNumber: str
    fullName: str
    fathersName: Optional[str]
    dateOfBirth: Optional[str]
    dateOfIssue: Optional[str]
    dateOfExpiry: Optional[str]
    isValid: bool

class DocumentProcessingError(Exception):
    """Custom exception for document processing errors"""
    pass

def preprocess_image(image_bytes: bytes) -> Image.Image:
    """
    Preprocess the document image for better OCR results.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert('L')  # Convert to grayscale
        
        # Enhance contrast
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        return image
    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        raise DocumentProcessingError(f"Failed to preprocess image: {str(e)}")

def extract_passport_number(text: str) -> str:
    """Extract passport number from text."""
    patterns = [
        r'[A-Z]\d{8}',  # Standard format
        r'[A-Z]{2}\d{7}',  # Alternative format
        r'\b\d{9}\b',  # Numeric only format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return ""

def extract_pan_number(text: str) -> str:
    """Extract PAN number from text."""
    pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'
    match = re.search(pan_pattern, text)
    return match.group(0) if match else ""

def extract_dates(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract dates from document text.
    Returns (date_of_birth, date_of_issue, date_of_expiry)
    """
    date_patterns = [
        r'\b\d{2}[/-]\d{2}[/-]\d{4}\b',  # DD/MM/YYYY or DD-MM-YYYY
        r'\b\d{4}[/-]\d{2}[/-]\d{2}\b',  # YYYY/MM/DD or YYYY-MM-DD
        r'\b\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{4}\b',
    ]
    
    def parse_date(date_str: str) -> Optional[str]:
        formats = ['%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y', '%Y-%m-%d', '%d %b %Y', '%d %B %Y']
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None

    dates = []
    for pattern in date_patterns:
        matches = re.finditer(pattern, text.upper())
        for match in matches:
            context = text[max(0, match.start()-20):min(len(text), match.end()+20)].upper()
            date_str = match.group(0)
            parsed_date = parse_date(date_str)
            if parsed_date:
                if any(x in context for x in ['BIRTH', 'DOB', 'BORN']):
                    return parsed_date, None, None
                elif any(x in context for x in ['ISSUE', 'ISSUED']):
                    return None, parsed_date, None
                elif any(x in context for x in ['EXPIRY', 'EXPIRES', 'VALID UNTIL']):
                    return None, None, parsed_date
                else:
                    dates.append(parsed_date)
    
    # If we couldn't identify dates by context, make best guess based on order
    dates.sort()
    return (dates[0] if dates else None,
            dates[1] if len(dates) > 1 else None,
            dates[-1] if len(dates) > 2 else None)

def extract_names(text: str, doc_type: str) -> Tuple[str, Optional[str]]:
    """Extract name and father's name from document text."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    name = ""
    fathers_name = None
    
    # Common name indicators
    name_indicators = ['name:', 'surname:', 'given names:']
    father_indicators = ["father's name:", 'father:']
    
    for line in lines:
        line_lower = line.lower()
        
        # Extract name
        if any(indicator in line_lower for indicator in name_indicators):
            for indicator in name_indicators:
                if indicator in line_lower:
                    name = line[line_lower.index(indicator) + len(indicator):].strip()
                    break
        
        # Extract father's name if present
        if any(indicator in line_lower for indicator in father_indicators):
            for indicator in father_indicators:
                if indicator in line_lower:
                    fathers_name = line[line_lower.index(indicator) + len(indicator):].strip()
                    break
    
    # If no name found with indicators, try pattern matching
    if not name:
        for line in lines:
            if re.match(r'^[A-Z][a-zA-Z\s\'-]{2,}$', line):
                non_name_words = {'PASSPORT', 'LICENSE', 'VALID', 'EXPIRES'}
                if not any(word in line.upper() for word in non_name_words):
                    name = line
                    break
    
    return name, fathers_name

async def process_document_image(image_bytes: bytes, document_type: str) -> DocumentData:
    """Process document image and extract relevant information."""
    try:
        logger.info(f"Starting document processing for type: {document_type}")
        
        # Preprocess image
        pil_image = preprocess_image(image_bytes)
        
        # Configure Tesseract
        custom_config = r'--oem 3 --psm 3'
        if document_type.lower() == 'pan':
            custom_config += ' -l eng+hin'  # Add Hindi language support for PAN cards
        
        # Extract text
        extracted_text = pytesseract.image_to_string(pil_image, config=custom_config)
        logger.debug(f"Extracted text: {extracted_text}")
        
        # Process based on document type
        if document_type.lower() == 'passport':
            doc_number = extract_passport_number(extracted_text)
            name, fathers_name = extract_names(extracted_text, 'passport')
            dob, issue_date, expiry_date = extract_dates(extracted_text)
            
            # Validate passport
            is_valid = bool(doc_number and expiry_date)
            if expiry_date:
                try:
                    expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
                    is_valid = is_valid and expiry > datetime.now()
                except ValueError:
                    is_valid = False
                    
        elif document_type.lower() == 'pan':
            doc_number = extract_pan_number(extracted_text)
            name, fathers_name = extract_names(extracted_text, 'pan')
            dob, _, _ = extract_dates(extracted_text)
            issue_date = None
            expiry_date = None
            is_valid = bool(doc_number)
            
        else:
            raise DocumentProcessingError(f"Unsupported document type: {document_type}")
        
        result = DocumentData(
            documentType=document_type.upper(),
            documentNumber=doc_number,
            fullName=name,
            fathersName=fathers_name,
            dateOfBirth=dob,
            dateOfIssue=issue_date,
            dateOfExpiry=expiry_date,
            isValid=is_valid
        )
        
        logger.info("Document processing completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Document processing failed: {str(e)}")
        raise DocumentProcessingError(f"Failed to process document: {str(e)}")