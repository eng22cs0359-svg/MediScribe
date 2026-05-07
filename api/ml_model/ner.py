"""
NER module with AWS Comprehend Medical and spaCy fallback.
"""
import boto3
import logging
from botocore.exceptions import BotoCoreError, ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InitiateNER:
    """
    NER class with AWS Comprehend Medical primary and spaCy fallback.
    """
    
    def __init__(self, region_name='us-east-1', aws_access_key_id=None, aws_secret_access_key=None):
        """
        Initialize NER with AWS Comprehend Medical and spaCy fallback.
        """
        self.use_aws = False
        self.spacy_ner = None
        
        # Try AWS Comprehend Medical first
        try:
            client_kwargs = {
                'service_name': 'comprehendmedical',
                'region_name': region_name
            }
            
            if aws_access_key_id and aws_secret_access_key:
                client_kwargs['aws_access_key_id'] = aws_access_key_id
                client_kwargs['aws_secret_access_key'] = aws_secret_access_key
            
            self.client = boto3.client(**client_kwargs)
            
            # Test if we have permissions
            test_response = self.client.detect_entities_v2(Text="test")
            self.use_aws = True
            logger.info("AWS Comprehend Medical initialized successfully")
            
        except Exception as e:
            logger.warning(f"AWS Comprehend Medical not available: {e}")
            logger.info("Falling back to rule-based medical NER")
            
            # Load rule-based medical NER as fallback
            try:
                from ml_model.medical_ner import MedicalNER
                self.spacy_ner = MedicalNER()
                logger.info("Rule-based medical NER loaded successfully")
            except Exception as fallback_error:
                logger.error(f"Failed to load medical NER fallback: {fallback_error}")
                raise Exception("No NER model available")
    
    def load_model(self, model_path=None):
        """For compatibility with existing code."""
        pass
    
    def predict(self, text):
        """
        Extract medical entities from text.
        """
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for prediction")
            return {}
        
        if self.use_aws:
            return self._predict_aws(text)
        else:
            return self._predict_spacy(text)
    
    def _predict_aws(self, text):
        """Use AWS Comprehend Medical for prediction."""
        try:
            response = self.client.detect_entities_v2(Text=text)
            result_dict = {}
            
            for entity in response.get('Entities', []):
                entity_type = entity.get('Category', 'UNKNOWN')
                entity_text = entity.get('Text', '')
                begin_offset = entity.get('BeginOffset', 0)
                end_offset = entity.get('EndOffset', 0)
                confidence = entity.get('Score', 0.0)
                
                if confidence > 0.5:
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
                        'PROTECTED_HEALTH_INFORMATION': 'PatientInfo'
                    }
                    
                    friendly_type = category_map.get(entity_type, entity_type)
                    
                    if friendly_type not in result_dict:
                        result_dict[friendly_type] = []
                    
                    result_dict[friendly_type].append(
                        (entity_text, (begin_offset, end_offset))
                    )
            
            logger.info(f"AWS extracted {len(response.get('Entities', []))} entities")
            return result_dict
            
        except Exception as e:
            logger.error(f"AWS Comprehend Medical error: {e}")
            return {"error": str(e)}
    
    def _predict_spacy(self, text):
        """Use rule-based medical NER for prediction."""
        try:
            if self.spacy_ner:
                result = self.spacy_ner.predict(text)
                logger.info(f"Medical NER extracted entities from text")
                return result
            else:
                return {"error": "No NER model available"}
        except Exception as e:
            logger.error(f"Medical NER prediction error: {e}")
            return {"error": str(e)}