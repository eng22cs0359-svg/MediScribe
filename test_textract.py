import sys
sys.path.insert(0, 'api')

from ml_model.ml_model import detect_text
from config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

print("Testing AWS Textract...")
print("-" * 60)

file_path = "./api/images/prescriptions/check2.jpeg"
print(f"Processing: {file_path}")
print("-" * 60)

extracted_text = detect_text(file_path, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

print("\nExtracted Text:")
print("=" * 60)
print(extracted_text)
print("=" * 60)
print(f"\nText length: {len(extracted_text)} characters")
