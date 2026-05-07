#!/usr/bin/env python3
"""
Debug script to trace the email flow in the application
This adds detailed logging to understand what's happening
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_mail import Mail, Message

# Load environment variables
load_dotenv('frontend/.env')

# Create Flask app
app = Flask(__name__)
app.config.update(dict(
    MAIL_DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = os.environ.get('email', ''),
    MAIL_PASSWORD = os.environ.get('pass', '')
))

mail = Mail(app)

# Simple HTML body for testing
def mail_body(message):
    return f"""
    <html>
        <body>
            <h2>Medicine Reminder</h2>
            <p>{message}</p>
        </body>
    </html>
    """

def send_mail(message, mail_id):
    """Exact copy of the send_mail function from app.py"""
    with app.app_context():
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📧 Attempting to send email...")
            print(f"  To: {mail_id}")
            print(f"  Message: {message}")
            
            msg = Message(
                'Hello', 
                sender=os.environ.get('email', 'noreply@mediscribe.com'), 
                recipients=[mail_id]
            )
            msg.html = mail_body(message)
            
            print(f"  Sending via Flask-Mail...")
            mail.send(msg)
            print(f"  ✅ Sent successfully!")
            return True
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

def simulate_scan_with_email():
    """Simulate what happens when a prescription is scanned with email"""
    
    print("=" * 70)
    print("SIMULATING PRESCRIPTION SCAN WITH EMAIL REMINDERS")
    print("=" * 70)
    
    # Simulate extracted medicines with duration
    medicines_list = [
        ("Paracetamol 500mg", "1-0-1 for 5 days"),
        ("Amoxicillin 250mg", "Take twice daily for 7 days"),
        ("Vitamin D", "Once daily for 30 days"),
        ("Cough Syrup", "10ml three times for 3 days"),
        ("Aspirin", "As needed for 10 days")
    ]
    
    email = input("\nEnter email address to receive reminders: ").strip()
    
    if not email:
        print("No email provided, exiting")
        return
    
    # Check if email is configured
    email_configured = os.environ.get('email') and os.environ.get('pass')
    print(f"\n✅ Email configured: {email_configured}")
    print(f"✅ Recipient email: {email}")
    print(f"✅ Medicines found: {len(medicines_list)}")
    
    if not email_configured:
        print("\n❌ Email not configured in .env file!")
        return
    
    # Start scheduler
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    scheduler.start()
    print(f"\n✅ Scheduler started at {datetime.now().strftime('%H:%M:%S')}")
    
    # Extract duration and schedule emails (same logic as app.py)
    import re
    working_list = []
    
    print("\n" + "=" * 70)
    print("PARSING MEDICINE DURATIONS")
    print("=" * 70)
    
    for med_name, dosage_info in medicines_list:
        print(f"\n📋 Medicine: {med_name}")
        print(f"   Dosage info: {dosage_info}")
        
        # Extract duration in days from dosage info
        duration_match = re.search(r'(\d+)\s*(?:days?|d)', dosage_info, re.IGNORECASE)
        if duration_match:
            days = int(duration_match.group(1))
            working_list.append((med_name, days))
            print(f"   ✅ Duration found: {days} days")
        else:
            # Try to find any number that could be duration
            numbers = re.findall(r'\d+', dosage_info)
            if numbers:
                potential_duration = max([int(n) for n in numbers])
                if potential_duration >= 3 and potential_duration <= 365:
                    working_list.append((med_name, potential_duration))
                    print(f"   ✅ Duration inferred: {potential_duration} days")
                else:
                    print(f"   ⚠️  Number found ({potential_duration}) but out of range")
            else:
                print(f"   ❌ No duration found")
    
    print("\n" + "=" * 70)
    print(f"SCHEDULING REMINDERS FOR {len(working_list)} MEDICINES")
    print("=" * 70)
    
    # Schedule reminders
    for med_name, duration_days in working_list:
        end_date = datetime.now() + timedelta(days=duration_days)
        
        print(f"\n💊 {med_name} ({duration_days} days)")
        
        # Send immediate reminder (5 seconds from now)
        message = f"Remember to take: {med_name} for the next {duration_days} days"
        run_time = datetime.now() + timedelta(seconds=5)
        print(f"   📧 Immediate reminder scheduled for: {run_time.strftime('%H:%M:%S')}")
        
        job = scheduler.add_job(
            send_mail, 
            'date', 
            [message, email], 
            run_date=run_time
        )
        
        # Schedule daily reminders
        daily_start = datetime.now() + timedelta(days=1)
        print(f"   📧 Daily reminders: {daily_start.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        job = scheduler.add_job(
            send_mail, 
            'interval', 
            [f"Daily reminder: {med_name}", email], 
            days=1, 
            start_date=daily_start,
            end_date=end_date
        )
    
    print(f"\n✅ Scheduled reminders for {len(working_list)} medicines")
    
    # Wait for immediate emails to be sent
    print("\n" + "=" * 70)
    print("WAITING FOR IMMEDIATE REMINDERS TO BE SENT")
    print("This will take about 10 seconds...")
    print("=" * 70)
    
    import time
    for i in range(10):
        time.sleep(1)
        print(f"⏱️  {i+1}/10 seconds", end='\r')
    
    print("\n\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"✅ {len(working_list)} immediate emails should have been sent")
    print(f"✅ Daily reminders will be sent starting tomorrow")
    print(f"✅ Check your inbox (and spam folder)")
    print("=" * 70)
    
    # Keep scheduler running for a bit longer
    print("\nKeeping scheduler alive for 5 more seconds...")
    time.sleep(5)
    
    scheduler.shutdown()
    print("✅ Scheduler shut down\n")

if __name__ == "__main__":
    simulate_scan_with_email()
