from flask import Flask, render_template, request, redirect, session, jsonify
import requests
from werkzeug.utils import secure_filename
import uuid
import os
import ast
import re
from apscheduler.schedulers.background import BackgroundScheduler
from htmlbody import *
from dotenv import load_dotenv

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from datetime import *
import smtplib



# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Debug: confirm keys loaded
_groq_key = os.environ.get('GROQ_API_KEY', '')
print(f"[STARTUP] GROQ key loaded: {bool(_groq_key)} | starts with: {_groq_key[:8] if _groq_key else 'MISSING'}")


app = Flask(__name__)

# Get the current directory
curr_dir = os.path.abspath(os.path.dirname(__file__))

# Configure Flask session for secure session cookie handling
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

app.config['UPLOAD_FOLDER_SCAN'] = os.path.join(curr_dir, "static", "temp")
upload_folder_prescriptions = os.path.join(curr_dir, "static", "prescriptions")
app.config["UPLOAD_FOLDER_prescriptions"] = upload_folder_prescriptions

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER_SCAN'], exist_ok=True)
os.makedirs(upload_folder_prescriptions, exist_ok=True)


scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
# scheduler.__init__(app)
scheduler.start()

api_url = "http://127.0.0.1:5000"

from flask_mail import Mail, Message

app.config.update(dict(
    MAIL_DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = os.environ.get('email', ''),
    MAIL_PASSWORD = os.environ.get('pass', '')
))

mail= Mail(app)

def is_doctor_name(name):
    """Check if a name appears to be a doctor's name"""
    if not name or not isinstance(name, str):
        return False
    
    name_lower = name.lower().strip()
    
    # Check for doctor titles/prefixes
    doctor_patterns = [
        r'\bdr\.?\s',  # Dr. or Dr followed by space
        r'\bdoctor\s',  # Doctor followed by space
        r'^dr\.?\s',  # Starts with Dr. or Dr
        r'^doctor\s',  # Starts with Doctor
    ]
    
    for pattern in doctor_patterns:
        if re.search(pattern, name_lower):
            return True
    
    return False

def extract_patient_name(name):
    """Extract and validate patient name, filtering out doctor names"""
    if not name or not isinstance(name, str):
        return "Not Mentioned"
    
    name = name.strip()
    
    # Check if it's a doctor name
    if is_doctor_name(name):
        return "Not Mentioned"
    
    # Return the name if it passes validation
    if len(name) > 0:
        return name
    
    return "Not Mentioned"

def send_mail(message, mail_id):
    """Send a single plain-text/HTML reminder email."""
    with app.app_context():
        msg = Message('MediScribe Reminder',
                      sender=os.environ.get('email', 'noreply@mediscribe.com'),
                      recipients=[mail_id])
        msg.html = mail_body(message)
        mail.send(msg)
        print("Sent")
        return


def send_combined_mail(medicines_list, mail_id, patient_name=""):
    """Send ONE email that lists ALL medicines together."""
    from htmlbody import combined_mail_body
    with app.app_context():
        subject = "MediScribe – Your Prescription Reminder"
        msg = Message(subject,
                      sender=os.environ.get('email', 'noreply@mediscribe.com'),
                      recipients=[mail_id])
        msg.html = combined_mail_body(medicines_list, patient_name)
        mail.send(msg)
        print(f"Combined mail sent to {mail_id}")


@app.route("/", methods = ["GET"])
def home_page():
    return render_template("home.html")

@app.route("/about", methods = ["GET"])
def about():
    return render_template("about.html")

@app.route("/contact", methods = ["GET"])
def contact():
    return render_template("contact.html")

@app.route("/login", methods = ["POST", "GET"])
def login():
    if request.method=="POST":
        data = {}
        data['email'] = request.form['email']
        data['password'] = request.form['password']

        response = requests.post(
            api_url + '/login',
            data
        )
        if response.headers['authentication']=="success":
            session['token'] = response.headers['token']
            session['email'] = data['email']
            print(session['token'])
            return redirect("/dashboard")
        else:
            return redirect("/login?status=invalid")

    else:
        status = request.args.get('status')
        return render_template("login.html", status=status)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = {}
        data['full_name'] = request.form['name']
        data['email'] = request.form['email']
        data['password'] = request.form['password']
        
        response = requests.post(
            api_url + '/signup',
            data
            )
        if response.headers['status']=="exists":
            return redirect("/signup?status=invalid")
        return redirect("/login?status=success")
    else:
        status = request.args.get('status')
        print(status)
        return render_template("signup.html", status=status)
    
@app.route("/scan", methods = ["GET", "POST"])
def scan():
    if request.method =="POST":
        pic = request.files['picture']
        pic_filename = secure_filename(pic.filename)
        pic_name = str(uuid.uuid1()) + "_" + pic_filename
        pic.save(os.path.join(app.config['UPLOAD_FOLDER_SCAN'], pic_name))
        
        data = {'path': os.path.join(app.config['UPLOAD_FOLDER_SCAN'], pic_name)}

        response = requests.post(
            api_url + '/scan',
            data
            ).json()
        
        response = ast.literal_eval(response)
        
        # Check if we have the new improved NLP results
        if 'Medicines' in response:
            # New format from prescription_nlp.py
            medicines_list = []
            for med_info in response['Medicines']:
                med_name = med_info['name']
                dosage_parts = []
                if med_info.get('dosage'):
                    dosage_parts.append(med_info['dosage'])
                if med_info.get('frequency'):
                    dosage_parts.append(med_info['frequency'])
                if med_info.get('duration'):
                    dosage_parts.append(med_info['duration'])
                
                dosage_str = ' '.join(dosage_parts) if dosage_parts else 'As prescribed'
                medicines_list.append((med_name, dosage_str))
            
            # Extract patient name from new format
            patient_info = response.get('PatientInfo', {})
            raw_name = patient_info.get('name', '') if isinstance(patient_info, dict) else ''
            name = extract_patient_name(raw_name)
            
        else:
            # Old format - fallback to previous logic
            full_text = response.get('extracted_text', '')
            
            # Extract patient name
            name = ''
            if 'PatientName' in response:
                raw_name = response['PatientName'][0][0] if response['PatientName'] else ''
                name = extract_patient_name(raw_name)
            elif 'PatientInfo' in response:
                for info in response['PatientInfo']:
                    text = info[0]
                    if not any(char.isdigit() for char in text) and len(text) > 3:
                        name = extract_patient_name(text)
                        if name != "Not Mentioned":
                            break
                if not name or name == "Not Mentioned":
                    name = "Not Mentioned"
            elif 'Name' in response:
                raw_name = response['Name'][0][0] if response['Name'] else ''
                name = extract_patient_name(raw_name)
            else:
                name = "Not Mentioned"

            # Extract medicines with old logic
            medicines_list = []
            medicines = response.get('Medicine', [])
            
            procedures = response.get('Procedure', [])
            for proc in procedures:
                proc_text = proc[0].lower()
                if any(indicator in proc_text for indicator in ['plus', 'kind', 'gargle', 'tab', 'cap', 'syp', 'inj', 'mg', 'ml']):
                    medicines.append(proc)
            
            dosages = response.get('Dosage', []) or []
            strengths = response.get('Strength', []) or []
            frequencies = response.get('Frequency', []) or []
            durations = response.get('Duration', []) or []
            time_expressions = response.get('TIME_EXPRESSION', []) or []
            
            all_dosage_info = dosages + strengths + frequencies + durations + time_expressions
            
            for med in medicines:
                med_name = med[0]
                med_position = med[1][0] if len(med) > 1 else 0
                
                nearby_info = []
                for info in all_dosage_info:
                    info_position = info[1][0] if len(info) > 1 else 0
                    if abs(info_position - med_position) < 100:
                        nearby_info.append(info[0])
                
                dosage_info = ' '.join(nearby_info).strip()
                
                if not dosage_info and full_text:
                    med_index = full_text.lower().find(med_name.lower())
                    if med_index != -1:
                        start = max(0, med_index - 50)
                        end = min(len(full_text), med_index + len(med_name) + 50)
                        context_before = full_text[start:med_index]
                        context_after = full_text[med_index + len(med_name):end]
                        
                        dosage_patterns = [
                            (r'\(\s*(\d+)\s*\)', 1),
                            (r'(\d{2,3})\s*$', 1),
                            (r'-\s*(\d+)', 1),
                            (r'(\d+)\s*(?:mg|mcg|ml|g|units?)\b', 0),
                            (r'^\s*-\s*(\d+)', 1),
                        ]
                        
                        for pattern, group in dosage_patterns:
                            match = re.search(pattern, context_before, re.IGNORECASE)
                            if match:
                                num = match.group(group).strip()
                                if num.isdigit() and 10 <= int(num) <= 999:
                                    dosage_info = num
                                    break
                        
                        if not dosage_info:
                            for pattern, group in dosage_patterns:
                                match = re.search(pattern, context_after, re.IGNORECASE)
                                if match:
                                    num = match.group(group).strip()
                                    if num.isdigit() and 10 <= int(num) <= 999:
                                        dosage_info = num
                                        break
                
                medicines_list.append((med_name, dosage_info if dosage_info else 'As prescribed'))

        email = request.form.get('email', '') or session.get('email', '')

        # Schedule ONE combined reminder email + daily reminders
        email_configured = os.environ.get('email') and os.environ.get('pass')

        if email and medicines_list and email_configured:
            try:
                # Send ONE immediate combined email for all medicines
                scheduler.add_job(
                    send_combined_mail, 'date',
                    [medicines_list, email, name],
                    run_date=datetime.now() + timedelta(seconds=5)
                )

                # Schedule daily combined reminders based on max duration
                max_days = 0
                for _, dosage_info in medicines_list:
                    dm = re.search(r'(\d+)\s*(?:days?|d\b)', dosage_info, re.IGNORECASE)
                    if dm:
                        max_days = max(max_days, int(dm.group(1)))
                    else:
                        nums = [int(n) for n in re.findall(r'\d+', dosage_info) if 3 <= int(n) <= 365]
                        if nums:
                            max_days = max(max_days, max(nums))

                if max_days > 1:
                    scheduler.add_job(
                        send_combined_mail, 'interval',
                        [medicines_list, email, name],
                        days=1,
                        start_date=datetime.now() + timedelta(days=1),
                        end_date=datetime.now() + timedelta(days=max_days)
                    )
                print(f"✅ Combined reminder scheduled for {len(medicines_list)} medicines → {email}")
            except Exception as e:
                print(f"⚠️  Email scheduling error: {e}")
        elif email and medicines_list and not email_configured:
            print("⚠️  Email reminders requested but email not configured.")

        return render_template("scan_result.html",name = name, medicine = medicines_list, output=response, pic = pic_name)
    else:
        return render_template("scan.html")
    
@app.route("/dashboard", methods = ["GET", "POST"])
def dashboard():
    if request.method=="GET":
        url = "http://127.0.0.1:5000/dashboard"
        payload={}
        headers = {
            'Authorization': 'Bearer '+session.get('token', '')
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        if response.status_code==200:
            data = ast.literal_eval(response.text)
            name = data['name']
            prescriptions = data.get('prescriptions', {})
            
            # Get status messages from query params
            upload_status = request.args.get('upload', '')
            delete_status = request.args.get('delete', '')
            
            return render_template("dashboard.html", 
                                 name=name, 
                                 prescriptions=prescriptions,
                                 upload_status=upload_status,
                                 delete_status=delete_status)
        else:
            return redirect("/login?status=invalid")

@app.route("/logout", methods = ["GET"])
def logout():
    # Clear the session
    session.clear()
    return redirect("/login")
        
@app.route("/dashboard/upload", methods = ["GET", "POST"])
def dashboard_upload():
    if request.method=="GET":
        return render_template("scan_at_dashboard.html")
    else:
        try:
            image = request.files['prescription']
            pic_filename = secure_filename(image.filename)
            pic_name = str(uuid.uuid1()) + "_" + pic_filename

            # Save to BOTH temp and prescriptions folders
            temp_path = os.path.join(app.config['UPLOAD_FOLDER_SCAN'], pic_name)
            prescriptions_path = os.path.join(app.config['UPLOAD_FOLDER_prescriptions'], pic_name)
            
            # Save the file
            image.save(temp_path)
            image.seek(0)  # Reset file pointer
            image.save(prescriptions_path)

            # First, save to database
            data_db = {
                'pic_name': pic_name,
                'email': session.get('email', '')
            }
            url_db = "http://127.0.0.1:5000/dashboard/upload_prescription"
            headers = {'Authorization': 'Bearer '+session.get('token', '')}
            
            db_response = requests.post(url_db, data_db, headers=headers)
            print(f"Database save response: {db_response.status_code}")
            
            # Then process with AWS and NLP
            data_scan = {'path': temp_path}
            scan_response = requests.post(api_url + '/scan', data_scan).json()
            scan_response = ast.literal_eval(scan_response)
            
            # Extract results similar to /scan route
            if 'Medicines' in scan_response:
                # New format from prescription_nlp.py
                medicines_list = []
                for med_info in scan_response['Medicines']:
                    med_name = med_info['name']
                    dosage_parts = []
                    if med_info.get('dosage'):
                        dosage_parts.append(med_info['dosage'])
                    if med_info.get('frequency'):
                        dosage_parts.append(med_info['frequency'])
                    if med_info.get('duration'):
                        dosage_parts.append(med_info['duration'])
                    
                    dosage_str = ' '.join(dosage_parts) if dosage_parts else 'As prescribed'
                    medicines_list.append((med_name, dosage_str))
                
                patient_info = scan_response.get('PatientInfo', {})
                raw_name = patient_info.get('name', '') if isinstance(patient_info, dict) else ''
                name = extract_patient_name(raw_name)
            else:
                # Old format fallback
                name = ''
                if 'PatientName' in scan_response:
                    raw_name = scan_response['PatientName'][0][0] if scan_response['PatientName'] else ''
                    name = extract_patient_name(raw_name)
                elif 'PatientInfo' in scan_response:
                    for info in scan_response['PatientInfo']:
                        text = info[0]
                        if not any(char.isdigit() for char in text) and len(text) > 3:
                            name = extract_patient_name(text)
                            if name != "Not Mentioned":
                                break
                    if not name or name == "Not Mentioned":
                        name = "Not Mentioned"
                else:
                    name = "Not Mentioned"
                
                medicines_list = []
                medicines = scan_response.get('Medicine', [])
                for med in medicines:
                    med_name = med[0]
                    medicines_list.append((med_name, 'As prescribed'))
            
            # Schedule combined email reminder using logged-in user's email
            user_email = session.get('email', '')
            email_configured = os.environ.get('email') and os.environ.get('pass')
            if user_email and medicines_list and email_configured:
                try:
                    scheduler.add_job(
                        send_combined_mail, 'date',
                        [medicines_list, user_email, name],
                        run_date=datetime.now() + timedelta(seconds=5)
                    )
                    max_days = 0
                    for _, dosage_info in medicines_list:
                        dm = re.search(r'(\d+)\s*(?:days?|d\b)', dosage_info, re.IGNORECASE)
                        if dm:
                            max_days = max(max_days, int(dm.group(1)))
                        else:
                            nums = [int(n) for n in re.findall(r'\d+', dosage_info) if 3 <= int(n) <= 365]
                            if nums:
                                max_days = max(max_days, max(nums))
                    if max_days > 1:
                        scheduler.add_job(
                            send_combined_mail, 'interval',
                            [medicines_list, user_email, name],
                            days=1,
                            start_date=datetime.now() + timedelta(days=1),
                            end_date=datetime.now() + timedelta(days=max_days)
                        )
                    print(f"✅ Dashboard upload: reminder scheduled → {user_email}")
                except Exception as e:
                    print(f"⚠️ Dashboard email error: {e}")

            # Show results page
            return render_template("scan_result.html", 
                                 name=name, 
                                 medicine=medicines_list, 
                                 output=scan_response, 
                                 pic=pic_name,
                                 from_dashboard=True)
            
        except Exception as e:
            print(f"Upload error: {e}")
            import traceback
            traceback.print_exc()
            return redirect("/dashboard?upload=error")

@app.route("/dashboard/view/<prescription_id>", methods = ["GET"])
def view_prescription(prescription_id):
    try:
        
        # Get all prescriptions from dashboard
        url_dashboard = "http://127.0.0.1:5000/dashboard"
        headers = {
            'Authorization': 'Bearer '+session.get('token', '')
        }
        
        dashboard_response = requests.get(url_dashboard, headers=headers)
        print(f"Dashboard response status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            dashboard_data = ast.literal_eval(dashboard_response.text)
            prescriptions = dashboard_data.get('prescriptions', {})
            
            # Find the prescription - use string ID since that's what the API returns
            print(f"Looking for prescription ID: {prescription_id}")
            print(f"Available prescription IDs: {list(prescriptions.keys())}")
            if prescription_id in prescriptions:
                prescription = prescriptions[prescription_id]
                # prescription_name is a tuple, get first element
                pic_filename = prescription['prescription_name']
                if isinstance(pic_filename, tuple):
                    pic_filename = pic_filename[0]
                
                # Process the prescription to get results
                pic_path = os.path.join(app.config['UPLOAD_FOLDER_prescriptions'], pic_filename)
                print(f"Looking for prescription file at: {pic_path}")
                print(f"File exists: {os.path.exists(pic_path)}")
                
                if os.path.exists(pic_path):
                    # Process with AWS and NLP
                    scan_data = {'path': pic_path}
                    scan_response = requests.post(api_url + '/scan', scan_data).json()
                    scan_response = ast.literal_eval(scan_response)
                    
                    # Extract results
                    if 'Medicines' in scan_response:
                        medicines_list = []
                        for med_info in scan_response['Medicines']:
                            med_name = med_info['name']
                            dosage_parts = []
                            if med_info.get('dosage'):
                                dosage_parts.append(med_info['dosage'])
                            if med_info.get('frequency'):
                                dosage_parts.append(med_info['frequency'])
                            if med_info.get('duration'):
                                dosage_parts.append(med_info['duration'])
                            
                            dosage_str = ' '.join(dosage_parts) if dosage_parts else 'As prescribed'
                            medicines_list.append((med_name, dosage_str))
                        
                        patient_info = scan_response.get('PatientInfo', {})
                        raw_name = patient_info.get('name', '') if isinstance(patient_info, dict) else ''
                        name = extract_patient_name(raw_name)
                    else:
                        # Fallback
                        name = "Not Mentioned"
                        medicines_list = []
                        for med in scan_response.get('Medicine', []):
                            medicines_list.append((med[0], 'As prescribed'))
                    
                    # Show results page
                    return render_template("scan_result.html",
                                         name=name,
                                         medicine=medicines_list,
                                         output=scan_response,
                                         pic=pic_filename,
                                         from_dashboard=True)
        
        print(f"View prescription failed - reached end of function")
        print(f"Dashboard status: {dashboard_response.status_code if 'dashboard_response' in locals() else 'N/A'}")
        print(f"Prescription ID: {prescription_id}")
        return redirect("/dashboard?view=error")
        
    except Exception as e:
        print(f"View error: {e}")
        import traceback
        traceback.print_exc()
        return redirect("/dashboard?view=error")

@app.route("/dashboard/delete/<prescription_id>", methods = ["GET", "POST"])
def delete_prescription(prescription_id):
    try:
        url = "http://127.0.0.1:5000/dashboard/delete"
        headers = {
            'Authorization': 'Bearer '+session.get('token', '')
        }
        data = {'id': prescription_id}
        
        response = requests.post(url, data, headers=headers)
        
        if response.status_code == 200:
            return redirect("/dashboard?delete=success")
        else:
            return redirect("/dashboard?delete=error")
    except Exception as e:
        print(f"Delete error: {e}")
        return redirect("/dashboard?delete=error")

@app.route("/prescription-summary", methods=["POST"])
def prescription_summary():
    """Auto-popup: returns AI summary of scanned prescription using Groq."""
    data = request.get_json()
    medicines = data.get("medicines", [])
    if not medicines:
        return jsonify({"summary": "No medicines found to summarise."})

    try:
        from groq import Groq
        api_key = os.environ.get('GROQ_API_KEY', '')
        if not api_key:
            raise Exception("No API key")

        med_lines = "\n".join(
            f"- {m.get('name','')} ({m.get('dosage','')})"
            for m in medicines if m.get('name')
        )

        prompt = (
            f"The patient has been prescribed the following medicines:\n{med_lines}\n\n"
            "Please provide a helpful summary covering:\n"
            "1. What each medicine is used for (1 line each)\n"
            "2. General food/drink to avoid (e.g. alcohol, dairy, grapefruit)\n"
            "3. Best time to take each medicine (morning/night/with food)\n"
            "4. Any important warnings\n"
            "Keep it concise, friendly and under 200 words. Use plain text, no markdown symbols."
        )

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful medical assistant. Give practical, patient-friendly medicine summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        summary = response.choices[0].message.content
        # Convert newlines to <br> for HTML display
        summary = summary.replace('\n', '<br>')
        return jsonify({"summary": summary})

    except Exception as e:
        print(f"Summary error: {e}")
        # Fallback: build a basic summary from medicine names
        med_names = [m.get('name', '') for m in medicines if m.get('name')]
        summary = (
            f"Your prescription includes: <b>{', '.join(med_names)}</b>.<br><br>"
            "General advice:<br>"
            "• Take medicines at the same time each day<br>"
            "• Take with water unless directed otherwise<br>"
            "• Avoid alcohol while on antibiotics<br>"
            "• Complete the full course even if you feel better<br>"
            "• Consult your doctor if you experience side effects"
        )
        return jsonify({"summary": summary})


@app.route("/agent", methods=["POST"])
def agent():
    data = request.get_json(force=True, silent=True) or {}
    user_message = data.get("message", "").strip()
    medicines    = data.get("medicines", [])
    user_email   = data.get("email", "")

    import re as _re

    # ── Scheduling intent ────────────────────────────────────────────────────
    time_pattern = _re.search(
        r'(?:at|@)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?',
        user_message, _re.IGNORECASE)
    schedule_kw = any(w in user_message.lower() for w in
        ["schedule", "remind", "reminder", "send mail", "send email",
         "email me", "notify", "alert", "set reminder"])

    if (schedule_kw or time_pattern) and medicines:
        target_email = user_email or session.get('email', '')
        if not target_email:
            return jsonify({"reply": "Please enter your email address to schedule reminders."})

        run_dt = None
        if time_pattern:
            hour   = int(time_pattern.group(1))
            minute = int(time_pattern.group(2) or 0)
            ampm   = (time_pattern.group(3) or "").lower()
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            now = datetime.now()
            run_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if run_dt <= now:
                run_dt += timedelta(days=1)

        med_tuples = [(m.get("name",""), m.get("dosage","")) for m in medicines]
        fire_at = run_dt or datetime.now() + timedelta(seconds=5)
        try:
            scheduler.add_job(send_combined_mail, 'date',
                              [med_tuples, target_email, ""], run_date=fire_at)
            time_str = run_dt.strftime("%I:%M %p") if run_dt else "shortly"
            names = ", ".join(m.get("name","") for m in medicines)
            return jsonify({"reply": f"✅ Reminder scheduled for {time_str}! Combined email for: {names} → {target_email}"})
        except Exception as e:
            return jsonify({"reply": f"⚠️ Could not schedule: {e}"})

    # ── Everything else → Groq ───────────────────────────────────────────────
    try:
        from groq import Groq
        api_key = os.environ.get('GROQ_API_KEY', '')
        if not api_key:
            return jsonify({"reply": "AI assistant is not configured. Please check GROQ_API_KEY."})

        med_context = ""
        if medicines:
            lines = "\n".join(f"- {m.get('name','')} ({m.get('dosage','')})"
                              for m in medicines if m.get('name'))
            med_context = f"\n\nPatient's current prescription:\n{lines}"

        system = (
            "You are MediScribe's medical AI assistant. "
            "MediScribe is a prescription management web app that uses AWS Textract for OCR, "
            "AWS Comprehend Medical for NER, and custom NLP to extract medicines from prescriptions. "
            "It sends email reminders and has a dashboard to save prescriptions. "
            "Answer any medical question clearly and helpfully. "
            "For MediScribe usage questions, explain the actual features. "
            "Keep answers under 200 words. Be friendly and practical."
            + med_context
        )

        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user_message}
            ],
            max_tokens=400
        )
        reply = resp.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        print(f"Groq error: {e}")
        return jsonify({"reply": f"Sorry, the AI assistant is temporarily unavailable. Error: {str(e)[:100]}"})


def _call_groq(user_message: str, medicines: list) -> str:
    """Call Groq API (Llama 3) with medical context."""
    try:
        from groq import Groq
        api_key = os.environ.get('GROQ_API_KEY', '')
        if not api_key:
            return None

        med_context = ""
        if medicines:
            med_lines = "\n".join(
                f"- {m.get('name','')} ({m.get('dosage','')})"
                for m in medicines if m.get('name')
            )
            med_context = f"\n\nThe patient's current prescription contains:\n{med_lines}"

        system_prompt = (
            "You are MediScribe's medical AI assistant built into the MediScribe web application. "
            "MediScribe is a smart prescription management system that:\n"
            "- Uses AWS Textract to extract text from prescription images (OCR)\n"
            "- Uses AWS Comprehend Medical to identify medicines, dosages, frequencies\n"
            "- Uses custom NLP post-processing with 7 strategies to improve accuracy\n"
            "- Sends email reminders for medicines based on prescription duration\n"
            "- Allows users to save prescriptions to a dashboard after logging in\n"
            "- Supports scanning prescriptions as a guest or logged-in user\n\n"
            "How to use MediScribe:\n"
            "1. Go to the Scan page\n"
            "2. Upload a clear photo of your prescription\n"
            "3. Enter your email to receive medicine reminders\n"
            "4. Click Submit — medicines, dosages and frequencies are extracted automatically\n"
            "5. The AI assistant (me) will pop up with a summary of your prescription\n"
            "6. You can ask me to schedule reminders at a specific time (e.g. 'remind me at 8am')\n"
            "7. Login to save prescriptions to your Dashboard\n\n"
            "Your role: Help patients understand their prescriptions, medicines, dosages, "
            "food interactions, drug interactions, side effects, and how to use MediScribe. "
            "Be specific, helpful and friendly. Keep responses under 200 words. "
            "When asked about MediScribe, explain the actual features above."
            + med_context
        )

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message}
            ],
            max_tokens=350
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq error: {type(e).__name__}: {e}")
        return None


def agent_reply(message, medicines, user_email,
                get_medicine_summary_fn=None, get_drug_interactions_fn=None):
    """AI agent: scheduling handled locally, everything else goes to Gemini."""
    import re as _re
    msg = message.lower().strip()

    # ── 1. Time-based scheduling (always handled locally) ─────────────────────
    time_pattern = _re.search(
        r'(?:at|@)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', msg, _re.IGNORECASE)
    schedule_kw = any(w in msg for w in
        ["schedule", "remind", "reminder", "send mail", "send email",
         "email me", "notify", "alert", "set reminder", "medicine reminder"])

    if schedule_kw or time_pattern:
        if not user_email:
            return "Please enter your email address in the field above so I can schedule reminders!"

        email_match = _re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
        target_email = email_match.group(0) if email_match else user_email

        if not medicines:
            return "No medicines found. Please scan a prescription first."

        run_dt = None
        if time_pattern:
            hour   = int(time_pattern.group(1))
            minute = int(time_pattern.group(2) or 0)
            ampm   = (time_pattern.group(3) or "").lower()
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            now = datetime.now()
            run_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if run_dt <= now:
                run_dt += timedelta(days=1)

        med_tuples = [(m.get("name", ""), m.get("dosage", "")) for m in medicines]

        try:
            fire_at = run_dt if run_dt else datetime.now() + timedelta(seconds=5)
            scheduler.add_job(
                send_combined_mail, 'date',
                [med_tuples, target_email, ""],
                run_date=fire_at
            )
            max_days = 0
            for _, dosage in med_tuples:
                dm = _re.search(r'(\d+)\s*(?:days?|d\b)', dosage, _re.IGNORECASE)
                if dm:
                    max_days = max(max_days, int(dm.group(1)))
                else:
                    nums = [int(n) for n in _re.findall(r'\d+', dosage) if 3 <= int(n) <= 365]
                    if nums:
                        max_days = max(max_days, max(nums))

            if max_days > 1:
                scheduler.add_job(
                    send_combined_mail, 'interval',
                    [med_tuples, target_email, ""],
                    days=1,
                    start_date=fire_at + timedelta(days=1),
                    end_date=fire_at + timedelta(days=max_days)
                )

            time_str = run_dt.strftime("%I:%M %p") if run_dt else "in a few seconds"
            names = ", ".join(m.get("name", "") for m in medicines)
            return (f"✅ Reminder scheduled for {time_str}! "
                    f"Combined email for: {names} → {target_email}. "
                    f"Daily reminders for {max_days} days.")
        except Exception as e:
            return f"⚠️ Could not schedule: {e}"

    # ── 2. Everything else → Groq (Llama 3) ─────────────────────────────────
    print(f"[AGENT] Calling Groq for: {message[:50]}")
    groq_reply = _call_groq(message, medicines)
    print(f"[AGENT] Groq reply: {groq_reply[:80] if groq_reply else 'None - using fallback'}")
    if groq_reply:
        return groq_reply

    # ── 3. Fallback if Groq fails ─────────────────────────────────────────────
    if any(w in msg for w in ["hello", "hi", "hey", "help"]):
        return ("Hi! I'm your MediScribe assistant powered by Llama 3 AI 👋<br>"
                "Ask me anything — medicine info, side effects, food interactions, "
                "drug interactions, or say 'remind me at 8am' to schedule reminders!")

    return ("I can help with any medical question! Try asking:<br>"
            "• 'What are the side effects of Augmentin?'<br>"
            "• 'What food should I avoid with ibuprofen?'<br>"
            "• 'Are Augmentin and Enzoflam safe together?'<br>"
            "• 'Remind me at 9am' to schedule reminders")


if __name__=="__main__":
    app.run(debug=True, port=8000)