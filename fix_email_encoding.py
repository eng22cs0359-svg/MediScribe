import sqlite3
import sys
import os

# Add the api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from models import db, App_user, Prescription
from api import app

def fix_email_encoding():
    """Fix email encoding in database - convert bytes to strings"""
    with app.app_context():
        print("Starting email encoding fix...")
        
        # Fix users
        users = App_user.query.all()
        users_fixed = 0
        
        for user in users:
            if isinstance(user.email, bytes):
                old_email = user.email
                user.email = user.email.decode('utf-8')
                users_fixed += 1
                print(f"Fixed user email: {old_email} -> {user.email}")
        
        # Fix prescriptions
        prescriptions = Prescription.query.all()
        prescriptions_fixed = 0
        
        for prescription in prescriptions:
            if isinstance(prescription.user_email, bytes):
                old_email = prescription.user_email
                prescription.user_email = prescription.user_email.decode('utf-8')
                prescriptions_fixed += 1
                print(f"Fixed prescription email: {old_email} -> {prescription.user_email}")
        
        # Commit changes
        db.session.commit()
        
        print(f"\nMigration complete!")
        print(f"Users fixed: {users_fixed}")
        print(f"Prescriptions fixed: {prescriptions_fixed}")

if __name__ == '__main__':
    fix_email_encoding()
