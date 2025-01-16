from flask import Flask, jsonify, render_template, request, redirect, url_for, session
app=Flask (__name__,static_folder='static')
import pyodbc
import random
import string
from io import BytesIO
from captcha.image import ImageCaptcha
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management
# Database connection
def get_db_connection():
   try:
       conn = pyodbc.connect(
           "Driver={ODBC Driver 17 for SQL Server};"
           "Server=localdb;"  # Replace with your server name or IP address
           "Database=CourtCases;"  # Replace with your database name
           "Trusted_Connection=yes;"  # Use "yes" if you're using Windows Authentication
       )
       return conn
   except Exception as e:
       print(f"Error connecting to the database: {e}")
       return None
# Serve the registration page
@app.route('/')
def register_page():
   return render_template('register.html')
# Generate and send OTP
@app.route('/send-otp', methods=['POST'])
def send_otp():
   data = request.get_json()
   phone = data.get('phone')
   if not phone:
       return jsonify({"success": False, "message": "Phone number is required."})
   # Generate a random 6-digit OTP
   otp = ''.join(random.choices(string.digits, k=6))
   session['otp'] = otp  # Store OTP in session for verification
   # Simulate sending OTP (Replace with SMS gateway integration)
   print(f"OTP sent to {phone}: {otp}")
   return jsonify({"success": True, "message": "OTP sent successfully!"})
# Generate CAPTCHA
@app.route('/generate-captcha')
def generate_captcha():
   image = ImageCaptcha()
   captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
   session['captcha'] = captcha_text  # Store CAPTCHA in session for verification
   data = image.generate(captcha_text)
   return BytesIO(data.read()).getvalue(), 200, {'Content-Type': 'image/png'}
# Registration endpoint
@app.route('/register', methods=['POST'])
def register():
   name = request.form.get('name')
   email = request.form.get('email')
   password = request.form.get('password')
   phone = request.form.get('phone')
   otp = request.form.get('otp')
   captcha = request.form.get('captcha')
   # Verify OTP
   if otp != session.get('otp'):
       return "Invalid OTP. Please try again.", 400
   # Verify CAPTCHA
   if captcha != session.get('captcha'):
       return "Invalid CAPTCHA. Please try again.", 400
   conn = get_db_connection()
   if conn:
       cursor = conn.cursor()
       # Insert the new user into the Users table
       try:
           cursor.execute(
               "INSERT INTO Users (name, email, password, phone) VALUES (?, ?, ?, ?)",
               (name, email, password, phone)
           )
           conn.commit()
       except Exception as e:
           conn.close()
           return f"Error registering user: {e}", 500
       conn.close()
       return redirect(url_for('index'))
   else:
       return "Database connection failed", 500
# Serve the main page
@app.route('/main')
def index():
   return render_template('index.html')
# API to fetch all cases
@app.route('/cases', methods=['GET'])
def get_cases():
   conn = get_db_connection()
   if conn:
       cursor = conn.cursor()
       try:
           cursor.execute("SELECT id, case_number, petitioner_name, respondent_name, status FROM Cases")
           cases = [
               {"id": row[0], "case_number": row[1], "petitioner_name": row[2], "respondent_name": row[3], "status": row[4]}
               for row in cursor.fetchall()
           ]
           conn.close()
           return jsonify(cases)
       except Exception as e:
           conn.close()
           return jsonify({"error": f"Error fetching cases: {e}"}), 500
   else:
       return jsonify({"error": "Database connection failed"}), 500
# API to fetch a specific case by case number
@app.route('/cases/<case_number>', methods=['GET'])
def get_case_by_number(case_number):
   conn = get_db_connection()
   if conn:
       cursor = conn.cursor()
       try:
           cursor.execute(
               "SELECT id, case_number, petitioner_name, respondent_name, status FROM Cases WHERE case_number = ?",
               (case_number,)
           )
           row = cursor.fetchone()
           conn.close()
           if row:
               case = {
                   "id": row[0],
                   "case_number": row[1],
                   "petitioner_name": row[2],
                   "respondent_name": row[3],
                   "status": row[4]
               }
               return jsonify(case)
           else:
               return jsonify({"error": "Case not found"}), 404
       except Exception as e:
           conn.close()
           return jsonify({"error": f"Error fetching case: {e}"}), 500
   else:
       return jsonify({"error": "Database connection failed"}), 500
if __name__ == '__main__':
   app.run(debug=True)


