import boto3
import logging
from botocore.exceptions import BotoCoreError, ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_text(local_file, region_name, aws_access_key_id, aws_secret_access_key):
    """
    Detects text from a local file using Amazon Textract or pytesseract fallback.
    
    :param local_file: Path to the local file to be analyzed.
    :param region_name: AWS region name for Textract.
    :param aws_access_key_id: AWS access key ID.
    :param aws_secret_access_key: AWS secret access key.
    :return: Extracted text or error message.
    """
    try:
        # Try AWS Textract first
        textract = boto3.client(
            'textract', 
            region_name=region_name, 
            aws_access_key_id=aws_access_key_id, 
            aws_secret_access_key=aws_secret_access_key
        )

        with open(local_file, 'rb') as document:
            response = textract.detect_document_text(Document={'Bytes': document.read()})

        text_lines = [
            item["Text"]
            for item in response.get("Blocks", [])
            if item.get("BlockType") == "LINE"
        ]
        extracted_text = " ".join(text_lines)
        logger.info(f"Successfully extracted text from {local_file} using AWS Textract")
        return extracted_text

    except Exception as aws_error:
        # Fallback to pytesseract
        logger.warning(f"AWS Textract failed: {aws_error}. Falling back to pytesseract")
        try:
            import pytesseract
            from PIL import Image
            import os
            
            # Set Tesseract path for Windows
            if os.name == 'nt':  # Windows
                possible_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    os.path.expanduser(r'~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe')
                ]
                for tesseract_path in possible_paths:
                    if os.path.exists(tesseract_path):
                        pytesseract.pytesseract.tesseract_cmd = tesseract_path
                        logger.info(f"Using Tesseract from: {tesseract_path}")
                        break
            
            # Open image and extract text
            image = Image.open(local_file)
            extracted_text = pytesseract.image_to_string(image)
            logger.info(f"Successfully extracted text from {local_file} using pytesseract")
            return extracted_text
            
        except ImportError:
            logger.error("pytesseract not installed. Install with: pip install pytesseract pillow")
            logger.error("Also install Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki")
            return "Error: OCR libraries not available"
        except FileNotFoundError:
            logger.error(f"File {local_file} not found.")
            return "Error: File not found."
        except Exception as e:
            logger.error(f"pytesseract error: {e}")
            return f"Error: {e}"
