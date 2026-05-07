"""
Email Configuration Setup for ScanPlus
This script helps you configure Gmail for sending medication reminders.
"""

import os
import sys
import getpass

def setup_email():
    print("=" * 60)
    print("ScanPlus Email Configuration Setup")
    print("=" * 60)
    print()
    print("This will configure Gmail to send medication reminders.")
    print()
    
    # Get email
    print("Step 1: Enter your Gmail address")
    print("-" * 60)
    email = input("Gmail address: ").strip()
    
    if not email:
        print("❌ Email address is required!")
        return False
    
    if '@gmail.com' not in email.lower():
        print("⚠️  Warning: This setup is optimized for Gmail.")
        proceed = input("Continue anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            return False
    
    print()
    
    # Get app password
    print("Step 2: Enter your Gmail App Password")
    print("-" * 60)
    print("📌 Don't have an App Password? Follow these steps:")
    print("   1. Go to: https://myaccount.google.com/security")
    print("   2. Enable 2-Step Verification (if not enabled)")
    print("   3. Search for 'App passwords'")
    print("   4. Select 'Mail' and 'Windows Computer'")
    print("   5. Click 'Generate' and copy the 16-character password")
    print()
    
    app_password = getpass.getpass("App Password (hidden): ").strip()
    
    if not app_password:
        print("❌ App password is required!")
        return False
    
    # Remove spaces from app password
    app_password = app_password.replace(' ', '')
    
    print()
    
    # Confirm
    print("Step 3: Confirm Configuration")
    print("-" * 60)
    print(f"Email: {email}")
    print(f"App Password: {'*' * len(app_password)}")
    print()
    
    confirm = input("Save this configuration? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("❌ Configuration cancelled.")
        return False
    
    # Set environment variables (permanent)
    try:
        # For Windows
        if sys.platform == 'win32':
            os.system(f'setx email "{email}"')
            os.system(f'setx pass "{app_password}"')
            print()
            print("✅ Configuration saved successfully!")
            print()
            print("⚠️  IMPORTANT: You must restart your terminal/IDE for changes to take effect!")
            print()
            print("Next steps:")
            print("1. Close this terminal")
            print("2. Open a new terminal")
            print("3. Restart the frontend: cd ScanPlus/frontend && python app.py")
        else:
            # For Linux/Mac
            print()
            print("✅ Configuration complete!")
            print()
            print("Add these lines to your ~/.bashrc or ~/.zshrc:")
            print(f'export email="{email}"')
            print(f'export pass="{app_password}"')
            print()
            print("Then run: source ~/.bashrc (or ~/.zshrc)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False

def test_email():
    """Test if email is configured"""
    email = os.environ.get('email', '')
    password = os.environ.get('pass', '')
    
    print()
    print("=" * 60)
    print("Email Configuration Test")
    print("=" * 60)
    print()
    
    if email and password:
        print(f"✅ Email configured: {email}")
        print(f"✅ Password configured: {'*' * len(password)}")
        print()
        print("Email reminders are ready to use!")
        return True
    else:
        print("❌ Email not configured")
        print()
        if not email:
            print("Missing: email environment variable")
        if not password:
            print("Missing: pass environment variable")
        print()
        print("Run this script to configure email.")
        return False

if __name__ == "__main__":
    print()
    
    # Check if already configured
    if os.environ.get('email') and os.environ.get('pass'):
        print("Email is already configured!")
        print()
        choice = input("Do you want to reconfigure? (y/n): ").strip().lower()
        if choice != 'y':
            test_email()
            sys.exit(0)
    
    # Run setup
    success = setup_email()
    
    if success:
        print()
        print("=" * 60)
        print("Setup Complete!")
        print("=" * 60)
        print()
        print("📧 Email reminders will be sent when:")
        print("   - You scan a prescription")
        print("   - Enter an email address")
        print("   - Medicine has a duration (e.g., 7 days, 30 days)")
        print()
        print("The system will send daily reminders until the medicine duration ends.")
        print()
    else:
        print()
        print("Setup was not completed. Email reminders will not work.")
        print("You can run this script again anytime to configure email.")
        print()
