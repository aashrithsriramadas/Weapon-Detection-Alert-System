import cv2
from flask import Flask, Response, request, redirect, url_for, render_template
from roboflow import Roboflow
import time
import geocoder
from flask_mail import Mail, Message
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import numpy as np
import email.charset
from unidecode import unidecode

app = Flask(__name__)

# Replace with your Roboflow API key
ROBOFLOW_API_KEY = 'NmAbA1QRNGTcU3m5SNKG'
# Create a Roboflow instance with your API key
rf = Roboflow(api_key=ROBOFLOW_API_KEY)

# Replace with your project and model information
project_name = "weapon-detection-f1lih"
model_version = 1

# Initialize a flag to control webcam streaming
webcam_streaming = False
 
# Initialize the webcam capture object (outside the webcam function)
cap = None
weapons = ["Knife", "Pistol", "grenade",]
# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your email server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'crimedetectionproject@gmail.com'  # Replace with your email address
app.config['MAIL_PASSWORD'] = 'pyrv xlfs zalm syxy'  # Replace with your email password
app.config['MAIL_USE_TLS'] = True

def send_email_notification(frame, object_name,location):
    try:
        # Email configuration
        smtp_server = 'smtp.gmail.com'  # Replace with your email server
        smtp_port = 587
        smtp_username = 'crimedetectionproject@gmail.com'  # Replace with your email address
        smtp_password = 'pyrv xlfs zalm syxy'  # Replace with your email password

        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = 'abhinavmodem@gmail.com,reddyashok399@gmail.com'  # Replace with the recipient's email address

        # Email subject
        msg['Subject'] = 'Weapon Detected Alert'
        location=location
        #location = location.replace('ā', 'a')
        #location=location('ū','u')
        #print(location)
        object_name=object_name
        # Email body
        body1 = "A weapon has been detected in camera:  " 
        body2 = "Object name: " + object_name
        body = body1 + "\n" + body2

# Encode the entire body as UTF-8
        body = body.encode('utf-8')

        body_msg = MIMEText(body, 'plain', 'utf-8')
 # Specify UTF-8 encoding for the email body
        msg.attach(body_msg)


        # Capture a screenshot and attach it
        if capture_screenshot:
            # Convert the frame to JPEG format in memory
            _, screenshot_data = cv2.imencode('.jpg', frame)
            screenshot_bytes = screenshot_data.tobytes()

            # Attach the screenshot directly to the email
            screenshot = MIMEImage(screenshot_bytes, name='screenshot.jpg')
            msg.attach(screenshot)

        # Connect to the SMTP server and send the email
        recipients = ['abhinavmodem@gmail.com', 'reddyashok399@gmail.com']
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, recipients, msg.as_string())
        server.quit()

        return 'Email sent!'
    except Exception as e:
        return f"Error sending email: {str(e)}"
def get_location():
    try:
        # Use geocoder to automatically obtain the location based on IP address
        g = geocoder.ip('me')
        return g.city
    except Exception as e:
        print(f"Error obtaining location: {str(e)}")
        return "Unknown Location"


def draw_annotations(frame, annotations):
    for annotation in annotations:
        x = annotation['x']
        y = annotation['y']
        width = annotation['width']
        height = annotation['height']
        label = annotation['class']
        confidence = annotation['confidence']

        # Calculate the coordinates of the bounding box
        x1 = int(x - width / 2)
        y1 = int(y - height / 2)
        x2 = int(x + width / 2)
        y2 = int(y + height / 2)

        # Draw bounding box
        color = (0, 255, 0)  # Green color
        thickness = 2
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

        # Add label and confidence
        label_text = f"{label}: {confidence:.2f}"
        cv2.putText(frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)


def webcam():
    global cap, capture_screenshot
  # Access the cap and capture_screenshot variables declared outside the function

    while True:
        if webcam_streaming:
            ret, frame = cap.read()

            if not ret:
                break

            # Predict on the webcam frame using the Roboflow model
            response = model.predict(frame, confidence=40, overlap=30)

            # Extract annotations from the prediction response
            annotations = response.json()['predictions']

            # Check if weapon is detected
            weapon_detected = False
            detected_label = ""

            for annotation in annotations:
                label = annotation['class']
                if label in weapons:
                    weapon_detected = True
                    detected_label = label
                    break

            # If weapon is detected, send an email notification
            if weapon_detected:
            # Draw bounding boxes and labels on the frame
                draw_annotations(frame, annotations,)
                capture_screenshot = True  # Set the flag to capture a screenshot  # Reset the flag after sending the email
                print(send_email_notification(frame, detected_label,get_location()))
                capture_screenshot = False
                #return render_template('email_sent.html')
            _, jpeg = cv2.imencode('.jpg', frame)
            frame_bytes = jpeg.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stop_webcam', methods=['POST'])
def stop_webcam():
    global webcam_streaming, cap
    webcam_streaming = False

    # Release the webcam capture object when stopping
    if cap is not None:
        cap.release()

    return redirect(url_for('start_webcam'))


@app.route('/video_feed', methods=['POST', 'GET'])
def video_feed():
    global webcam_streaming, cap, model  # Access global variables

    if request.method == 'POST':
        webcam_streaming = True

        # Initialize the webcam capture object when starting
        cap = cv2.VideoCapture(0)
        cap.set(3, 640)  # Set camera width
        cap.set(4, 480)  # Set camera height

        # Load the model only once when starting
        project = rf.workspace().project(project_name)
        model = project.version(model_version).model    
    return Response(webcam(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(debug=True)
