"""
Script to train the NER model.
Run this script to train the model before using the prediction functionality.
"""
import sparknlp
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from sparknlp.annotator import *
from sparknlp.training import CoNLL
from sparknlp.base import DocumentAssembler
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_ner_model():
    """Train the NER model using the training dataset."""
    
    logger.info("Starting Spark NLP session...")
    # Configure Spark to work with Windows SSL certificates
    import os
    
    # Set environment variable for SSL
    os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages com.johnsnowlabs.nlp:spark-nlp_2.12:5.5.0 pyspark-shell'
    
    # Start Spark session with Windows-compatible settings
    spark = SparkSession.builder \
        .appName("Spark NLP") \
        .master("local[*]") \
        .config("spark.driver.memory", "4g") \
        .config("spark.driver.maxResultSize", "2g") \
        .config("spark.kryoserializer.buffer.max", "2000M") \
        .config("spark.jars.packages", "com.johnsnowlabs.nlp:spark-nlp_2.12:5.5.0") \
        .config("spark.driver.extraJavaOptions", "-Djavax.net.ssl.trustStoreType=Windows-ROOT") \
        .getOrCreate()
    
    logger.info("Loading BERT embeddings...")
    bert_embeddings = BertEmbeddings.pretrained('bert_base_uncased', 'en') \
        .setInputCols(["sentence", 'token']) \
        .setOutputCol("embeddings") \
        .setCaseSensitive(False)
    
    logger.info("Configuring NER tagger...")
    ner_tagger = NerDLApproach() \
        .setInputCols(["sentence", "token", "embeddings"]) \
        .setLabelColumn("label") \
        .setOutputCol("ner") \
        .setMaxEpochs(20) \
        .setLr(0.001) \
        .setPo(0.005) \
        .setBatchSize(32) \
        .setValidationSplit(0.1) \
        .setUseBestModel(True) \
        .setEnableOutputLogs(True)
    
    logger.info("Loading training data...")
    training_data = CoNLL().readDataset(spark, "../content/NERDataset.txt")
    training_data = bert_embeddings.transform(training_data).drop("text", "document", "pos")
    
    logger.info("Training model... This may take a while.")
    ner_model = ner_tagger.fit(training_data)
    logger.info("Model trained successfully!")
    
    logger.info("Saving model...")
    ner_model.write().overwrite().save("../content/model")
    logger.info("Model saved at: ../content/model")
    
    spark.stop()
    logger.info("Training complete!")

if __name__ == "__main__":
    train_ner_model()
