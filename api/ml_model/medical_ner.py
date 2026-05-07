"""
Rule-based Medical NER for prescription text extraction.
This provides better results than blank spaCy models.
"""
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MedicalNER:
    """Rule-based medical entity extractor for prescriptions."""
    
    def __init__(self):
        # Common medicine patterns
        self.medicine_patterns = [
            r'\b[A-Z][a-z]+(?:cin|zole|pril|olol|pine|mycin|cillin|oxin|statin|pam|zepam)\b',
            r'\b(?:Tab|Cap|Syp|Inj)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
        ]
        
        # Dosage patterns
        self.dosage_patterns = [
            r'\b\d+\s*(?:mg|mcg|g|ml|cc|units?)\b',
            r'\b\d+/\d+\s*(?:mg|mcg)\b',
        ]
        
        # Frequency patterns
        self.frequency_patterns = [
            r'\b(?:once|twice|thrice|1|2|3)\s*(?:daily|a day|per day|times?\s*(?:a|per)\s*day)\b',
            r'\bOD\b|\bBD\b|\bTD\b|\bQD\b|\bBID\b|\bTID\b|\bQID\b',
            r'\b(?:morning|afternoon|evening|night|bedtime)\b',
            r'\b\d+\s*(?:x|X)\s*\d+\b',
        ]
        
        # Duration patterns
        self.duration_patterns = [
            r'\b\d+\s*(?:days?|weeks?|months?|years?)\b',
            r'\bfor\s+\d+\s*(?:days?|weeks?|months?)\b',
        ]
        
        # Medical condition patterns
        self.condition_patterns = [
            r'\b(?:fever|cough|cold|pain|infection|diabetes|hypertension|asthma|allergy)\b',
            r'\b(?:headache|backache|stomachache|toothache)\b',
            r'\b(?:arthritis|bronchitis|gastritis|dermatitis)\b',
        ]
        
    def extract_entities(self, text):
        """Extract medical entities from text."""
        if not text:
            return {}
        
        text_lower = text.lower()
        entities = {}
        
        # Extract medicines
        medicines = []
        for pattern in self.medicine_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                med_text = match.group(1) if match.lastindex else match.group(0)
                medicines.append((med_text, (match.start(), match.end())))
        
        # Also look for capitalized words that might be medicines
        cap_words = re.finditer(r'\b[A-Z][a-z]{3,}(?:\s+[A-Z][a-z]+)?\b', text)
        for match in cap_words:
            word = match.group(0)
            # Skip common non-medicine words
            if word.lower() not in ['name', 'date', 'address', 'phone', 'doctor', 'patient', 'clinic']:
                if len(word) > 4:  # Likely a medicine name
                    medicines.append((word, (match.start(), match.end())))
        
        if medicines:
            entities['Medicine'] = medicines
        
        # Extract dosages
        dosages = []
        for pattern in self.dosage_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                dosages.append((match.group(0), (match.start(), match.end())))
        if dosages:
            entities['Dosage'] = dosages
        
        # Extract frequency
        frequencies = []
        for pattern in self.frequency_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                frequencies.append((match.group(0), (match.start(), match.end())))
        if frequencies:
            entities['Frequency'] = frequencies
        
        # Extract duration
        durations = []
        for pattern in self.duration_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                durations.append((match.group(0), (match.start(), match.end())))
        if durations:
            entities['Duration'] = durations
        
        # Extract conditions
        conditions = []
        for pattern in self.condition_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                conditions.append((match.group(0), (match.start(), match.end())))
        if conditions:
            entities['Condition'] = conditions
        
        # Extract patient name (usually after "Name:" or "Patient:")
        name_match = re.search(r'(?:Name|Patient)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
        if name_match:
            entities['PatientName'] = [(name_match.group(1), (name_match.start(1), name_match.end(1)))]
        
        # Extract age
        age_match = re.search(r'Age\s*:?\s*(\d+)\s*(?:yrs?|years?)?', text, re.IGNORECASE)
        if age_match:
            entities['Age'] = [(age_match.group(1), (age_match.start(1), age_match.end(1)))]
        
        # Extract doctor name (usually has Dr. prefix)
        doctor_match = re.search(r'Dr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
        if doctor_match:
            entities['Doctor'] = [(doctor_match.group(1), (doctor_match.start(1), doctor_match.end(1)))]
        
        logger.info(f"Extracted {sum(len(v) for v in entities.values())} entities")
        return entities
    
    def predict(self, text):
        """Predict entities (compatible with existing interface)."""
        return self.extract_entities(text)
