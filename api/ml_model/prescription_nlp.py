"""
Advanced NLP post-processor for prescription entity extraction.
Improves AWS Comprehend Medical results with domain-specific rules.
Uses robust pattern matching to ensure stability across different inputs.
"""
import re
import logging
from typing import Dict, List, Tuple, Set

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrescriptionNLP:
    """Post-processes AWS Comprehend Medical results for better accuracy."""
    
    def __init__(self):
        # Medicine name suffixes and patterns
        self.medicine_suffixes = [
            'cillin', 'mycin', 'zole', 'pril', 'olol', 'pine', 'statin',
            'pam', 'zepam', 'caine', 'oxin', 'phylline', 'floxacin',
            'azole', 'tidine', 'prazole', 'mab', 'tinib', 'afil'
        ]
        
        # Medicine form indicators
        self.medicine_forms = [
            'tab', 'tablet', 'tablets', 'cap', 'capsule', 'capsules',
            'syp', 'syrup', 'inj', 'injection', 'susp', 'suspension',
            'drops', 'drop', 'cream', 'ointment', 'gel', 'lotion',
            'gargles', 'gargle', 'spray', 'inhaler', 'powder'
        ]
        
        # Medicine name patterns
        self.medicine_patterns = [
            'plus', 'forte', 'sr', 'xr', 'er', 'ds', 'ls', 'duo', 'max'
        ]
        
        # Comprehensive medicine database (expandable)
        self.known_medicines = {
            # Antibiotics
            'augmentin', 'amoxicillin', 'azithromycin', 'ciprofloxacin', 'doxycycline',
            'cephalexin', 'clarithromycin', 'metronidazole', 'levofloxacin', 'cefixime',
            # Pain/Fever
            'aspirin', 'paracetamol', 'ibuprofen', 'diclofenac', 'naproxen',
            'crocin', 'dolo', 'combiflam', 'brufen', 'disprin', 'saridon',
            # Cardiac
            'atorvastatin', 'metoprolol', 'amlodipine', 'losartan', 'ramipril',
            'stamlo', 'arvant', 'telma', 'ecosprin', 'rosuvastatin', 'telmisartan',
            # Gastro
            'omeprazole', 'pantoprazole', 'ranitidine', 'esomeprazole', 'rabeprazole',
            'pan', 'pand', 'pantocid', 'rantac', 'gelusil', 'digene',
            # Allergy
            'cetirizine', 'loratadine', 'fexofenadine', 'montelukast', 'allegra',
            'avil', 'pheniramine',
            # Vitamins
            'neurokind', 'becosules', 'shelcal', 'calcirol', 'evion', 'zincovit',
            'supradyn', 'revital',
            # Respiratory
            'salbutamol', 'levosalbutamol', 'deriphyllin', 'asthalin', 'budecort',
            # Throat/Oral
            'oro', 'orot', 'oro t', 'oro-t', 'betadine', 'tantum', 'hexigel',
            # Diabetes
            'metformin', 'glimepiride', 'sitagliptin', 'vildagliptin', 'glipizide',
            # Thyroid
            'thyronorm', 'eltroxin', 'thyour', 'thyrox', 'levothyroxine',
            # Others
            'enzoflam', 'enzof', 'zerodol', 'voveran', 'flexon', 'myospaz',
            'cyclopam', 'meftal', 'nimesulide'
        }
        
        # Terms that are NOT medicines
        self.non_medicine_terms = {
            'orthopedic', 'surgery', 'cardiology', 'neurology', 'pediatric',
            'dermatology', 'psychiatry', 'radiology', 'pathology', 'oncology',
            'gynecology', 'urology', 'ophthalmology', 'ent', 'general medicine',
            'consultation', 'follow up', 'follow-up', 'checkup', 'check up',
            'examination', 'diagnosis', 'treatment', 'therapy', 'procedure',
            'doctor', 'hospital', 'clinic', 'patient', 'prescription',
            'designing', 'whitening', 'implants', 'dentistry', 'dental'
        }
        
        # Dosage units
        self.dosage_units = ['mg', 'mcg', 'g', 'ml', 'cc', 'iu', 'units', 'gm']
        
        # Frequency patterns
        self.frequency_patterns = [
            'od', 'bd', 'td', 'qd', 'bid', 'tid', 'qid',
            'once', 'twice', 'thrice', 'daily', 'morning', 'evening', 'night',
            'sos', 'stat', 'prn'
        ]
    
    def process(self, aws_results: Dict, extracted_text: str) -> Dict:
        """
        Post-process AWS Comprehend Medical results with robust pattern matching.
        
        Args:
            aws_results: Raw results from AWS Comprehend Medical
            extracted_text: Full OCR text from prescription
            
        Returns:
            Improved and reorganized entity dictionary
        """
        logger.info("Starting NLP post-processing...")
        logger.info(f"Extracted text length: {len(extracted_text)} characters")
        logger.info("=" * 80)
        logger.info("FULL EXTRACTED TEXT:")
        logger.info(extracted_text)
        logger.info("=" * 80)
        
        # Log all AWS entities for debugging
        logger.info("AWS ENTITIES EXTRACTED:")
        for category in ['Medicine', 'BRAND_NAME', 'GENERIC_NAME', 'Medication', 'Procedure', 
                        'Dosage', 'Strength', 'Frequency', 'Duration', 'TIME_EXPRESSION', 'PatientInfo']:
            entities = aws_results.get(category, [])
            if entities:
                logger.info(f"  {category}: {entities}")
        logger.info("=" * 80)
        
        # Step 1: Extract medicines using multiple strategies
        medicines = self._extract_medicines_comprehensive(aws_results, extracted_text)
        logger.info(f"Found {len(medicines)} unique medicines")
        
        # Step 2: Match dosages to medicines
        medicines_with_dosage = self._match_dosages(medicines, aws_results, extracted_text)
        
        # Step 3: Extract other entities
        result = {
            'Medicines': medicines_with_dosage,
            'Conditions': self._extract_conditions(aws_results),
            'PatientInfo': self._extract_patient_info(aws_results, extracted_text),
            'Instructions': self._extract_instructions(aws_results, extracted_text)
        }
        
        logger.info(f"Post-processing complete. Returning {len(medicines_with_dosage)} medicines")
        return result
    
    def _extract_medicines_comprehensive(self, aws_results: Dict, text: str) -> List[Tuple[str, int, int]]:
        """
        Extract medicines using multiple strategies for maximum stability.
        Combines AWS results with pattern matching and known medicine database.
        """
        medicines_dict = {}  # Use dict with medicine name as key to avoid duplicates
        
        text_lower = text.lower()
        
        logger.info("=" * 80)
        logger.info("MEDICINE EXTRACTION - STRATEGY BY STRATEGY:")
        logger.info("=" * 80)
        
        # Strategy 1: Get from AWS results (all relevant categories)
        logger.info("Strategy 1: Extracting from AWS Medicine/Brand/Generic categories...")
        for category in ['Medicine', 'BRAND_NAME', 'GENERIC_NAME', 'Medication']:
            for med in aws_results.get(category, []):
                if len(med) >= 2 and isinstance(med[1], (list, tuple)) and len(med[1]) >= 2:
                    med_name = med[0].strip()
                    if self._is_valid_medicine(med_name):
                        # Use normalized name as key to avoid duplicates
                        key = self._normalize_medicine_name(med_name)
                        if key not in medicines_dict:
                            medicines_dict[key] = (med_name, med[1][0], med[1][1])
                            logger.info(f"  ✓ AWS {category} found: {med_name}")
        
        # Strategy 2: Check procedures that might be medicines
        logger.info("Strategy 2: Checking Procedure entities for misclassified medicines...")
        for proc in aws_results.get('Procedure', []):
            if len(proc) >= 2 and isinstance(proc[1], (list, tuple)) and len(proc[1]) >= 2:
                proc_name = proc[0].strip()
                logger.info(f"  Evaluating procedure: '{proc_name}'")
                if self._looks_like_medicine(proc_name):
                    key = self._normalize_medicine_name(proc_name)
                    if key not in medicines_dict:
                        medicines_dict[key] = (proc_name, proc[1][0], proc[1][1])
                        logger.info(f"  ✓ Reclassified from procedure: {proc_name}")
                else:
                    logger.info(f"  ✗ Not a medicine: {proc_name}")
        
        # Strategy 3: Search for known medicines in text
        logger.info("Strategy 3: Searching for known medicines in text...")
        for known_med in self.known_medicines:
            pattern = r'\b' + re.escape(known_med) + r'\b'
            for match in re.finditer(pattern, text_lower):
                actual_text = text[match.start():match.end()]
                key = self._normalize_medicine_name(actual_text)
                if key not in medicines_dict:
                    medicines_dict[key] = (actual_text, match.start(), match.end())
                    logger.info(f"  ✓ Known medicine found: {actual_text}")
        
        # Strategy 4: Pattern-based extraction (Tab/Cap + Name + Dosage)
        logger.info("Strategy 4: Pattern-based extraction (Tab/Cap + Name)...")
        medicine_pattern = r'\b(tab\.?|cap\.?|syp\.?|inj\.?)\s+([A-Za-z][A-Za-z\s-]{2,30}?)\s+(\d+\s*(?:mg|mcg|ml|g)?)'
        for match in re.finditer(medicine_pattern, text, re.IGNORECASE):
            med_name = match.group(2).strip()
            med_name = re.sub(r'\s+', ' ', med_name).strip()
            
            if self._is_valid_medicine(med_name) and len(med_name) > 3:
                key = self._normalize_medicine_name(med_name)
                if key not in medicines_dict:
                    medicines_dict[key] = (med_name, match.start(), match.end())
                    logger.info(f"  ✓ Pattern found: {med_name}")
        
        # Strategy 5: Find medicine-like words (words ending with medicine suffixes)
        logger.info("Strategy 5: Finding words with medicine suffixes...")
        words = re.findall(r'\b[A-Za-z]{4,}(?:cillin|mycin|zole|pril|olol|pine|statin|floxacin|azole|tidine|prazole)\b', text, re.IGNORECASE)
        for word in words:
            pattern = r'\b' + re.escape(word) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                if self._is_valid_medicine(word):
                    key = self._normalize_medicine_name(word)
                    if key not in medicines_dict:
                        medicines_dict[key] = (word, match.start(), match.end())
                        logger.info(f"  ✓ Suffix pattern found: {word}")
        
        # Strategy 6: Medicine + form pattern (e.g., "Augmentin tablet", "Oro T gargles")
        logger.info("Strategy 6: Medicine + form pattern (e.g., 'Medicine tablet')...")
        form_pattern = r'\b([A-Za-z][A-Za-z\s-]{2,25}?)\s+(tablet|capsule|syrup|drops|gargles?|injection|cream|ointment)s?\b'
        for match in re.finditer(form_pattern, text, re.IGNORECASE):
            med_name = match.group(1).strip()
            form = match.group(2)
            med_name = re.sub(r'\s+', ' ', med_name).strip()
            
            if self._is_valid_medicine(med_name) and len(med_name) > 2:
                key = self._normalize_medicine_name(med_name)
                # Only add if not already found, or if this is a more complete name
                if key not in medicines_dict:
                    full_name = f"{med_name} {form}"
                    medicines_dict[key] = (full_name, match.start(), match.end())
                    logger.info(f"  ✓ Form pattern found: {full_name}")
        
        # Strategy 7: Look for capitalized words that might be medicine names
        # This catches medicines that don't match other patterns
        logger.info("Strategy 7: Looking for capitalized medicine-like words...")
        # Pattern: Capitalized word(s) that might be a medicine name
        cap_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)?)\b'
        for match in re.finditer(cap_pattern, text):
            potential_med = match.group(1).strip()
            potential_lower = potential_med.lower()
            
            # Check if it's in our known medicines or looks like a medicine
            if potential_lower in self.known_medicines:
                key = self._normalize_medicine_name(potential_med)
                if key not in medicines_dict:
                    medicines_dict[key] = (potential_med, match.start(), match.end())
                    logger.info(f"  ✓ Capitalized known medicine: {potential_med}")
        
        # Convert dict to list and sort by position
        medicines_list = list(medicines_dict.values())
        medicines_list.sort(key=lambda x: x[1])
        
        logger.info("=" * 80)
        logger.info(f"TOTAL UNIQUE MEDICINES FOUND: {len(medicines_list)}")
        for idx, (name, start, end) in enumerate(medicines_list, 1):
            logger.info(f"  {idx}. {name} (position {start}-{end})")
        logger.info("=" * 80)
        
        return medicines_list
    
    def _normalize_medicine_name(self, name: str) -> str:
        """Normalize medicine name for deduplication."""
        # Convert to lowercase, remove extra spaces, remove common suffixes
        normalized = name.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove form words for comparison
        for form in self.medicine_forms:
            normalized = re.sub(r'\b' + form + r's?\b', '', normalized, flags=re.IGNORECASE)
        
        normalized = normalized.strip()
        return normalized
    
    def _is_valid_medicine(self, name: str) -> bool:
        """Check if a name is a valid medicine (not a non-medicine term)."""
        name_lower = name.lower().strip()
        
        # Check if it's in non-medicine terms
        if any(term in name_lower for term in self.non_medicine_terms):
            return False
        
        # Too short
        if len(name_lower) < 2:
            return False
        
        # Check if it's just numbers or special characters
        if not re.search(r'[a-z]', name_lower):
            return False
        
        return True
    
    def _looks_like_medicine(self, name: str) -> bool:
        """Check if a name looks like a medicine based on patterns."""
        name_lower = name.lower().strip()
        
        # Check if it's a valid medicine first
        if not self._is_valid_medicine(name):
            return False
        
        # Check for medicine suffixes
        if any(name_lower.endswith(suffix) for suffix in self.medicine_suffixes):
            return True
        
        # Check for medicine forms
        if any(form in name_lower for form in self.medicine_forms):
            return True
        
        # Check for medicine patterns
        if any(pattern in name_lower for pattern in self.medicine_patterns):
            return True
        
        # Check if it's in known medicines
        if name_lower in self.known_medicines:
            return True
        
        # Check if any known medicine is part of this name
        if any(known in name_lower for known in self.known_medicines if len(known) > 4):
            return True
        
        return False
    
    def _match_dosages(self, medicines: List[Tuple], aws_results: Dict, text: str) -> List[Dict]:
        """Match dosages and frequencies to medicines with improved accuracy."""
        result = []
        
        # Get all dosage-related entities from AWS
        dosages = aws_results.get('Dosage', []) + aws_results.get('Strength', [])
        frequencies = aws_results.get('Frequency', [])
        durations = aws_results.get('Duration', []) + aws_results.get('TIME_EXPRESSION', [])
        
        for med_name, med_start, med_end in medicines:
            dosage_info = {
                'name': med_name,
                'dosage': '',
                'frequency': '',
                'duration': ''
            }
            
            # Extract dosage - try multiple methods
            # Method 1: AWS entities
            closest_dosage = self._find_closest_entity(med_start, med_end, dosages, text, 150)
            if closest_dosage:
                dosage_info['dosage'] = closest_dosage
            
            # Method 2: Pattern matching in context
            if not dosage_info['dosage']:
                dosage_info['dosage'] = self._extract_dosage_pattern(med_start, med_end, text)
            
            # Extract frequency
            closest_freq = self._find_closest_entity(med_start, med_end, frequencies, text, 150)
            if closest_freq:
                dosage_info['frequency'] = closest_freq
            else:
                dosage_info['frequency'] = self._extract_frequency_pattern(med_start, med_end, text)
            
            # Extract duration
            closest_duration = self._find_closest_entity(med_start, med_end, durations, text, 150)
            if closest_duration:
                dosage_info['duration'] = closest_duration
            else:
                dosage_info['duration'] = self._extract_duration_pattern(med_start, med_end, text)
            
            result.append(dosage_info)
            logger.info(f"Medicine: {med_name} | Dosage: {dosage_info['dosage']} | Freq: {dosage_info['frequency']} | Duration: {dosage_info['duration']}")
        
        return result
    
    def _find_closest_entity(self, med_start: int, med_end: int, entities: List, 
                            text: str, max_distance: int) -> str:
        """Find the closest entity to a medicine."""
        closest = None
        min_distance = max_distance
        
        for entity in entities:
            if len(entity) < 2:
                continue
            if not isinstance(entity[1], (list, tuple)) or len(entity[1]) < 1:
                continue
                
            entity_pos = entity[1][0]
            distance = abs(entity_pos - med_end)
            
            if distance < min_distance:
                min_distance = distance
                closest = entity[0]
        
        return closest if closest else ''
    
    def _extract_dosage_pattern(self, med_start: int, med_end: int, text: str) -> str:
        """Extract dosage using comprehensive pattern matching."""
        # Get context around medicine - focus on text AFTER the medicine name
        context_after_start = med_end
        context_after_end = min(len(text), med_end + 100)
        context_after = text[context_after_start:context_after_end]
        
        # Also get a small context before for cases like "Tab Augmentin 625mg"
        context_before_start = max(0, med_start - 20)
        context_before = text[context_before_start:med_start]
        
        # Priority 1: Dosage immediately after medicine name (most reliable)
        # Pattern: 625mg, 625 mg, 625 mcg, etc.
        immediate_pattern = r'^\s*(\d{1,4})\s*(mg|mcg|ml|gm|g)\b'
        match = re.search(immediate_pattern, context_after, re.IGNORECASE)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        
        # Priority 2: Dosage with unit anywhere in after context
        dosage_unit_pattern = r'\b(\d{1,4})\s*(mg|mcg|ml|gm|g)\b'
        match = re.search(dosage_unit_pattern, context_after, re.IGNORECASE)
        if match:
            # Make sure it's not too far (within first 50 chars)
            if match.start() < 50:
                return f"{match.group(1)} {match.group(2)}"
        
        # Priority 3: Check before context (for "Tab Augmentin 625" pattern)
        match = re.search(dosage_unit_pattern, context_before, re.IGNORECASE)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        
        # Priority 4: Just numbers (less reliable, only if close)
        number_pattern = r'^\s*(\d{2,4})\b'
        match = re.search(number_pattern, context_after)
        if match:
            num = int(match.group(1))
            # Only accept if it looks like a dosage (10-2000 range)
            if 10 <= num <= 2000:
                return match.group(1)
        
        return ''
    
    def _extract_frequency_pattern(self, med_start: int, med_end: int, text: str) -> str:
        """Extract frequency using pattern matching - focus on text after medicine."""
        # Get context after medicine name (where frequency usually appears)
        context_start = med_end
        context_end = min(len(text), med_end + 100)
        context = text[context_start:context_end].lower()
        
        # Priority 1: Numeric patterns (1-0-1, 1x5, 0 x5, etc.) - most common
        freq_patterns = [
            (r'(\d+)\s*-\s*(\d+)\s*-\s*(\d+)', 0),  # 1-0-1
            (r'(\d+)\s*(?:0|o)\s*(\d+)', 0),  # 1 0 1, 1o1
            (r'(\d+)\s*x\s*(\d+)', 0),  # 1x5
            (r'x\s*(\d+)', 0),  # x5
        ]
        
        for pattern, group_idx in freq_patterns:
            match = re.search(pattern, context)
            if match:
                # Make sure it's close to the medicine (within first 50 chars)
                if match.start() < 50:
                    freq_str = match.group(0).replace('o', '0').replace('O', '0').upper()
                    
                    # Validate: frequency should be reasonable length and contain valid numbers
                    if len(freq_str) < 20:  # Reasonable length
                        # Check if it's a valid frequency pattern (not a phone number, etc.)
                        # Extract all numbers from the frequency
                        numbers = re.findall(r'\d+', freq_str)
                        # Valid frequencies have small numbers (0-10 typically)
                        if numbers and all(int(num) <= 10 for num in numbers):
                            return freq_str
        
        # Priority 2: Standard frequency abbreviations
        for freq in self.frequency_patterns:
            if re.search(r'\b' + freq + r'\b', context):
                return freq.upper()
        
        return ''
    
    def _extract_duration_pattern(self, med_start: int, med_end: int, text: str) -> str:
        """
        Extract duration using pattern matching with improved context awareness.
        Prioritizes finding duration near the medicine and in the full text.
        """
        # Strategy 1: Look in context around the medicine (most reliable)
        context_start = max(0, med_start - 30)
        context_end = min(len(text), med_end + 150)
        context = text[context_start:context_end]
        
        # Duration patterns (ordered by priority)
        patterns = [
            (r'(?:for\s+)?(\d+)\s*days?\b', 'days'),  # "for 30 days", "30 days"
            (r'x\s*(\d+)\s*days?\b', 'days'),  # "x30 days", "x 30 days"
            (r'(\d+)\s*d\b', 'd'),  # "30d"
            (r'(?:for\s+)?(\d+)\s*weeks?\b', 'weeks'),  # "2 weeks"
            (r'(\d+)\s*w\b', 'w'),  # "2w"
            (r'(?:for\s+)?(\d+)\s*months?\b', 'months'),  # "1 month"
            (r'(\d+)\s*m\b', 'm'),  # "1m"
        ]
        
        for pattern, unit in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                duration_value = match.group(1)
                duration_text = match.group(0)
                logger.info(f"[DEBUG] Duration found in medicine context: '{duration_text}'")
                return duration_text
        
        # Strategy 2: If not found near medicine, search the full text for duration patterns
        # This helps when duration is mentioned separately from the medicine
        logger.info(f"[DEBUG] No duration found near medicine, searching full text...")
        
        # Look for explicit duration patterns in full text
        full_text_patterns = [
            (r'(?:for\s+)?(\d+)\s*days?\b', 'days'),
            (r'x\s*(\d+)\s*days?\b', 'days'),
            (r'(\d+)\s*d\b(?!\w)', 'd'),  # "30d" but not "30days" (already covered)
        ]
        
        # Find all duration matches in the full text
        duration_matches = []
        for pattern, unit in full_text_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                duration_value = int(match.group(1))
                # Filter out unrealistic durations (e.g., > 365 days)
                if 1 <= duration_value <= 365:
                    duration_matches.append({
                        'text': match.group(0),
                        'value': duration_value,
                        'position': match.start(),
                        'distance': abs(match.start() - med_end)
                    })
                    logger.info(f"[DEBUG] Found duration candidate in full text: '{match.group(0)}' at position {match.start()}")
        
        # If we found duration matches, return the closest one to the medicine
        if duration_matches:
            # Sort by distance from medicine
            duration_matches.sort(key=lambda x: x['distance'])
            closest = duration_matches[0]
            logger.info(f"[DEBUG] Selected closest duration: '{closest['text']}' (distance: {closest['distance']})")
            return closest['text']
        
        logger.info(f"[DEBUG] No duration pattern found")
        return ''
    
    def _extract_conditions(self, aws_results: Dict) -> List[str]:
        """Extract medical conditions."""
        conditions = []
        for cond in aws_results.get('Condition', []):
            conditions.append(cond[0])
        return conditions
    
    def _extract_patient_info(self, aws_results: Dict, text: str) -> Dict:
        """Extract patient information with improved name detection and context-aware age classification."""
        info = {
            'name': '',
            'age': '',
            'gender': ''
        }
        
        # Words that indicate it's NOT a patient name
        non_patient_words = {
            'clinic', 'hospital', 'dr', 'doctor', 'medical', 'health', 'care',
            'center', 'centre', 'pharmacy', 'lab', 'laboratory', 'diagnostics',
            'polyclinic', 'nursing', 'home', 'institute', 'foundation'
        }
        
        # Medical titles and suffixes that indicate a doctor's name
        doctor_titles = {'dr', 'dr.', 'doctor', 'prof', 'prof.', 'professor'}
        medical_suffixes = {'md', 'mbbs', 'ms', 'bds', 'bhms', 'bams', 'sg', 'frcs', 'mrcp', 'dnb'}
        
        # Duration keywords that indicate a number is NOT an age
        duration_keywords = ['days', 'day', 'weeks', 'week', 'months', 'month', 'd', 'w', 'm']
        
        def is_number_near_duration_keyword(number_str: str, full_text: str) -> bool:
            """
            Check if a number appears near duration keywords like "days", "weeks", etc.
            This helps distinguish between age (e.g., "30 years old") and duration (e.g., "30 days").
            """
            if not number_str or not number_str.isdigit():
                return False
            
            # Find all occurrences of this number in the text
            pattern = r'\b' + re.escape(number_str) + r'\b'
            for match in re.finditer(pattern, full_text, re.IGNORECASE):
                # Get context around the number (30 chars before and after)
                start = max(0, match.start() - 30)
                end = min(len(full_text), match.end() + 30)
                context = full_text[start:end].lower()
                
                logger.info(f"[DEBUG] Checking number '{number_str}' context: '{context}'")
                
                # Check if any duration keyword appears near this number
                for keyword in duration_keywords:
                    # Pattern: number followed by keyword (e.g., "30 days", "30days", "for 30 days")
                    if re.search(r'\b' + re.escape(number_str) + r'\s{0,3}' + keyword + r'\b', context, re.IGNORECASE):
                        logger.info(f"[DEBUG] ✓ Number '{number_str}' appears near duration keyword '{keyword}'")
                        return True
                    # Pattern: keyword followed by number (e.g., "days 30", less common but possible)
                    if re.search(r'\b' + keyword + r'\s{0,3}' + re.escape(number_str) + r'\b', context, re.IGNORECASE):
                        logger.info(f"[DEBUG] ✓ Number '{number_str}' appears after duration keyword '{keyword}'")
                        return True
            
            logger.info(f"[DEBUG] ✗ Number '{number_str}' does not appear near duration keywords")
            return False
        
        def is_doctor_name(name: str) -> bool:
            """Check if the name appears to be a doctor's name."""
            name_lower = name.lower().strip()
            
            logger.info(f"[DEBUG] is_doctor_name() called with: '{name}'")
            logger.info(f"[DEBUG] name_lower: '{name_lower}'")
            
            # Check if starts with doctor title
            for title in doctor_titles:
                if name_lower.startswith(title + ' ') or name_lower.startswith(title):
                    logger.info(f"[DEBUG] ✓ Matched doctor title: '{title}'")
                    return True
            
            # Check if contains medical suffix
            # Split by spaces and check last word(s)
            words = name_lower.split()
            logger.info(f"[DEBUG] Words in name: {words}")
            for word in words:
                # Remove punctuation for comparison
                clean_word = word.strip('.,;:')
                logger.info(f"[DEBUG] Checking word: '{word}' -> clean: '{clean_word}'")
                if clean_word in medical_suffixes:
                    logger.info(f"[DEBUG] ✓ Matched medical suffix: '{clean_word}'")
                    return True
            
            logger.info(f"[DEBUG] ✗ Not identified as doctor name")
            return False
        
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
            # This handles: "Dr. Sachin Kumar", "Dr.Sachin Kumar", "Dr Sachin Kumar"
            pattern = r'\b(?:dr\.?|doctor)\s{0,5}' + escaped_name + r'\b'
            match = re.search(pattern, full_text, re.IGNORECASE)
            
            if match:
                logger.info(f"[DEBUG] ✓ Name '{name}' appears near doctor title in text")
                logger.info(f"[DEBUG]   Matched text: '{match.group(0)}'")
                return True
            
            # Pattern: Name followed by medical suffix (within 0-5 characters)
            # This handles: "Sachin Kumar SG", "Sachin Kumar MBBS"
            suffix_pattern = escaped_name + r'\s{0,5}\b(?:' + '|'.join(medical_suffixes) + r')\b'
            match = re.search(suffix_pattern, full_text, re.IGNORECASE)
            
            if match:
                logger.info(f"[DEBUG] ✓ Name '{name}' appears near medical suffix in text")
                logger.info(f"[DEBUG]   Matched text: '{match.group(0)}'")
                return True
            
            logger.info(f"[DEBUG] ✗ Name '{name}' does not appear near doctor indicators")
            return False
        
        # Extract from AWS results
        patient_info = aws_results.get('PatientInfo', [])
        logger.info(f"[DEBUG] ========== PATIENT INFO EXTRACTION ==========")
        logger.info(f"[DEBUG] AWS PatientInfo extracted: {patient_info}")
        logger.info(f"[DEBUG] Number of PatientInfo items: {len(patient_info)}")
        
        for idx, item in enumerate(patient_info):
            text_item = item[0].strip()
            text_lower = text_item.lower()
            
            logger.info(f"[DEBUG] --- Processing item {idx + 1}: '{text_item}' ---")
            
            # Check if it's a number that could be age OR duration
            if text_item.isdigit():
                number_value = int(text_item)
                logger.info(f"[DEBUG] Found number: {text_item}")
                
                # First, check if this number appears near duration keywords in the full text
                if is_number_near_duration_keyword(text_item, text):
                    logger.info(f"[DEBUG] ✗ Skipped as age - number appears near duration keywords (likely duration, not age)")
                    continue
                
                # If not near duration keywords and in valid age range, treat as age
                if 1 <= number_value <= 120:
                    logger.info(f"[DEBUG] ✓ Identified as age: {text_item}")
                    info['age'] = text_item
                    continue
                else:
                    logger.info(f"[DEBUG] ✗ Number {text_item} out of valid age range (1-120)")
                    continue
            
            # Check if it's a name (not a clinic/hospital)
            if not any(char.isdigit() for char in text_item) and len(text_item) > 2:
                logger.info(f"[DEBUG] Potential name candidate: '{text_item}'")
                
                # Skip if it contains non-patient words
                matching_non_patient = [word for word in non_patient_words if word in text_lower]
                if matching_non_patient:
                    logger.info(f"[DEBUG] ✗ Skipped - contains non-patient words: {matching_non_patient}")
                    continue
                
                # Skip if it's all uppercase and longer than 10 chars (likely clinic name)
                if text_item.isupper() and len(text_item) > 10:
                    logger.info(f"[DEBUG] ✗ Skipped - all uppercase and long (likely clinic)")
                    continue
                
                # Skip if it's a doctor's name
                is_doctor = is_doctor_name(text_item)
                if is_doctor:
                    logger.info(f"[DEBUG] ✗ Skipped - identified as doctor name")
                    continue
                
                # Additional check: See if this name appears near doctor title in full text
                if appears_near_doctor_title(text_item, text):
                    logger.info(f"[DEBUG] ✗ Skipped - name appears near doctor title in full text")
                    continue
                
                # This looks like a patient name
                if not info['name']:
                    logger.info(f"[DEBUG] ✓ ACCEPTED as patient name: '{text_item}'")
                    info['name'] = text_item
                else:
                    logger.info(f"[DEBUG] ✗ Skipped - patient name already set to: '{info['name']}'")
        
        # If no name found from AWS, try pattern matching in text
        if not info['name']:
            logger.info(f"[DEBUG] No name found from AWS, trying pattern matching...")
            # Look for "Name:" or "Patient:" followed by name
            name_patterns = [
                r'(?:patient|pt\.?)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # Patient: First Last (requires at least 2 words)
                r'(?:name)\s*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # Name: First Last (requires colon and 2 words)
                r'\bMr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                r'\bMrs\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                r'\bMs\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    potential_name = match.group(1).strip()
                    potential_lower = potential_name.lower()
                    logger.info(f"[DEBUG] Pattern matched potential name: '{potential_name}'")
                    
                    # Verify it's not a clinic name
                    if not any(word in potential_lower for word in non_patient_words):
                        # Verify it's not a doctor's name
                        if not is_doctor_name(potential_name):
                            # Additional check: See if this name appears near doctor title
                            if not appears_near_doctor_title(potential_name, text):
                                logger.info(f"[DEBUG] ✓ ACCEPTED from pattern: '{potential_name}'")
                                info['name'] = potential_name
                                break
                            else:
                                logger.info(f"[DEBUG] ✗ Rejected - appears near doctor title in text")
                        else:
                            logger.info(f"[DEBUG] ✗ Rejected - doctor name")
                    else:
                        logger.info(f"[DEBUG] ✗ Rejected - contains non-patient words")
        
        # Extract gender
        gender_match = re.search(r'\b(M|F|Male|Female)\b', text, re.IGNORECASE)
        if gender_match:
            info['gender'] = gender_match.group(1).upper()[0]
        
        # Extract age if not found
        if not info['age']:
            age_patterns = [
                r'(?:age|yrs?|years?)\s*:?\s*(\d{1,3})',
                r'(\d{1,3})\s*(?:yrs?|years?|y)\b',
            ]
            for pattern in age_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    age = int(match.group(1))
                    if 1 <= age <= 120:
                        info['age'] = str(age)
                        break
        
        logger.info(f"[DEBUG] ========== FINAL PATIENT INFO ==========")
        logger.info(f"[DEBUG] Final patient name: '{info['name']}'")
        logger.info(f"[DEBUG] Final patient age: '{info['age']}'")
        logger.info(f"[DEBUG] Final patient gender: '{info['gender']}'")
        logger.info(f"[DEBUG] ==========================================")
        
        return info
    
    def _extract_instructions(self, aws_results: Dict, text: str) -> List[str]:
        """Extract special instructions."""
        instructions = []
        
        # Look for instruction patterns
        instruction_patterns = [
            r'(?:take|use|apply)\s+[^.]+',
            r'(?:before|after)\s+(?:food|meal|breakfast|lunch|dinner)',
            r'(?:with|in)\s+(?:water|milk|food)',
        ]
        
        for pattern in instruction_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                instructions.append(match.group(0))
        
        return instructions[:3]  # Limit to 3 instructions
