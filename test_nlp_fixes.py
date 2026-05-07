"""
Test script to verify NLP fixes for check2.jpeg
Tests:
1. Duration extraction: Should find "30 days" not "3 days"
2. Medicine count: Should find all 4 medicines
3. Age classification: "30" should not be classified as age if it appears with "days"
"""
import sys
sys.path.insert(0, 'api')

from ml_model.ml_model import detect_text
from ml_model.ner import extract_entities
from config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

print("=" * 80)
print("TESTING NLP FIXES FOR check2.jpeg")
print("=" * 80)

file_path = "./api/images/prescriptions/check2.jpeg"
print(f"\nProcessing: {file_path}")
print("-" * 80)

# Step 1: Extract text using AWS Textract
print("\n[STEP 1] Extracting text with AWS Textract...")
extracted_text = detect_text(file_path, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
print(f"✓ Text extracted: {len(extracted_text)} characters")

# Step 2: Extract entities using AWS Comprehend Medical + NLP post-processing
print("\n[STEP 2] Extracting entities with AWS Comprehend Medical + NLP...")
print("-" * 80)
entities = extract_entities(extracted_text, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
print("-" * 80)

# Step 3: Analyze results
print("\n" + "=" * 80)
print("RESULTS ANALYSIS")
print("=" * 80)

# Check medicines
medicines = entities.get('Medicines', [])
print(f"\n✓ MEDICINES FOUND: {len(medicines)}")
for idx, med in enumerate(medicines, 1):
    name = med.get('name', 'Unknown')
    dosage = med.get('dosage', 'N/A')
    frequency = med.get('frequency', 'N/A')
    duration = med.get('duration', 'N/A')
    print(f"  {idx}. {name}")
    print(f"     Dosage: {dosage}")
    print(f"     Frequency: {frequency}")
    print(f"     Duration: {duration}")

# Check patient info
patient_info = entities.get('PatientInfo', {})
print(f"\n✓ PATIENT INFO:")
print(f"  Name: {patient_info.get('name', 'N/A')}")
print(f"  Age: {patient_info.get('age', 'N/A')}")
print(f"  Gender: {patient_info.get('gender', 'N/A')}")

# Check conditions
conditions = entities.get('Conditions', [])
print(f"\n✓ CONDITIONS: {len(conditions)}")
for idx, cond in enumerate(conditions, 1):
    print(f"  {idx}. {cond}")

# Step 4: Verify fixes
print("\n" + "=" * 80)
print("FIX VERIFICATION")
print("=" * 80)

# Test 1: Medicine count
expected_medicine_count = 4
actual_medicine_count = len(medicines)
test1_pass = actual_medicine_count >= expected_medicine_count
print(f"\n[TEST 1] Medicine Count")
print(f"  Expected: >= {expected_medicine_count}")
print(f"  Actual: {actual_medicine_count}")
print(f"  Status: {'✓ PASS' if test1_pass else '✗ FAIL'}")

# Test 2: Duration should contain "30" not just "3"
test2_pass = False
duration_found = None
for med in medicines:
    duration = med.get('duration', '')
    if '30' in duration:
        test2_pass = True
        duration_found = duration
        break

print(f"\n[TEST 2] Duration Extraction")
print(f"  Expected: Duration containing '30' (e.g., '30 days')")
print(f"  Actual: {duration_found if duration_found else 'No duration with 30 found'}")
print(f"  Status: {'✓ PASS' if test2_pass else '✗ FAIL'}")

# Test 3: Age should not be "30" if "30 days" exists in text
test3_pass = True
patient_age = patient_info.get('age', '')
if patient_age == '30' and '30 days' in extracted_text.lower():
    test3_pass = False

print(f"\n[TEST 3] Age vs Duration Classification")
print(f"  Patient Age: {patient_age if patient_age else 'N/A'}")
print(f"  '30 days' in text: {'Yes' if '30 days' in extracted_text.lower() else 'No'}")
print(f"  Status: {'✓ PASS (30 not misclassified as age)' if test3_pass else '✗ FAIL (30 incorrectly classified as age)'}")

# Overall result
print("\n" + "=" * 80)
all_tests_pass = test1_pass and test2_pass and test3_pass
if all_tests_pass:
    print("✓✓✓ ALL TESTS PASSED ✓✓✓")
else:
    print("✗✗✗ SOME TESTS FAILED ✗✗✗")
    if not test1_pass:
        print(f"  - Need to extract all 4 medicines (currently {actual_medicine_count})")
    if not test2_pass:
        print("  - Need to extract '30 days' duration correctly")
    if not test3_pass:
        print("  - Need to prevent '30' from being classified as age when it's part of '30 days'")
print("=" * 80)
