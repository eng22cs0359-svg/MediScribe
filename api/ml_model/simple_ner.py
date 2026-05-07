"""
Simplified NER implementation using spaCy instead of Spark NLP.
This is more Windows-friendly and doesn't require complex setup.
"""
import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
import random
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_training_data(file_path):
    """Load training data from CoNLL format."""
    logger.info(f"Loading training data from {file_path}")
    
    training_data = []
    current_text = []
    current_entities = []
    current_pos = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            if not line or line.startswith('-DOCSTART-'):
                if current_text:
                    text = ' '.join(current_text)
                    training_data.append((text, {"entities": current_entities}))
                    current_text = []
                    current_entities = []
                    current_pos = 0
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                word = parts[0]
                tag = parts[-1]  # Last column is the NER tag
                
                start = current_pos
                end = start + len(word)
                
                if tag != 'O' and not tag.startswith('O-'):
                    # Remove B- or I- prefix
                    entity_type = tag.split('-')[-1] if '-' in tag else tag
                    current_entities.append((start, end, entity_type))
                
                current_text.append(word)
                current_pos = end + 1  # +1 for space
    
    # Add last sentence if exists
    if current_text:
        text = ' '.join(current_text)
        training_data.append((text, {"entities": current_entities}))
    
    logger.info(f"Loaded {len(training_data)} training examples")
    return training_data

def train_ner_model():
    """Train a simple NER model using spaCy."""
    
    logger.info("Starting NER model training with spaCy...")
    
    # Create blank English model
    nlp = spacy.blank("en")
    
    # Create the NER component
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner")
    else:
        ner = nlp.get_pipe("ner")
    
    # Load training data
    training_data = load_training_data("../content/NERDataset.txt")
    
    # Add labels to NER
    for _, annotations in training_data:
        for ent in annotations.get("entities"):
            ner.add_label(ent[2])
    
    # Disable other pipes during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    with nlp.disable_pipes(*other_pipes):
        # Initialize the model
        nlp.initialize(lambda: [Example.from_dict(nlp.make_doc(text), annotations) 
                                for text, annotations in training_data[:10]])
        
        logger.info("Training model...")
        # Training loop
        for iteration in range(20):
            random.shuffle(training_data)
            losses = {}
            
            # Batch the examples
            batches = minibatch(training_data, size=compounding(4.0, 32.0, 1.001))
            
            for batch in batches:
                examples = []
                for text, annotations in batch:
                    doc = nlp.make_doc(text)
                    example = Example.from_dict(doc, annotations)
                    examples.append(example)
                
                nlp.update(examples, drop=0.5, losses=losses)
            
            logger.info(f"Iteration {iteration + 1}/20 - Loss: {losses.get('ner', 0):.4f}")
    
    # Save the model
    output_dir = Path("../content/spacy_model")
    output_dir.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(output_dir)
    logger.info(f"Model saved to {output_dir}")
    
    logger.info("Training complete!")

if __name__ == "__main__":
    train_ner_model()
