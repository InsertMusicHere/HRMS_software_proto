import zipfile
from flask import Flask, redirect, render_template, request, session, url_for,flash,jsonify
import pymongo
import urllib
import datetime
import os
from werkzeug.utils import secure_filename
from datetime import timedelta
from bson import json_util
from bson.objectid import ObjectId
from flask import send_file
import csv
from io import StringIO
import pandas as pd
from flask import make_response
from waitress import serve
import pdfkit
from reportlab.pdfgen import canvas
from io import BytesIO
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Flowable
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer,  Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

username_in_mongo = ''
password_in_mongo = ''

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB configuration
# client = MongoClient('mongodb://localhost:27017')
# db = client['your_database_name']
# users_collection = db['users']

client = pymongo.MongoClient("mongodb+srv://"+username_in_mongo+":"+ urllib.parse.quote(password_in_mongo) + "@.frvr4k3.mongodb.net/?retryWrites=true&w=majority")
cluster = "mongodb+srv://"+username_in_mongo+":"+ urllib.parse.quote(password_in_mongo) + "@.frvr4k3.mongodb.net/?retryWrites=true&w=majority"
db = client.get_database('Dbox_database')
users_collection = db['employee_zero']
clock_collection = db['clock']
leave_collection = db['leave']

# Add this index creation code where you initialize your MongoDB connection 
# to create a unique index on employee_id, start_date, and end_date. This will prevent users from applying for leave on the same dates more than once.
db.user_applied_leaves.create_index([('employee_id', 1), ('start_date', 1), ('end_date', 1)], unique=True)


@app.route('/')
def index():

    if 'username' in session:
        username = session['username']
        message = f'Logged in as {username}'
        return render_template('landing_page.html', message=message)
    
    message =  'You are not logged in.'
    return render_template('landing_page.html', message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users_collection.find_one({'Employee_ID': username})

        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('logged_in'))
        else:
            message =  'Invalid username or password'
            return redirect(url_for('oops'))

    return render_template('login.html')

@app.route('/oops')
def oops():
    session.pop('username', None)
    message =  'Invalid username or password'
    return render_template('oops.html', message=message)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' in session:
        username = session['username']
        user = users_collection.find_one({'username': username})

        if request.method == 'POST':
            old_password = request.form['old_password']
            new_password = request.form['new_password']

            if old_password == user['password']:
                users_collection.update_one(
                    {'username': username},
                    {'$set': {'password': new_password}}
                )
                return redirect(url_for('index'))
            else:
                return 'Incorrect old password'

        return render_template('change_password.html', default_password=user['default_password'])

    return redirect(url_for('login'))

@app.route('/clock_in', methods=['POST'])
def clock_in():

    employee_profile = db.employee_zero.find_one({}, {"profile_picture": 1})
    profile_picture = employee_profile.get("profile_picture") if employee_profile else None

    # If no profile picture is found in the database, use the default one
    if not profile_picture:
        profile_picture = 's.jpeg'  # Change to your default profile picture name

    # return render_template('index.html', profile_picture=profile_picture)

    employee_id = str(session['username'])  # Replace with actual employee ID
    timestamp = datetime.datetime.utcnow()

    db.clock.insert_one({
        'employee_id': employee_id,
        'timestamp': timestamp,
        'type': 'clock_in'
    })

    username = session['username']
    username_to_display = username

    clock_in_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    clock_out_time = get_last_clock_time('clock_out')

    return render_template('logged_in.html', clockInTime=clock_in_time, clockOutTime=clock_out_time,email = username_to_display,profile_picture=profile_picture)


@app.route('/clock_out', methods=['POST'])
def clock_out():

    employee_profile = db.employee_zero.find_one({}, {"profile_picture": 1})
    profile_picture = employee_profile.get("profile_picture") if employee_profile else None

    # If no profile picture is found in the database, use the default one
    if not profile_picture:
        profile_picture = 's.jpeg'  # Change to your default profile picture name

    employee_id = str(session['username'])   # Replace with actual employee ID
    timestamp = datetime.datetime.utcnow()
    
    db.clock.insert_one({
        'employee_id': employee_id,
        'timestamp': timestamp,
        'type': 'clock_out'
    })

    username = session['username']
    username_to_display = username

    clock_in_time = get_last_clock_time('clock_in')
    clock_out_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')

    return render_template('logged_in.html', clockInTime=clock_in_time, clockOutTime=clock_out_time,email = username_to_display,profile_picture=profile_picture)

@app.route('/delete_profile_picture', methods=['POST'])
def delete_profile_picture():
    # Get the employee profile from the collection 'employee_zero'
    employee_profile = db.employee_zero.find_one({}, {"profile_picture": 1})
    profile_picture = employee_profile.get("profile_picture") if employee_profile else None

    # If a profile picture exists, delete it
    if profile_picture:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], profile_picture))
            db.employee_zero.update_one({}, {"$unset": {"profile_picture": 1}})
            flash('Profile picture deleted successfully!', 'success')
        except Exception as e:
            flash('An error occurred while deleting the profile picture.', 'error')

    return redirect(url_for('index'))


@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    if 'profile_picture' in request.files:
        profile_picture_file = request.files['profile_picture']

        # Check if the file has a valid filename
        if profile_picture_file.filename == '':
            flash('No selected file.', 'error')
            return redirect(url_for('index'))

        # Check if the file is allowed (you can add more file types if needed)
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
        if not allowed_file(profile_picture_file.filename, allowed_extensions):
            flash('Invalid file type. Allowed extensions are jpg, jpeg, png, and gif.', 'error')
            return redirect(url_for('index'))

        # If a profile picture exists, delete it first
        delete_profile_picture()

        # Save the uploaded file and update the database
        filename = secure_filename(profile_picture_file.filename)
        profile_picture_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        db.employee_zero.update_one({}, {"$set": {"profile_picture": filename}})
        flash('Profile picture uploaded successfully!', 'success')

    return redirect(url_for('index'))

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_last_clock_time(clock_type):
    last_clock = db.clock.find_one({'type': clock_type}, sort=[('timestamp', -1)])
    if last_clock:
        return last_clock['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    return ''


@app.route('/logged_in')
def logged_in():

    employee_profile = db.employee_zero.find_one({}, {"profile_picture": 1})
    profile_picture = employee_profile.get("profile_picture") if employee_profile else None
    
    

    # If no profile picture is found in the database, use the default one
    if not profile_picture:
        profile_picture = 's.jpeg'  # Change to your default profile picture name

    if "username" in session:
        username = session['username']
        email = username
        # Check if the user is an admin based on 'is_admin' key in 'employee_zero' collection
        is_admin = db['employee_zero'].find_one({'Employee_ID': str(email), 'is_admin': 'yes'})
        return render_template('logged_in.html', email=email,profile_picture=profile_picture,is_admin=is_admin)
    else:
        return redirect(url_for("index"))

def generate_csv(data):
    # Convert the data to a pandas DataFrame
    df = pd.DataFrame(data)

    # Remove the "_id" column if present
    df.drop(columns=['_id'], inplace=True, errors='ignore')

    # Convert the 'timestamp' column to datetime format
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True).dt.strftime('%Y-%m-%d %H:%M:%S')

    # Create a StringIO object to hold the CSV data
    output = StringIO()

    # Write the DataFrame to the StringIO object as CSV
    df.to_csv(output, index=False)

    # Reset the StringIO position to the beginning
    output.seek(0)

    # Create a response object with the CSV data
    response = make_response(output.getvalue())

    # Set the Content-Type and Content-Disposition headers
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=attendance_data.csv'

    return response

def generate_csv_leave(data):
    # Convert the data to a pandas DataFrame
    df = pd.DataFrame(data)

    # Remove the "_id" column if present
    df.drop(columns=['_id'], inplace=True, errors='ignore')

    # Convert the 'timestamp' column to datetime format
    # df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True).dt.strftime('%Y-%m-%d %H:%M:%S')

    # Create a StringIO object to hold the CSV data
    output = StringIO()

    # Write the DataFrame to the StringIO object as CSV
    df.to_csv(output, index=False)

    # Reset the StringIO position to the beginning
    output.seek(0)

    # Create a response object with the CSV data
    response = make_response(output.getvalue())

    # Set the Content-Type and Content-Disposition headers
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=attendance_data.csv'

    return response


@app.route('/download_attendance_data', methods=['GET'])
def download_attendance_data():
    if 'username' not in session:
        return redirect('/login')  # Redirect to login page if user is not logged in

    username = session['username']

    # Retrieve attendance data from the "clock" collection for the logged-in user
    data = clock_collection.find({'employee_id': username})
    
    # Convert the data to a list of dictionaries
    attendance_data = list(data)

    # Call the function to generate and return the CSV file
    return generate_csv(attendance_data)

@app.route('/get_attendance')
def calendar():
    if 'username' not in session:
        return redirect('/login')  # Redirect to login page if user is not logged in

    username = session['username']
    employee_data = users_collection.find_one({'Employee_ID': username}, {'weekly_policy': 1})
    weekly_off = employee_data.get('weekly_policy', '') if employee_data else ''
    print("weekly_off",weekly_off)

    return render_template('attendance.html', username=session.get('username'), weekly_off=weekly_off)

@app.route('/get_attendance_data')
def get_attendance_data():
    if 'username' not in session:
        return json_util.dumps({})  # Return empty attendance data if username is not in session

    username = session['username']

    # Retrieve attendance data from MongoDB collection for the logged-in user
    data = clock_collection.find({'employee_id': username})
    attendance_data = {}
    for entry in data:
        # Extract the date from the timestamp and convert it to ISO string
        date_str = entry['timestamp'].strftime('%Y-%m-%d')  # Convert to YYYY-MM-DD format
        attendance_data[date_str] = True

    print("Username:", username)  # Debugging statement
    print("Attendance Data:", attendance_data)  # Debugging statement

    # Convert the dictionary to a JSON string and send it to the frontend
    return json_util.dumps(attendance_data)

def get_reporting_employees(manager_employee_id):

    print(manager_employee_id)
    print(type(manager_employee_id))

    reporting_employees = db.employee_zero.find(
        {'Manager_Email_Employee_Number': manager_employee_id},
        {'Employee_ID': 1}
    )

    return [employee['Employee_ID'] for employee in reporting_employees]


@app.route('/download_leave_data')
def download_leave_data():

    if 'username' not in session:
        return redirect('/login')  # Redirect to login page if user is not logged in

    username = session['username']

    # Retrieve attendance data from the "clock" collection for the logged-in user
    data = leave_collection.find({'Employee_ID': username})
    print(data)
    # Convert the data to a list of dictionaries
    leave_data = list(data)

    # Call the function to generate and return the CSV file
    return generate_csv_leave(leave_data)


@app.route('/leaves')
def leaves():
    if 'username' not in session:
        return redirect('/login')

    username = str(session['username'])
    leave_data = db.leave.find_one({'Employee_ID': username})
    print(leave_data)

    if leave_data:
        casual_leave_balance = leave_data.get('casual_leave', 0)
        emergency_leave_balance = leave_data.get('emergency_leave', 0)
        medical_leave_balance = leave_data.get('medical_leave', 0)
    else:
        casual_leave_balance = 0
        emergency_leave_balance = 0
        medical_leave_balance = 0

    # Fetch the reporting employees' IDs for the current user (the manager)
    reporting_employee_ids = get_reporting_employees(username)
    print('reporting_employee_ids',reporting_employee_ids)

    # Fetch pending leave applications for the reporting employees

    pending_leaves = []
    for reporting_employee_id in reporting_employee_ids:
        leaves = db.user_applied_leaves.find({
            'Employee_Id': str(reporting_employee_id),
            'status': 'pending'
        })
        pending_leaves.extend(leaves)


    print(pending_leaves)

    # Fetch reporting employees for the current user (managers)
    reporting_employees = get_reporting_employees(username)

    # # Filter pending leaves that have 'Manager' as the current user and 'status' as 'pending'
    # relevant_pending_leaves = [
    #     leave for leave in pending_leaves if leave['Manager'] == username
    # ]

    return render_template('leaves.html',
                           casual_leave_balance=casual_leave_balance,
                           emergency_leave_balance=emergency_leave_balance,
                           medical_leave_balance=medical_leave_balance,
                           pending_leaves=pending_leaves,
                           reporting_employees=reporting_employees,email=session['username'])

@app.route('/approve_leave', methods=['POST'])
def approve_leave():
    leave_id = request.form['leave_id']
    db.user_applied_leaves.update_one({'_id': ObjectId(leave_id)}, {'$set': {'status': 'approved'}})
    flash(f"Leave application approved successfully!", 'success')
    return redirect('/leaves')

@app.route('/decline_leave', methods=['POST'])
def decline_leave():
    leave_id = request.form['leave_id']
    leave_data = db.user_applied_leaves.find_one({'_id': ObjectId(leave_id)})

    if leave_data:
        leave_type = leave_data['leave_type']
        leave_days = (datetime.datetime.strptime(leave_data['end_date'], '%Y-%m-%d') -
                      datetime.datetime.strptime(leave_data['start_date'], '%Y-%m-%d')).days + 1

        # Update the leave balance in the 'leave' collection
        db.leave.update_one({'Employee_ID': leave_data['Employee_Id']},
                            {'$inc': {leave_type: leave_days}})

        # Update the leave status to 'rejected'
        db.user_applied_leaves.update_one({'_id': ObjectId(leave_id)},
                                          {'$set': {'status': 'rejected'}})

        flash(f"Leave application declined successfully!", 'success')
    else:
        flash(f"Leave application not found!", 'error')

    return redirect('/leaves')

# ... Your existing code ...
@app.route('/apply_leave', methods=['POST'])
def apply_leave():
    leave_type = request.form.get('leave-type')
    start_date = request.form.get('start-date')
    end_date = request.form.get('end-date')
    half_day = request.form.get('half-day') == 'on'  # Check if the checkbox for half-day is checked

    # Calculate the number of leave days
    start_datetime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    leave_days = (end_datetime - start_datetime).days + 1

    # Check if it's a half-day leave
    if half_day:
        leave_days = 0.5

    # Get the user's existing leave balance for the selected leave type from the 'leave' collection
    user = db.leave.find_one({'Employee_ID': session['username']}, {'_id': 0, leave_type: 1})
    if user:
        leave_balance = user.get(leave_type, 0)
    else:
        # If the user document doesn't exist in 'leave' collection, initialize the leave balance to zero
        leave_balance = 0

    # Check if the user has enough leave balance
    if leave_days > leave_balance:
        flash(f"You don't have enough {leave_type} leave balance to apply for {leave_days} day(s).", 'error')
        return redirect('/leaves')

    # Fetch the manager from 'employee_zero' collection based on the 'Manager_Email_Employee_Number'
    employee_id = str(session['username'])
    employee_data = db.employee_zero.find_one({'Employee_ID': employee_id})
    manager_employee_id = employee_data.get('Manager_Email_Employee_Number', None)

    # Fetch the existing leave applications for the user
    existing_leave_applications = db.user_applied_leaves.find({
        'Employee_Id': employee_id,
        'start_date': {'$lte': end_date},  # Check for overlapping leave applications
        'end_date': {'$gte': start_date}
    })

    # Check if there are any overlapping leave applications
    for application in existing_leave_applications:
        flash(f"You have already applied for {leave_type} on these day(s).", 'error')
        return redirect('/leaves')

    # Prepare the new leave application data
    applied_leave_data = {
        'Employee_Id': employee_id,
        'Manager': manager_employee_id,
        'leave_type': leave_type,
        'start_date': start_date,
        'end_date': end_date,
        'status': 'pending'
    }

    # Attempt to insert the new leave application data
    try:
        db.user_applied_leaves.insert_one(applied_leave_data)

        # Update the leave balance in the 'leave' collection only if validation passes and insertion is successful
        new_leave_balance = leave_balance - leave_days
        db.leave.update_one({'Employee_ID': session['username']}, {'$set': {leave_type: new_leave_balance}}, upsert=True)

        flash(f"Leave applied successfully!", 'success')
        return redirect('/leaves')

    except pymongo.errors.DuplicateKeyError as e:
        if "employee_id" in str(e) and "start_date" in str(e) and "end_date" in str(e):
            flash(f"You have already applied for {leave_type} on these day(s).", 'error')
        else:
            # For other DuplicateKeyErrors not related to user_applied_leaves, re-raise the exception
            raise e

    return redirect('/leaves')



@app.route('/compensation')
def compensation():

    collection = db['compensation']

    # Get the 'Employee_ID' from the session
    employee_id = session['username']

    # Fetch data from the 'compensation' collection for the user in session
    data = list(collection.find({'Employee_ID': str(employee_id)}))

    # Pass the data to the 'compensation.html' template
    return render_template('compensation.html', data=data,email=employee_id)


@app.route('/ctcpro')
def ctc_pro():

    collection = db['compensation']

    # Get the 'Employee_ID' from the session
    employee_id = session['username']

    # Fetch data from the 'compensation' collection for the user in session
    data = list(collection.find({'Employee_ID': str(employee_id)}))

    # Check if the user is an admin based on 'is_admin' key in 'employee_zero' collection
    is_admin = db['employee_zero'].find_one({'Employee_ID': employee_id, 'is_admin': 'yes'})

    # Filter the data to keep only the latest entry based on 'Date when it was changed'
    if data:
        data = [max(data, key=lambda x: x['Date when it was changed'])]
    
    list_c = ['Basic', 'HRA', 'Provident Fund', 'Gratuity', 'Special Allowance', 'Total Cost to Company', 'Total CTC including variable pay']

    # Pass the data to the 'ctcpro.html' template
    return render_template('ctcpro.html', data=data, email=employee_id,list_c = list_c, is_admin=is_admin)


class MongoDBTable(Flowable):
    def __init__(self, data, col_widths, row_height, col_headers, header_color=None, data_color=None):
        super(MongoDBTable, self).__init__()
        self.data = data
        self.col_widths = col_widths
        self.row_height = row_height
        self.col_headers = col_headers
        self.header_color = header_color if header_color is not None else colors.gray
        self.data_color = data_color if data_color is not None else colors.black

    def drawOn(self, canvas, x, y, _sW=0):
        data = [self.col_headers] + self.data

        for i, row in enumerate(data):
            for j, text in enumerate(row):
                # Determine font color based on header or data row
                font_color = colors.white if i == 0 else self.data_color
                
                # Draw cell background
                canvas.setFillColor(self.header_color if i == 0 else colors.white)
                canvas.rect(x + sum(self.col_widths[:j]), y - (i + 1) * self.row_height,
                            self.col_widths[j], self.row_height, fill=True)
                
                # Draw cell text
                canvas.setFillColor(font_color)
                canvas.drawString(x + sum(self.col_widths[:j]) + 2, y - (i + 1) * self.row_height - 15, str(text))


# List of columns to fetch from the 'compensation' collection
list_c = ['Basic', 'HRA', 'Provident Fund', 'Gratuity', 'Special Allowance', 'Total Cost to Company']


@app.route('/create_payslips', methods=['GET', 'POST'])
def create_payslips():
    # Get the 'Employee_ID' from the session
    employee_id = session.get('username')

    # Check if the user is an admin based on 'is_admin' key in 'employee_zero' collection
    is_admin = db['employee_zero'].find_one({'Employee_ID': employee_id, 'is_admin': 'yes'})
    print(is_admin)

    # Initialize the payslip_data variable
    payslip_data = None

    if request.method == 'POST':

        

        if is_admin:
            print('yes---')
            # Get the form data
            company_name = request.form['company_name']
            address = request.form['address']
            employee_id = request.form['employee_id']
            month_year = request.form['month_year']

            print(month_year)

            # Fetch data from the 'compensation' collection for the provided employee ID
            data = db['compensation'].find_one({'Employee_ID': str(employee_id)})
            print(data)

            if data:
                # Generate the PDF data
                pdf_data = generate_payslip_pdf(company_name, address, data, month_year)

                # Save the PDF data in session to display on the page
                session['pdf_data'] = pdf_data

    return render_template('create_payslips.html', is_admin=is_admin, pdf_data=session.get('pdf_data'))


def generate_payslip_pdf(company_name, address, data, month_and_year):
    # Create a BytesIO buffer to store the PDF content
    buffer = BytesIO()

    # Create a SimpleDocTemplate with the buffer and set page size and margins
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    Story = []

    # Create and set the styles for the PDF
    styles = getSampleStyleSheet()

    # Add the company name as a large header
    company_name_paragraph = Paragraph(company_name, styles['Title'])
    company_name_paragraph.alignment = 1  # Center align the company name
    Story.append(company_name_paragraph)

    # Create a paragraph style for the centered address
    address_style = ParagraphStyle('AddressStyle', parent=styles['Normal'])
    address_style.alignment = 1  # Center align the address

    # Add the address using the new style
    address_paragraph = Paragraph(address, address_style)
    Story.append(address_paragraph)

    Story.append(Spacer(1, 20))  # Add a space between header and table
    
    
    # Add the month and year information using a new paragraph style
    month_and_year_style = ParagraphStyle('MonthYearStyle', parent=styles['Normal'])
    month_and_year_style.alignment = 1  # Center align the month and year

    # Add the month and year information using the new style
    month_and_year_paragraph = Paragraph(month_and_year, month_and_year_style)
    Story.append(month_and_year_paragraph)

    Story.append(Spacer(1, 20))  # Add a space between header and table

    # Create the table data with headers and employee data
    table_data = [list_c]  # Add the column headers to the table data
    employee_data = [str(data.get(column, '')) for column in list_c]  # Get the employee data as a list
    table_data.append(employee_data)  # Add the employee data to the table data

    # Transpose the table data
    transposed_table_data = list(map(list, zip(*table_data)))

    # Add new headers "Components" and "Values"
    transposed_table_data.insert(0, ['Components', 'Values'])

    # Set the table style
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header row background color
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Header row text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center align all cells
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold font for header row
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Add padding to header row
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Data row background color
        ('GRID', (0, 0), (-1, -1), 1, colors.black)  # Add grid lines to the table
    ])

    # Create the table and apply the style
    table = Table(transposed_table_data)
    table.setStyle(table_style)

    # Add the table to the Story
    Story.append(table)

    Story.append(Spacer(1, 40))

    # Add the month and year information using a new paragraph style
    notice_style = ParagraphStyle('MonthYearStyle', parent=styles['Normal'])
    notice_style.alignment = 1  # Center align the month and year

    # Add the month and year information using the new style
    month_and_year_paragraph = Paragraph('Note: This is a Computer Generated Slip and does not require signature', notice_style)
    Story.append(month_and_year_paragraph)

      # Add a space between header and table

    # Build the document
    doc.build(Story)

    buffer.seek(0)

    # Convert the BytesIO object to a base64-encoded string
    pdf_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Add a flash message indicating payslip generation
    # flash('Payslip generated successfully!', 'success')

    return pdf_base64
    


@app.route('/download_payslip')
def download_payslip():
    pdf_data = session.get('pdf_data')

    # Ensure the user is an admin and the PDF data is available
    if pdf_data:
        # Send the PDF data as a file for download
        return send_file(BytesIO(base64.b64decode(pdf_data)),
                         as_attachment=True,
                         attachment_filename='payslip.pdf',
                         mimetype='application/pdf')

    return "Payslip data not available for download."


@app.route('/generate_all_payslips', methods=['GET'])
def generate_all_payslips():
    # Get the query parameters from the URL
    company_name = request.args.get('company_name')
    address = request.args.get('address')
    month_year = request.args.get('month_year')

    # Fetch all employee data from the 'compensation' collection
    all_employee_data = db['compensation'].find()

    # Create a list to store the PDF data of all payslips
    all_payslips_pdf_data = []

    # Iterate over each employee data and generate their payslip PDF
    for employee_data in all_employee_data:
        pdf_data = generate_payslip_pdf(company_name, address, employee_data,month_year)
        all_payslips_pdf_data.append((employee_data['Employee_ID'], pdf_data))

    # Create a zip file containing all the individual payslips
    zip_filename = 'all_payslips.zip'
    with zipfile.ZipFile(zip_filename, 'w') as zip_file:
        for employee_id, pdf_data in all_payslips_pdf_data:
            payslip_filename = f'payslip_{employee_id}.pdf'
            zip_file.writestr(payslip_filename, base64.b64decode(pdf_data))

    # Clear the session's 'pdf_data' to avoid conflicts
    session.pop('pdf_data', None)

    # Send the zip file as a response for download
    return send_file(zip_filename, as_attachment=True)

# ... Your existing code ...

mode = 'dev'

if __name__ == '__main__':

    if mode == 'dev':
        app.run(debug=True)
    else:
        serve(app,host='0.0.0.0',port=5000,threads=1)
