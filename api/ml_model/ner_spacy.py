"""
Simplified NER module using spaCy instead of Spark NLP.
This is more Windows-friendly and easier to set up.
"""
import spacy
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleNER:
    def __init__(self, model_path=None):
        """Initialize the NER model."""
        if model_path is None:
            # Use absolute path relative to this file
            import os
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(curr_dir, "..", "content", "spacy_model")
        self.model_path = Path(model_path)
        self.nlp = None
        
    def load_model(self):
        """Load the trained spaCy model."""
        try:
            if self.model_path.exists():
                self.nlp = spacy.load(self.model_path)
                logger.info(f"Model loaded from {self.model_path}")
            else:
                logger.warning(f"Model not found at {self.model_path}. Using blank model.")
                self.nlp = spacy.blank("en")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.nlp = spacy.blank("en")
    
    def predict(self, text):
        """
        Predict named entities in the given text.
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            dict: Dictionary with entity types as keys and lists of (text, (start, end)) tuples as values
        """
        if self.nlp is None:
            self.load_model()
        
        try:
            doc = self.nlp(text)
            result_dict = {}
            
            for ent in doc.ents:
                entity_type = ent.label_
                result_dict.setdefault(entity_type, []).append(
                    (ent.text, (ent.start_char, ent.end_char))
                )
            
            logger.info(f"Found {len(doc.ents)} entities in text")
            return result_dict
            
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            return {"error": str(e)}
    
    def format_output(self, entities_dict):
        """Format the output for display."""
        if "error" in entities_dict:
            return entities_dict
        
        formatted = {}
        for entity_type, entities in entities_dict.items():
            formatted[entity_type] = [text for text, _ in entities]
        
        return formatted


# For backward compatibility, create an instance
def get_ner_model():
    """Get or create the NER model instance."""
    if not hasattr(get_ner_model, 'instance'):
        get_ner_model.instance = SimpleNER()
        get_ner_model.instance.load_model()
    return get_ner_model.instance


# Example usage
if __name__ == "__main__":
    from ml_model import detect_text
    
    ner = SimpleNER()
    ner.load_model()
    
    # Test with an image
    text = detect_text("../images/prescriptions/check2.jpeg")
    result = ner.predict(text)
    print("Entities found:")
    print(ner.format_output(result))
