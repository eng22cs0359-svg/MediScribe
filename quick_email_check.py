#!/usr/bin/env python3
"""
Quick Email Check - Verify email configuration in 30 seconds
"""

import os
import sys
from dotenv import load_dotenv
import smtplib

# Load environment variables
load_dotenv('frontend/.env')

def main():
    print("\n" + "="*60)
    print("QUICK EMAIL CONFIGURATION CHECK")
    print("="*60)
    
    # Check 1: Environment variables
    email = os.environ.get('email', '')
    password = os.environ.get('pass', '')
    
    print("\n1. Environment Variables:")
    if email and password:
        print(f"   ✅ Email: {email}")
        print(f"   ✅ Password: {'*' * len(password)} ({len(password)} chars)")
    else:
        print("   ❌ Email credentials not found in .env file")
        return False
    
    # Check 2: SMTP Connection
    print("\n2. SMTP Connection Test:")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.starttls()
        server.login(email, password)
        server.quit()
        print("   ✅ Successfully connected to Gmail SMTP")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    # Check 3: Send test email
    print("\n3. Send Test Email:")
    recipient = input("   Enter email to send test to (or press Enter to skip): ").strip()
    
    if recipient:
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['Subject'] = 'ScanPlus Quick Test'
            msg['From'] = email
            msg['To'] = recipient
            msg.attach(MIMEText('This is a quick test from ScanPlus. Email is working!', 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email, password)
            server.sendmail(email, recipient, msg.as_string())
            server.quit()
            
            print(f"   ✅ Test email sent to {recipient}")
            print("   📧 Check your inbox (and spam folder)")
        except Exception as e:
            print(f"   ❌ Failed to send: {e}")
            return False
    else:
        print("   ⏭️  Skipped")
    
    # Summary
    print("\n" + "="*60)
    print("RESULT: ✅ Email system is working correctly!")
    print("="*60)
    print("\nIf you're not receiving emails from the app:")
    print("1. Check your SPAM folder")
    print("2. Ensure the app stays running for 10+ seconds after scan")
    print("3. Verify the email field is filled in the scan form")
    print("4. Check that prescriptions contain duration info (e.g., '5 days')")
    print("="*60 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
