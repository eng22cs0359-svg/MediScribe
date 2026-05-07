#!/usr/bin/env python3
"""
Test the email scheduler functionality
This simulates what happens when the app schedules email reminders
"""

import os
import sys
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_mail import Mail, Message

# Load environment variables
load_dotenv('frontend/.env')

# Create a minimal Flask app
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

def send_mail_test(message, mail_id):
    """Test version of send_mail function"""
    with app.app_context():
        try:
            msg = Message(
                'ScanPlus Reminder Test', 
                sender=os.environ.get('email', 'noreply@mediscribe.com'), 
                recipients=[mail_id]
            )
            msg.body = message
            msg.html = f"<html><body><h2>Test Reminder</h2><p>{message}</p></body></html>"
            mail.send(msg)
            print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Email sent: {message}")
            return True
        except Exception as e:
            print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Failed to send email: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    print("=" * 60)
    print("Testing APScheduler Email Functionality")
    print("=" * 60)
    
    recipient = input("Enter email address to receive test reminders: ").strip()
    if not recipient:
        print("No email provided, exiting")
        sys.exit(1)
    
    # Create scheduler
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    scheduler.start()
    print(f"\n✅ Scheduler started at {datetime.now().strftime('%H:%M:%S')}")
    
    # Schedule immediate test email (5 seconds from now)
    print(f"\n📧 Scheduling immediate test email for {(datetime.now() + timedelta(seconds=5)).strftime('%H:%M:%S')}")
    job1 = scheduler.add_job(
        send_mail_test, 
        'date', 
        [f"Immediate test at {datetime.now().strftime('%H:%M:%S')}", recipient], 
        run_date=datetime.now() + timedelta(seconds=5)
    )
    
    # Schedule another email 15 seconds from now
    print(f"📧 Scheduling second test email for {(datetime.now() + timedelta(seconds=15)).strftime('%H:%M:%S')}")
    job2 = scheduler.add_job(
        send_mail_test, 
        'date', 
        [f"Second test at {datetime.now().strftime('%H:%M:%S')}", recipient], 
        run_date=datetime.now() + timedelta(seconds=15)
    )
    
    print("\n" + "=" * 60)
    print("Waiting for scheduled emails to be sent...")
    print("This will take about 20 seconds")
    print("=" * 60)
    
    # Wait for jobs to execute
    for i in range(20):
        time.sleep(1)
        print(f"⏱️  Waiting... {i+1}/20 seconds", end='\r')
    
    print("\n\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
    print("Check your email inbox (and spam folder)")
    print("You should have received 2 test emails")
    
    # Shutdown scheduler
    scheduler.shutdown()
    print("\n✅ Scheduler shut down")

if __name__ == "__main__":
    main()
