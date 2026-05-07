import sys
sys.path.insert(0, 'api')

from ml_model.ml_model import detect_text
from ml_model.ner import InitiateNER
from config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
import json

# Test with the specific prescription
file_path = "./frontend/static/temp/098a320b-11c5-11f1-a651-dffd7b96c265_14fc9ad8-e155-11ed-a634-270f5964a9bb_p2.png"

print("Extracting text from prescription...")
extracted_text = detect_text(file_path, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

print("\n" + "="*80)
print("EXTRACTED TEXT:")
print("="*80)
print(extracted_text)
print("="*80)

print("\nExtracting entities...")
ner = InitiateNER(AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
entities = ner.predict(extracted_text)

print("\n" + "="*80)
print("EXTRACTED ENTITIES:")
print("="*80)
print(json.dumps(entities, indent=2))
print("="*80)

# Show what's near "Neurokind"
if "Neurokind" in extracted_text or "neurokind" in extracted_text.lower():
    import re
    match = re.search(r'.{0,100}neurokind.{0,100}', extracted_text, re.IGNORECASE)
    if match:
        print("\n" + "="*80)
        print("TEXT AROUND 'NEUROKIND':")
        print("="*80)
        print(match.group(0))
        print("="*80)
