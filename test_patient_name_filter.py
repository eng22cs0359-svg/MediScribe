"""
Test script to verify patient name filtering logic
"""
import re

def is_doctor_name(name):
    """Check if a name appears to be a doctor's name"""
    if not name or not isinstance(name, str):
        return False
    
    name_lower = name.lower().strip()
    
    # Check for doctor titles/prefixes
    doctor_patterns = [
        r'\bdr\.?\s',  # Dr. or Dr followed by space
        r'\bdoctor\s',  # Doctor followed by space
        r'^dr\.?\s',  # Starts with Dr. or Dr
        r'^doctor\s',  # Starts with Doctor
    ]
    
    for pattern in doctor_patterns:
        if re.search(pattern, name_lower):
            return True
    
    return False

def extract_patient_name(name):
    """Extract and validate patient name, filtering out doctor names"""
    if not name or not isinstance(name, str):
        return "Not Mentioned"
    
    name = name.strip()
    
    # Check if it's a doctor name
    if is_doctor_name(name):
        return "Not Mentioned"
    
    # Return the name if it passes validation
    if len(name) > 0:
        return name
    
    return "Not Mentioned"

# Test cases
test_cases = [
    ("Dr. John Smith", "Not Mentioned"),
    ("Dr John Smith", "Not Mentioned"),
    ("Dr. Smith", "Not Mentioned"),
    ("Doctor Jane Doe", "Not Mentioned"),
    ("John Smith", "John Smith"),
    ("Jane Doe", "Jane Doe"),
    ("", "Not Mentioned"),
    (None, "Not Mentioned"),
    ("Dr.Smith", "Dr.Smith"),  # Edge case: no space after Dr.
    ("  Dr. Williams  ", "Not Mentioned"),
]

print("Testing patient name extraction logic:\n")
print("-" * 60)

all_passed = True
for input_name, expected_output in test_cases:
    result = extract_patient_name(input_name)
    status = "✓ PASS" if result == expected_output else "✗ FAIL"
    if result != expected_output:
        all_passed = False
    print(f"{status} | Input: {repr(input_name):30} | Expected: {expected_output:20} | Got: {result}")

print("-" * 60)
if all_passed:
    print("\n✓ All tests passed!")
else:
    print("\n✗ Some tests failed!")
