#!/usr/bin/env python3
"""
Email Configuration Test Script
Tests the email sending functionality with the configured credentials
"""

import os
import sys
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

# Load environment variables
load_dotenv('frontend/.env')

def test_env_loading():
    """Test if environment variables are loaded correctly"""
    print("=" * 60)
    print("STEP 1: Testing Environment Variable Loading")
    print("=" * 60)
    
    email = os.environ.get('email', '')
    password = os.environ.get('pass', '')
    
    print(f"Email loaded: {email}")
    print(f"Password loaded: {'*' * len(password) if password else '(empty)'}")
    print(f"Password length: {len(password)}")
    
    if not email or not password:
        print("\n❌ ERROR: Email credentials not loaded from .env file!")
        return False
    
    print("\n✅ Environment variables loaded successfully")
    return True

def test_smtp_connection():
    """Test SMTP connection to Gmail"""
    print("\n" + "=" * 60)
    print("STEP 2: Testing SMTP Connection")
    print("=" * 60)
    
    email = os.environ.get('email', '')
    password = os.environ.get('pass', '')
    
    try:
        print("Connecting to smtp.gmail.com:587...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(1)  # Enable debug output
        
        print("\nStarting TLS...")
        server.starttls()
        
        print(f"\nLogging in as {email}...")
        server.login(email, password)
        
        print("\n✅ SMTP connection and authentication successful!")
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\nPossible issues:")
        print("1. App password is incorrect")
        print("2. 2-factor authentication not enabled on Gmail")
        print("3. App password not generated correctly")
        return False
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False

def test_send_email(recipient_email):
    """Test sending an actual email"""
    print("\n" + "=" * 60)
    print("STEP 3: Testing Email Sending")
    print("=" * 60)
    
    sender_email = os.environ.get('email', '')
    password = os.environ.get('pass', '')
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'ScanPlus Email Test'
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Create plain text and HTML versions
        text = "This is a test email from ScanPlus to verify email functionality."
        html = """
        <html>
          <body>
            <h2>ScanPlus Email Test</h2>
            <p>This is a test email to verify email functionality.</p>
            <p><strong>If you received this, email sending is working correctly!</strong></p>
          </body>
        </html>
        """
        
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        print(f"Sending test email to {recipient_email}...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        
        print(f"\n✅ Test email sent successfully to {recipient_email}!")
        print("Please check your inbox (and spam folder)")
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to send email: {e}")
        return False

def test_flask_mail_config():
    """Test Flask-Mail configuration"""
    print("\n" + "=" * 60)
    print("STEP 4: Testing Flask-Mail Configuration")
    print("=" * 60)
    
    email = os.environ.get('email', '')
    password = os.environ.get('pass', '')
    
    config = {
        'MAIL_SERVER': 'smtp.gmail.com',
        'MAIL_PORT': 587,
        'MAIL_USE_TLS': True,
        'MAIL_USE_SSL': False,
        'MAIL_USERNAME': email,
        'MAIL_PASSWORD': password
    }
    
    print("Flask-Mail Configuration:")
    for key, value in config.items():
        if 'PASSWORD' in key:
            print(f"  {key}: {'*' * len(str(value))}")
        else:
            print(f"  {key}: {value}")
    
    if not email or not password:
        print("\n❌ Flask-Mail configuration incomplete!")
        return False
    
    print("\n✅ Flask-Mail configuration looks correct")
    return True

def main():
    print("\n" + "=" * 60)
    print("ScanPlus Email Configuration Test")
    print("=" * 60)
    
    # Test 1: Environment variables
    if not test_env_loading():
        print("\n❌ FAILED: Cannot proceed without credentials")
        sys.exit(1)
    
    # Test 2: SMTP connection
    if not test_smtp_connection():
        print("\n❌ FAILED: Cannot connect to SMTP server")
        sys.exit(1)
    
    # Test 3: Flask-Mail config
    test_flask_mail_config()
    
    # Test 4: Send test email
    print("\n" + "=" * 60)
    recipient = input("\nEnter email address to send test email to (or press Enter to skip): ").strip()
    
    if recipient:
        test_send_email(recipient)
    else:
        print("Skipping email send test")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("✅ Environment variables: OK")
    print("✅ SMTP connection: OK")
    print("✅ Flask-Mail config: OK")
    if recipient:
        print("✅ Email sending: Check your inbox")
    print("\nIf all tests passed, the email functionality should work in the app.")
    print("=" * 60)

if __name__ == "__main__":
    main()
