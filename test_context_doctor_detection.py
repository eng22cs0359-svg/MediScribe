"""
Test the context-based doctor name detection.
This simulates the scenario where AWS extracts "Sachin Kumar" without "Dr." or "SG",
but the full text contains "Dr. Sachin Kumar SG".
"""
import re

# Medical titles and suffixes
doctor_titles = {'dr', 'dr.', 'doctor', 'prof', 'prof.', 'professor'}
medical_suffixes = {'md', 'mbbs', 'ms', 'bds', 'bhms', 'bams', 'sg', 'frcs', 'mrcp', 'dnb'}

def appears_near_doctor_title(name: str, full_text: str) -> bool:
    """
    Check if the name appears near 'Dr.' or 'Doctor' in the full text.
    This catches cases where AWS extracts just the name without the title.
    """
    if not name or len(name) < 3:
        return False
    
    # Escape special regex characters in the name
    escaped_name = re.escape(name)
    
    # Pattern: Dr./Doctor followed by the name (within 0-5 characters)
    pattern = r'\b(?:dr\.?|doctor)\s{0,5}' + escaped_name + r'\b'
    match = re.search(pattern, full_text, re.IGNORECASE)
    
    if match:
        print(f"  ✓ Name appears near doctor title")
        print(f"    Matched: '{match.group(0)}'")
        return True
    
    # Pattern: Name followed by medical suffix (within 0-5 characters)
    suffix_pattern = escaped_name + r'\s{0,5}\b(?:' + '|'.join(medical_suffixes) + r')\b'
    match = re.search(suffix_pattern, full_text, re.IGNORECASE)
    
    if match:
        print(f"  ✓ Name appears near medical suffix")
        print(f"    Matched: '{match.group(0)}'")
        return True
    
    print(f"  ✗ Name does not appear near doctor indicators")
    return False


# Test scenarios
test_scenarios = [
    {
        "name": "Sachin Kumar",
        "full_text": "Dr. Sachin Kumar SG\nOrthopedic Surgeon\nPatient: John Doe",
        "expected": True,
        "description": "AWS extracts 'Sachin Kumar', but full text has 'Dr. Sachin Kumar SG'"
    },
    {
        "name": "Sachin Kumar",
        "full_text": "Dr.Sachin Kumar SG\nOrthopedic Surgeon\nPatient: John Doe",
        "expected": True,
        "description": "No space after Dr."
    },
    {
        "name": "Sachin Kumar",
        "full_text": "Doctor Sachin Kumar\nOrthopedic Surgeon\nPatient: John Doe",
        "expected": True,
        "description": "Full word 'Doctor' instead of 'Dr.'"
    },
    {
        "name": "Sachin Kumar",
        "full_text": "Sachin Kumar MBBS\nOrthopedic Surgeon\nPatient: John Doe",
        "expected": True,
        "description": "Name followed by MBBS suffix"
    },
    {
        "name": "Sachin Kumar",
        "full_text": "Sachin Kumar SG\nOrthopedic Surgeon\nPatient: John Doe",
        "expected": True,
        "description": "Name followed by SG suffix"
    },
    {
        "name": "John Doe",
        "full_text": "Dr. Sachin Kumar SG\nOrthopedic Surgeon\nPatient: John Doe",
        "expected": False,
        "description": "Patient name should NOT be detected as doctor"
    },
    {
        "name": "Jane Smith",
        "full_text": "Clinic Name: ABC Medical Center\nPatient: Jane Smith\nAge: 35",
        "expected": False,
        "description": "Regular patient name with no doctor context"
    },
]

print("=" * 80)
print("TESTING CONTEXT-BASED DOCTOR NAME DETECTION")
print("=" * 80)

passed = 0
failed = 0

for i, scenario in enumerate(test_scenarios, 1):
    print(f"\n[TEST {i}] {scenario['description']}")
    print(f"  Name extracted by AWS: '{scenario['name']}'")
    print(f"  Full text snippet: {scenario['full_text'][:60]}...")
    
    result = appears_near_doctor_title(scenario['name'], scenario['full_text'])
    expected = scenario['expected']
    
    if result == expected:
        print(f"  ✓ PASS: Expected {expected}, Got {result}")
        passed += 1
    else:
        print(f"  ✗ FAIL: Expected {expected}, Got {result}")
        failed += 1

print("\n" + "=" * 80)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_scenarios)} tests")
print("=" * 80)

# Demonstrate the complete flow
print("\n" + "=" * 80)
print("COMPLETE FLOW DEMONSTRATION")
print("=" * 80)

print("\nScenario: Prescription with 'Dr. Sachin Kumar SG'")
print("AWS extracts PatientInfo: ['Sachin Kumar', '35', 'M']")
print("\nProcessing 'Sachin Kumar':")
print("  1. is_doctor_name('Sachin Kumar') -> False (no title/suffix in extracted text)")
print("  2. appears_near_doctor_title('Sachin Kumar', full_text) -> ", end="")

full_prescription_text = """
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
"""

result = appears_near_doctor_title("Sachin Kumar", full_prescription_text)
print(f"{result}")
print(f"  3. Final decision: {'FILTER OUT (Doctor name)' if result else 'ACCEPT (Patient name)'}")

print("\n\nScenario: Prescription with patient 'Ramesh Patel'")
print("AWS extracts PatientInfo: ['Ramesh Patel', '35']")
print("\nProcessing 'Ramesh Patel':")
print("  1. is_doctor_name('Ramesh Patel') -> False (no title/suffix)")
print("  2. appears_near_doctor_title('Ramesh Patel', full_text) -> ", end="")

result = appears_near_doctor_title("Ramesh Patel", full_prescription_text)
print(f"{result}")
print(f"  3. Final decision: {'FILTER OUT (Doctor name)' if result else 'ACCEPT (Patient name)'}")
