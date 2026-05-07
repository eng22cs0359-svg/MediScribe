"""
Complete integration test for patient name extraction with doctor name filtering.
This simulates the actual flow with AWS results and full prescription text.
"""
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.ml_model.prescription_nlp import PrescriptionNLP

# Simulate AWS Comprehend Medical results
# This is what AWS might extract from a prescription with "Dr. Sachin Kumar SG"
aws_results_scenario_1 = {
    'Medicine': [
        ['Augmentin', [150, 159]],
        ['Oro T', [200, 205]]
    ],
    'Dosage': [
        ['625mg', [160, 165]],
    ],
    'Frequency': [
        ['1-0-1', [170, 175]],
    ],
    'Duration': [
        ['5 days', [180, 186]],
    ],
    'PatientInfo': [
        ['Sachin Kumar', [45, 58]],  # AWS extracts doctor name without "Dr." or "SG"
        ['35', [120, 122]],
        ['M', [125, 126]]
    ],
    'Condition': [],
    'Procedure': []
}

# Full prescription text (what OCR extracted) - WITHOUT patient name in text
full_text_scenario_1 = """
ORTHOPEDIC CLINIC
Dr. Sachin Kumar SG
MBBS, MS (Ortho)
Reg. No: 12345

Age: 35 years
Gender: Male
Date: 2024-01-15

Rx:
Tab Augmentin 625mg
1-0-1 x 5 days

Tab Oro T gargles
Twice daily
"""

# Full prescription text WITH patient name
full_text_with_patient = """
ORTHOPEDIC CLINIC
Dr. Sachin Kumar SG
MBBS, MS (Ortho)
Reg. No: 12345

Patient Name: Ramesh Patel
Age: 35 years
Gender: Male
Date: 2024-01-15

Rx:
Tab Augmentin 625mg
1-0-1 x 5 days

Tab Oro T gargles
Twice daily
"""

# Scenario 2: AWS correctly extracts patient name
aws_results_scenario_2 = {
    'Medicine': [
        ['Augmentin', [150, 159]],
    ],
    'PatientInfo': [
        ['Ramesh Patel', [85, 97]],  # Correct patient name
        ['35', [120, 122]],
        ['M', [125, 126]]
    ],
    'Condition': [],
    'Procedure': []
}

# Scenario 3: AWS extracts doctor name WITH title and suffix
aws_results_scenario_3 = {
    'Medicine': [
        ['Augmentin', [150, 159]],
    ],
    'PatientInfo': [
        ['Dr. Sachin Kumar SG', [20, 40]],  # Full doctor name with title
        ['35', [120, 122]],
    ],
    'Condition': [],
    'Procedure': []
}

# Scenario 4: AWS extracts doctor name with suffix but no title
aws_results_scenario_4 = {
    'Medicine': [
        ['Augmentin', [150, 159]],
    ],
    'PatientInfo': [
        ['Sachin Kumar SG', [23, 39]],  # Doctor name with SG suffix
        ['35', [120, 122]],
    ],
    'Condition': [],
    'Procedure': []
}

def test_scenario(scenario_name, aws_results, full_text, expected_patient_name):
    """Test a specific scenario."""
    print(f"\n{'='*80}")
    print(f"SCENARIO: {scenario_name}")
    print(f"{'='*80}")
    
    print(f"\nAWS PatientInfo: {aws_results.get('PatientInfo', [])}")
    print(f"Expected patient name: '{expected_patient_name}'")
    
    # Create NLP processor and process
    nlp = PrescriptionNLP()
    result = nlp.process(aws_results, full_text)
    
    actual_patient_name = result['PatientInfo']['name']
    print(f"\nActual patient name: '{actual_patient_name}'")
    
    # Check result
    if actual_patient_name == expected_patient_name:
        print(f"[PASS] Patient name correctly extracted")
        return True
    else:
        print(f"[FAIL] Expected '{expected_patient_name}', got '{actual_patient_name}'")
        return False

# Run all scenarios
print("="*80)
print("COMPLETE PATIENT EXTRACTION INTEGRATION TEST")
print("="*80)

results = []

# Scenario 1: The problematic case - AWS extracts "Sachin Kumar" without title/suffix
results.append(test_scenario(
    "AWS extracts doctor name without title/suffix",
    aws_results_scenario_1,
    full_text_scenario_1,
    ""  # Should be empty (doctor name filtered out)
))

# Scenario 2: AWS correctly extracts patient name
results.append(test_scenario(
    "AWS correctly extracts patient name",
    aws_results_scenario_2,
    full_text_with_patient,  # Use text WITH patient name
    "Ramesh Patel"  # Should extract patient name
))

# Scenario 3: AWS extracts doctor name WITH title and suffix
results.append(test_scenario(
    "AWS extracts doctor name with title and suffix",
    aws_results_scenario_3,
    full_text_scenario_1,
    ""  # Should be empty (doctor name filtered out)
))

# Scenario 4: AWS extracts doctor name with suffix but no title
results.append(test_scenario(
    "AWS extracts doctor name with suffix but no title",
    aws_results_scenario_4,
    full_text_scenario_1,
    ""  # Should be empty (doctor name filtered out)
))

# Summary
print(f"\n{'='*80}")
print("TEST SUMMARY")
print(f"{'='*80}")
passed = sum(results)
total = len(results)
print(f"Passed: {passed}/{total}")
print(f"Failed: {total - passed}/{total}")

if passed == total:
    print("\n[SUCCESS] ALL TESTS PASSED!")
else:
    print(f"\n[FAILURE] SOME TESTS FAILED")

sys.exit(0 if passed == total else 1)
