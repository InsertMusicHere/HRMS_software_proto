from flask import Flask, render_template, request, url_for, redirect, session
import pandas
import pymongo
import bcrypt
import urllib
# from authlib.integrations.flask_client import OAuth
# from authlib.integrations.flask_client import token_update
from flask_oauthlib.client import OAuth
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


username_in_mongo = 'saumitra27'
password_in_mongo = 'Saumitra@27'

app = Flask(__name__)

app.secret_key = "testing"
client = pymongo.MongoClient("mongodb+srv://"+username_in_mongo+":"+ urllib.parse.quote(password_in_mongo) + "@dbox.frvr4k3.mongodb.net/?retryWrites=true&w=majority")
cluster = "mongodb+srv://"+username_in_mongo+":"+ urllib.parse.quote(password_in_mongo) + "@dbox.frvr4k3.mongodb.net/?retryWrites=true&w=majority"
db = client.get_database('Dbox_database')
records2 = db.register
records = db.employee_zero
employee_collection = db['employee_zero']


@app.route("/", methods=['post', 'get'])
def index_function():
    global email_var
    message = ''

    if "email" in session:
        return redirect(url_for("logged_in"))
    
    if request.method == "POST":
        user = request.form.get("fullname")
        email_var = request.form.get("email")
        password = request.form.get("password")

        df = pandas.DataFrame(list(records.find()))

        if str(user) in str(df['Employee_ID'].values) and str(email_var) in str(df['Email'].values) :
            if str(password) in str(df['password'].values):
                email = email_var
                return render_template('logged_in.html', email=email)
        
        else:
            message = 'Employee Id, Email and password do not match'
            return render_template('index.html', message=message)
        
    return render_template('index.html')
  

@app.route('/logged_in')
def logged_in():
    if "email" in session:
        print(email)
        # email = email_var
        email = 'email'
        return render_template('logged_in.html', email=email)
    else:
        return redirect(url_for("index_function"))


@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "email" in session:
        session.pop("email", None)
        return render_template("signout.html")
    else:
        return render_template('index.html')
    
attendance_records = [
    {'date': '2023-07-08', 'present': True},
    {'date': '2023-07-07', 'present': False},
    # Add more attendance records here
]

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if request.method == 'POST':
        # Retrieve the date to revoke attendance
        date_to_revoke = request.form['date']
        
        # Find the attendance record for the given date
        for record in attendance_records:
            if record['date'] == date_to_revoke:
                record['present'] = False
                break

    return render_template('attendance.html', attendance_records=attendance_records)

@app.route('/employee_profile')
def fetch_mongo_csv3():

    client = pymongo.MongoClient(cluster)

    # adding new database to store csv
    new_mong_db = client["Dbox_database"]

    collection = new_mong_db['employee_zero']

    df = pandas.DataFrame(list(collection.find()))

    df = df.astype({"_id": str})

    df = df.drop(columns=['_id'])
    html_table = df.to_html(index=False)

    return render_template('employee_profile.html',table=html_table)

#end of code to run it
if __name__ == "__main__":
    app.run(debug=True)