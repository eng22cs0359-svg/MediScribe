#!/usr/bin/env python3
"""
Test script to verify email sending functionality
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv('frontend/.env')

def test_email_config():
    """Test if email credentials are loaded correctly"""
    email = os.environ.get('email')
    password = os.environ.get('pass')
    
    print("=" * 50)
    print("Email Configuration Test")
    print("=" * 50)
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
    print(f"SMTP Server: smtp.gmail.com:587")
    print()
    
    if not email or not password:
        print("❌ ERROR: Email credentials not found in .env file")
        return False
    
    print("✅ Email credentials loaded successfully")
    return True

def test_smtp_connection():
    """Test SMTP connection and authentication"""
    email = os.environ.get('email')
    password = os.environ.get('pass')
    
    print("=" * 50)
    print("SMTP Connection Test")
    print("=" * 50)
    
    try:
        # Connect to Gmail SMTP server
        print("Connecting to smtp.gmail.com:587...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(0)  # Set to 1 for verbose output
        
        print("Starting TLS...")
        server.starttls()
        
        print("Logging in...")
        server.login(email, password)
        
        print("✅ SMTP connection and authentication successful!")
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\nPossible issues:")
        print("1. Incorrect email or password")
        print("2. 2-Step Verification not enabled on Gmail")
        print("3. App password not generated or incorrect")
        print("4. 'Less secure app access' needs to be enabled (if not using app password)")
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def send_test_email(recipient=None):
    """Send a test email"""
    email = os.environ.get('email')
    password = os.environ.get('pass')
    
    if not recipient:
        recipient = email  # Send to self if no recipient specified
    
    print("=" * 50)
    print("Test Email Send")
    print("=" * 50)
    print(f"From: {email}")
    print(f"To: {recipient}")
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = recipient
        msg['Subject'] = 'MediScribe Email Test'
        
        body = """
        <html>
        <body>
            <h2>MediScribe Email Test</h2>
            <p>This is a test email from MediScribe prescription reminder system.</p>
            <p>If you received this email, the email configuration is working correctly!</p>
            <hr>
            <p><small>Sent from MediScribe test script</small></p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect and send
        print("Connecting to SMTP server...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, password)
        
        print("Sending email...")
        server.send_message(msg)
        server.quit()
        
        print("✅ Test email sent successfully!")
        print(f"Check inbox at: {recipient}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def main():
    print("\n" + "=" * 50)
    print("MediScribe Email Testing Suite")
    print("=" * 50 + "\n")
    
    # Test 1: Check configuration
    if not test_email_config():
        return
    
    print()
    
    # Test 2: Test SMTP connection
    if not test_smtp_connection():
        return
    
    print()
    
    # Test 3: Send test email
    print("Would you like to send a test email? (y/n): ", end='')
    try:
        response = input().strip().lower()
        if response == 'y':
            print("Enter recipient email (press Enter to send to yourself): ", end='')
            recipient = input().strip()
            send_test_email(recipient if recipient else None)
    except:
        # If running in non-interactive mode, send to self
        print("Running in non-interactive mode, sending test email to self...")
        send_test_email()
    
    print("\n" + "=" * 50)
    print("Testing Complete")
    print("=" * 50)

if __name__ == "__main__":
    main()
