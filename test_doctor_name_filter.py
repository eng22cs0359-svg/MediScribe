"""
Test script to verify the is_doctor_name() function works correctly.
Tests with the specific names from the prescription issue.
"""

# Simulate the is_doctor_name function from prescription_nlp.py
def is_doctor_name(name: str) -> bool:
    """Check if the name appears to be a doctor's name."""
    doctor_titles = {'dr', 'dr.', 'doctor', 'prof', 'prof.', 'professor'}
    medical_suffixes = {'md', 'mbbs', 'ms', 'bds', 'bhms', 'bams', 'sg', 'frcs', 'mrcp', 'dnb'}
    
    name_lower = name.lower().strip()
    
    print(f"\n[TEST] Testing: '{name}'")
    print(f"  name_lower: '{name_lower}'")
    
    # Check if starts with doctor title
    for title in doctor_titles:
        if name_lower.startswith(title + ' ') or name_lower.startswith(title):
            print(f"  ✓ Matched doctor title: '{title}'")
            return True
    
    # Check if contains medical suffix
    words = name_lower.split()
    print(f"  Words: {words}")
    for word in words:
        clean_word = word.strip('.,;:')
        print(f"    Checking: '{word}' -> '{clean_word}'")
        if clean_word in medical_suffixes:
            print(f"  ✓ Matched medical suffix: '{clean_word}'")
            return True
    
    print(f"  ✗ Not identified as doctor name")
    return False


# Test cases
test_cases = [
    ("Sachin Kumar", False, "Should NOT be identified as doctor (no title/suffix)"),
    ("Sachin Kumar SG", True, "Should be identified as doctor (has SG suffix)"),
    ("Dr. Sachin Kumar SG", True, "Should be identified as doctor (has Dr. title)"),
    ("Dr Sachin Kumar", True, "Should be identified as doctor (has Dr title)"),
    ("Dr. Sachin Kumar", True, "Should be identified as doctor (has Dr. title)"),
    ("Sachin Kumar MBBS", True, "Should be identified as doctor (has MBBS suffix)"),
    ("John Doe", False, "Should NOT be identified as doctor (regular name)"),
    ("Dr Smith", True, "Should be identified as doctor (has Dr title)"),
    ("Kumar SG", True, "Should be identified as doctor (has SG suffix)"),
]

print("=" * 70)
print("TESTING is_doctor_name() FUNCTION")
print("=" * 70)

passed = 0
failed = 0

for name, expected, description in test_cases:
    result = is_doctor_name(name)
    status = "✓ PASS" if result == expected else "✗ FAIL"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"\n{status}: {description}")
    print(f"  Input: '{name}'")
    print(f"  Expected: {expected}, Got: {result}")

print("\n" + "=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("=" * 70)

# Additional test: Check what AWS might be extracting
print("\n" + "=" * 70)
print("SIMULATING AWS EXTRACTION SCENARIOS")
print("=" * 70)

aws_scenarios = [
    ("Sachin Kumar", "AWS extracts just the name without Dr. or SG"),
    ("Dr. Sachin Kumar SG", "AWS extracts the full text with title and suffix"),
    ("Sachin Kumar SG", "AWS extracts name with suffix but no title"),
]

for name, scenario in aws_scenarios:
    print(f"\nScenario: {scenario}")
    print(f"  Extracted: '{name}'")
    result = is_doctor_name(name)
    print(f"  is_doctor_name(): {result}")
    print(f"  Would be filtered: {'YES' if result else 'NO'}")
