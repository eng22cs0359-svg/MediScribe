"""
Configuration Template
Copy this file to config.py and fill in your actual credentials.

IMPORTANT: 
- Never commit config.py with real credentials to git!
- Add config.py to .gitignore
"""

# ============================================
# AWS Configuration
# ============================================
# Get these from AWS Console > IAM > Users > Security Credentials
AWS_REGION = 'us-east-1'  # e.g., 'us-east-1', 'us-west-2', 'eu-west-1'
AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE'  # Replace with your actual access key
AWS_SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'  # Replace with your actual secret key

# ============================================
# Database Configuration
# ============================================
SQLALCHEMY_DATABASE_URI = "sqlite:///database.sqlite"

# ============================================
# JWT Configuration
# ============================================
JWT_SECRET_KEY = "change-this-to-a-random-secret-key-123456"  # Change this!
JWT_COOKIE_SECURE = False  # Set to True in production with HTTPS
JWT_TOKEN_LOCATION = ["headers"]

# ============================================
# Upload Folders
# ============================================
UPLOAD_FOLDER_PFP = "images/pfp"
UPLOAD_FOLDER_PRESCRIPTIONS = "images/prescriptions"

# ============================================
# Email Configuration (Optional - for notifications)
# ============================================
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = 'your-email@gmail.com'  # Your email
MAIL_PASSWORD = 'your-app-specific-password'  # Gmail app password (not your regular password)

# ============================================
# How to Get AWS Credentials:
# ============================================
# 1. Log in to AWS Console: https://console.aws.amazon.com/
# 2. Go to IAM (Identity and Access Management)
# 3. Click "Users" in the left sidebar
# 4. Click your username (or create a new user)
# 5. Click "Security credentials" tab
# 6. Click "Create access key"
# 7. Copy the Access Key ID and Secret Access Key
# 8. Paste them above
#
# Required Permissions:
# - AmazonTextractFullAccess (for OCR)
# - ComprehendMedicalFullAccess (for NER)
