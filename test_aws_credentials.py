import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import sys
sys.path.insert(0, 'api')

try:
    from config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    
    print("Testing AWS Credentials...")
    print(f"Region: {AWS_REGION}")
    print(f"Access Key ID: {AWS_ACCESS_KEY_ID[:4]}...{AWS_ACCESS_KEY_ID[-4:]} (length: {len(AWS_ACCESS_KEY_ID)})")
    print(f"Secret Key: {'*' * 10} (length: {len(AWS_SECRET_ACCESS_KEY)})")
    print("-" * 60)
    
    # Test Textract
    print("\n1. Testing AWS Textract...")
    try:
        textract = boto3.client(
            'textract',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        # Just test the connection
        print("   ✓ Textract client created successfully")
    except Exception as e:
        print(f"   ✗ Textract error: {e}")
    
    # Test Comprehend Medical
    print("\n2. Testing AWS Comprehend Medical...")
    try:
        comprehend = boto3.client(
            'comprehendmedical',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        print("   ✓ Comprehend Medical client created successfully")
        
        # Try a simple test
        test_text = "Patient prescribed Aspirin 100mg twice daily"
        result = comprehend.detect_entities_v2(Text=test_text)
        print(f"   ✓ Successfully detected {len(result.get('Entities', []))} entities in test text")
        
    except Exception as e:
        print(f"   ✗ Comprehend Medical error: {e}")
    
    print("\n" + "=" * 60)
    print("Credential validation complete!")
    
except ImportError:
    print("Error: Could not import config.py")
    print("Make sure config.py exists in the api folder")
except Exception as e:
    print(f"Unexpected error: {e}")
