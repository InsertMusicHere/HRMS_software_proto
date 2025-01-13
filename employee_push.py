import csv
import pandas as pd
from pymongo import MongoClient
import urllib

username_in_mongo = 'saumitra27'
password_in_mongo = 'Saumitra@27'

cluster = "mongodb+srv://"+username_in_mongo+":"+ urllib.parse.quote(password_in_mongo) + "@dbox.frvr4k3.mongodb.net/?retryWrites=true&w=majority"

# remeber password should always be a string
def push_csv_mongo(dataframe,collection_name):

    global data_dict
    data_dict = dataframe.to_dict(orient="records")

    # re-initiate connection
    client = MongoClient(cluster)

    # adding new database to store csv
    new_mong_db = client["Dbox_database"]

    # adding a collection
    new_mong_db[collection_name].insert_many(data_dict)

# df = pd.read_csv('C:/Users/Saumitra/Documents/flask_test/employee.csv')

# push_csv_mongo(dataframe = df,collection_name = 'employee_zero')

# remeber password should always be a string
def push_leaves_mongo(dataframe,collection_name):

    global data_dict
    data_dict = dataframe.to_dict(orient="records")

    # re-initiate connection
    client = MongoClient(cluster)

    # adding new database to store csv
    new_mong_db = client["Dbox_database"]

    # adding a collection
    new_mong_db[collection_name].insert_many(data_dict)


df_leaves = pd.read_csv('C:/Users/Saumitra/Documents/flask_test/leave.csv')

# push_leaves_mongo(dataframe = df_leaves,collection_name = 'leave')



# remeber password should always be a string
def push_employee_basic_ctc(dataframe,collection_name):

    global data_dict
    data_dict = dataframe.to_dict(orient="records")

    # re-initiate connection
    client = MongoClient(cluster)

    # adding new database to store csv
    new_mong_db = client["Dbox_database"]

    # adding a collection
    new_mong_db[collection_name].insert_many(data_dict)


df_basicCtc = pd.read_csv('C:/Users/Saumitra/Documents/flask_test/compensation.csv')

push_employee_basic_ctc(dataframe = df_basicCtc,collection_name = 'compensation')