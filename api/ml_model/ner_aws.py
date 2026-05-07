"""
NER module using AWS Comprehend Medical for high-accuracy medical entity extraction.
This replaces Spark NLP with a cloud-based solution that works on any platform.
"""
import boto3
import logging
from botocore.exceptions import BotoCoreError, ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AWSMedicalNER:
    def __init__(self, region_name='us-east-1', aws_access_key_id=None, aws_secret_access_key=None):
        """
        Initialize AWS Comprehend Medical client.
        
        Args:
            region_name: AWS region (default: us-east-1)
            aws_access_key_id: AWS access key
            aws_secret_access_key: AWS secret key
        """
        try:
            self.client = boto3.client(
                'comprehendmedical',
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
            logger.info("AWS Comprehend Medical client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AWS Comprehend Medical: {e}")
            raise
    
    def predict(self, text):
        """
        Extract medical entities from text using AWS Comprehend Medical.
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            dict: Dictionary with entity types as keys and lists of (text, (start, end)) tuples as values
        """
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for prediction")
            return {}
        
        try:
            # Detect medical entities
            response = self.client.detect_entities_v2(Text=text)
            
            result_dict = {}
            
            # Process entities
            for entity in response.get('Entities', []):
                entity_type = entity.get('Category', 'UNKNOWN')
                entity_text = entity.get('Text', '')
                begin_offset = entity.get('BeginOffset', 0)
                end_offset = entity.get('EndOffset', 0)
                confidence = entity.get('Score', 0.0)
                
                # Only include entities with reasonable confidence
                if confidence > 0.5:
                    # Map AWS categories to more user-friendly names
                    category_map = {
                        'MEDICATION': 'Medicine',
                        'MEDICAL_CONDITION': 'Condition',
                        'DOSAGE': 'Dosage',
                        'STRENGTH': 'Strength',
                        'FREQUENCY': 'Frequency',
                        'DURATION': 'Duration',
                        'ROUTE_OR_MODE': 'Route',
                        'TEST_TREATMENT_PROCEDURE': 'Procedure',
                        'ANATOMY': 'Anatomy',
                        'PROTECTED_HEALTH_INFORMATION': 'PHI'
                    }
                    
                    friendly_type = category_map.get(entity_type, entity_type)
                    
                    if friendly_type not in result_dict:
                        result_dict[friendly_type] = []
                    
                    result_dict[friendly_type].append(
                        (entity_text, (begin_offset, end_offset))
                    )
            
            logger.info(f"Extracted {len(response.get('Entities', []))} entities from text")
            return result_dict
            
        except (BotoCoreError, ClientError) as e:
            logger.error(f"AWS Comprehend Medical error: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during prediction: {e}")
            return {"error": str(e)}
    
    def format_output(self, entities_dict):
        """
        Format the output for display.
        
        Args:
            entities_dict: Dictionary of entities
            
        Returns:
            dict: Formatted dictionary with just entity texts
        """
        if "error" in entities_dict:
            return entities_dict
        
        formatted = {}
        for entity_type, entities in entities_dict.items():
            formatted[entity_type] = [text for text, _ in entities]
        
        return formatted


# Singleton instance
_ner_instance = None

def get_ner_model(region_name='us-east-1', aws_access_key_id=None, aws_secret_access_key=None):
    """
    Get or create the NER model instance.
    
    Args:
        region_name: AWS region
        aws_access_key_id: AWS access key
        aws_secret_access_key: AWS secret key
        
    Returns:
        AWSMedicalNER: NER model instance
    """
    global _ner_instance
    if _ner_instance is None:
        _ner_instance = AWSMedicalNER(
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
    return _ner_instance


# For backward compatibility with existing code
class InitiateNER:
    """Wrapper class for backward compatibility with existing API code."""
    
    def __init__(self, region_name='us-east-1', aws_access_key_id=None, aws_secret_access_key=None):
        self.ner = AWSMedicalNER(
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        logger.info("AWS Medical NER initialized")
    
    def load_model(self, model_path=None):
        """For compatibility - AWS Comprehend doesn't need local model loading."""
        logger.info("Using AWS Comprehend Medical - no local model needed")
        pass
    
    def predict(self, text):
        """Predict entities in text."""
        return self.ner.predict(text)


# Example usage
if __name__ == "__main__":
    # Test with sample medical text
    sample_text = """
    Patient: John Doe
    Prescription: Aspirin 100mg, take twice daily for 30 days
    Diagnosis: Hypertension
    """
    
    # Initialize (replace with your AWS credentials)
    ner = InitiateNER(
        region_name='us-east-1',
        aws_access_key_id='YOUR_ACCESS_KEY',
        aws_secret_access_key='YOUR_SECRET_KEY'
    )
    
    # Predict
    result = ner.predict(sample_text)
    print("Entities found:")
    for entity_type, entities in result.items():
        print(f"\n{entity_type}:")
        for text, (start, end) in entities:
            print(f"  - {text} (position {start}-{end})")
