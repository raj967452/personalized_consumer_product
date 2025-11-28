import os
import uuid
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='../frontend/templates')
UPLOAD_FOLDER = 'backend/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/submit_preferences', methods=['POST'])
def submit_preferences():
    # Ensure the upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Check if the scan file is present
    if 'scan' not in request.files:
        return 'No scan found', 400
    scan = request.files['scan']
    if scan.filename == '':
        return 'No selected file', 400

    # Get preferences from the form
    style = request.form.get('style')
    color = request.form.get('color')
    material = request.form.get('material')
    features = request.form.get('features')

    # Save the scan with a unique filename
    if scan:
        filename = f"{uuid.uuid4()}.png"
        scan_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        scan.save(scan_path)
        print(f"Scan saved as: {filename}")
        print(f"Associated Preferences - Style: {style}, Color: {color}, Material: {material}, Features: {features}")
        return "Preferences and scan submitted successfully!", 200

    return 'An error occurred', 500

if __name__ == '__main__':
    app.run(debug=True)
