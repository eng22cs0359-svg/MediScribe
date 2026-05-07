from flask import Flask, jsonify, request, abort, make_response
from flask_restful import Api, Resource
import json
import os
import bcrypt
# from flask_security import auth_required, logout_user, current_user
from functools import wraps

from models import *

from werkzeug.utils import secure_filename
import uuid as uuid

from htmlbody import *

from apscheduler.schedulers.background import BackgroundScheduler
import base64

from ml_model.ner import InitiateNER
from ml_model.ml_model import detect_text

# Import configuration
try:
    from config import *
except ImportError:
    # Fallback to environment variables if config.py doesn't exist
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'super-secret')
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.sqlite"
    UPLOAD_FOLDER_PFP = "images/pfp"
    UPLOAD_FOLDER_PRESCRIPTIONS = "images/prescriptions"

import jwt
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_jwt_extended import set_access_cookies
from flask_jwt_extended import unset_jwt_cookies
import datetime


curr_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

scheduler.start()

app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=30)

jwt = JWTManager(app)

api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI

upload_folder_pfp = UPLOAD_FOLDER_PFP
app.config["UPLOAD_FOLDER_PFP"] = upload_folder_pfp

upload_folder_prescriptions = UPLOAD_FOLDER_PRESCRIPTIONS
app.config["UPLOAD_FOLDER_prescriptions"] = upload_folder_prescriptions

db.init_app(app)
app.app_context().push()

salt = bcrypt.gensalt()


######################
from flask_mail import Mail, Message

app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = 'xyz@gmail.com',
    MAIL_PASSWORD = '',
))

mail= Mail(app)

def send_mail(message, mail_id):
    with app.app_context():
        msg = Message('Hello', sender = 'xyz@gmail.com', recipients = [mail_id])
        # mail.send(msg)
        msg.html = mail_body(message)
        mail.send(msg)
        print("Sent")
        return

def encoding_image(path):
    with open(path, mode='rb') as file:
        img = file.read()
    return base64.b64encode(img).decode('utf-8')


class SignUp(Resource):
    def post(self):
        fname = request.form['full_name']
        email = request.form['email']
        pwd = request.form['password']
        isEmpty = App_user.query.filter_by(email = email).first()
        if isEmpty:
            return make_response("Invalid Email", 401, {'status': "exists"})

        pwd = bytes(pwd, 'utf-8')
        pwd = bcrypt.hashpw(pwd, salt)
        q = App_user(email = email, full_name = fname, password = pwd, profile_pic = "default_pic.png")
        db.session.add(q)
        db.session.commit()
        return make_response("User Successfully Registered",200, {'status' : "success"})
    

class Login(Resource):
    def post(self):
        email = request.form['email']
        pwd = request.form['password'].encode('utf-8')
        find_user = App_user.query.filter_by(email = email).first()
        if find_user:
            user_pass = find_user.password
            if bcrypt.checkpw(pwd, user_pass):
                # token = jwt.encode({'user': str(find_user.email, 'UTF-8'), 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
                token = create_access_token(identity=find_user.email)
                response = jsonify({"msg": "login successful"})
                set_access_cookies(response, token)
                print(token)
                return make_response("success", 200, {'authentication': "success", 'token': token})
            else:
                return make_response("Invalid Credentials", 401, {'authentication': "login required", 'token':''})
        else:
            return make_response("Invalid Credentials", 401, {'authentication': "login required", 'token':''})

class PrescriptionUpload(Resource):
    @jwt_required()
    def post(self):
        try:
            email = request.form['email']
            pic_name = request.form['pic_name']
            
            # Ensure email is string, not bytes
            if isinstance(email, bytes):
                email = email.decode('utf-8')
            
            print(f"PrescriptionUpload - Email: {email}, Pic: {pic_name}")

            q = Prescription(prescription_name = pic_name, user_email = email)
            db.session.add(q)
            db.session.commit()
            
            print(f"Prescription saved to database with ID: {q.id}")
            
            # Return success without processing (already processed in frontend)
            return make_response(jsonify({"status": "success", "id": q.id}), 200)

        except Exception as e:
            print(f"PrescriptionUpload error: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)

class Dashboard(Resource):
    @jwt_required()
    def get(self):
        try:
            email = get_jwt_identity()
            
            # Ensure email is string for database query
            if isinstance(email, bytes):
                email = email.decode("utf-8")
            
            print(f"Dashboard - Looking up user: {email}")
            user = App_user.query.filter_by(email = email).first()
            
            if not user:
                print(f"User not found: {email}")
                return make_response("User not found", 404)
            
            uname = user.email
            
            # Get prescriptions
            presciptions = Prescription.query.filter_by(user_email = uname).all()
            print(f"Found {len(presciptions)} prescriptions")
            
            presciptions_dict = {}
            for i in presciptions:
                temp = {}
                temp["id"] = i.id
                temp["prescription_name"] = i.prescription_name
                temp["date"] = i.time_stamp.strftime('%m/%d/%Y')
                
                image_path = "./images/prescriptions/"+i.prescription_name
                print(f"Encoding image: {image_path}")
                
                try:
                    temp["image"] = encoding_image(image_path)
                except Exception as e:
                    print(f"Error encoding image {image_path}: {e}")
                    temp["image"] = ""
                
                presciptions_dict[i.id] = temp
            
            print(f"Returning {len(presciptions_dict)} prescriptions")
            return jsonify({
                "name": user.full_name, 
                "pfp": user.profile_pic, 
                "number_of_prescription": len(presciptions_dict), 
                "prescriptions": presciptions_dict
            })
            
        except Exception as e:
            print(f"Dashboard error: {e}")
            import traceback
            traceback.print_exc()
            return make_response(str(e), 500)

class ViewPrescription(Resource):
    @jwt_required()
    def post(self):
        curr_id = request.form["id"]
        find_prescription = Prescription.query.filter_by(id = curr_id).first()
        if not find_prescription:
            abort(401)
        return make_response(jsonify({"picture":encoding_image("./images/prescriptions/"+find_prescription.prescription_name)}), 200)
        
class DeletePrescription(Resource):
    @jwt_required()
    def post(self):
        curr_id = request.form["id"]    
        x = Prescription.query.filter_by(id = curr_id).first()
        if not x:
            abort(401)
        db.session.delete(x)
        db.session.commit()
        return make_response(jsonify({'msg': "Successfully signed in!!!"}), 200)
    

class Logout(Resource): #done
    @jwt_required()
    def delete(self):
        response = jsonify({"msg": "logout successful"})
        unset_jwt_cookies(response)
        print(response)
        return response
        # logout_user()
        # return make_response(jsonify({'msg': "Successfully logged out!!!"}), 200)


class SendMail(Resource):
    def get(self):
        message = "hi"
        mail_id = "xyz@gmail.com"
        
        with app.app_context():
            job = scheduler.add_job(send_mail,'interval', ["hi", "xyz@gmail.com"], seconds=10)
        return

class Scan(Resource):
    def post(self):
        file_path = request.form['path']
        
        # Extract text from image using AWS Textract
        extracted_text = detect_text(file_path, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        
        # Extract entities using AWS Comprehend Medical
        aws_results = ner_model.predict(extracted_text)
        
        # Post-process with advanced NLP for better accuracy
        from ml_model.prescription_nlp import PrescriptionNLP
        nlp_processor = PrescriptionNLP()
        improved_results = nlp_processor.process(aws_results, extracted_text)
        
        # Add the full extracted text to the response
        improved_results['extracted_text'] = extracted_text
        
        # Also include raw AWS results for comparison
        improved_results['aws_raw'] = aws_results

        return json.dumps(improved_results)

class Schedule(Resource):
    def post(self):
        pass


api.add_resource(Login, "/login")
api.add_resource(SignUp, "/signup")
api.add_resource(PrescriptionUpload, "/dashboard/upload_prescription")
api.add_resource(Dashboard, "/dashboard")
api.add_resource(ViewPrescription, "/dashboard/view")
api.add_resource(DeletePrescription, "/dashboard/delete")
api.add_resource(Logout, "/logout")
api.add_resource(SendMail, "/api/mail")
api.add_resource(Scan, "/scan")
api.add_resource(Schedule, "/schedule")

if __name__=="__main__":
    db.create_all()
    
    # Initialize NER model with AWS Comprehend Medical
    print("Initializing AWS Comprehend Medical NER...")
    ner_model = InitiateNER(
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    ner_model.load_model()  # For compatibility (does nothing for AWS)
    print("NER model ready!")
    
    app.run(debug=True)