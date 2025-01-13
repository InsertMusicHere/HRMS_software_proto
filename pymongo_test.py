import pymongo
import urllib
import pandas


username_in_mongo = 'saumitra27'
password_in_mongo = 'Saumitra@27'
client = pymongo.MongoClient("mongodb+srv://"+username_in_mongo+":"+ urllib.parse.quote(password_in_mongo) + "@dbox.frvr4k3.mongodb.net/?retryWrites=true&w=majority")
cluster = "mongodb+srv://"+username_in_mongo+":"+ urllib.parse.quote(password_in_mongo) + "@dbox.frvr4k3.mongodb.net/?retryWrites=true&w=majority"

def fetch_mongo_csv3():

    client = pymongo.MongoClient(cluster)

    # adding new database to store csv
    new_mong_db = client["Dbox_database"]

    collection = new_mong_db['employee_zero']

    df = pandas.DataFrame(list(collection.find()))

    df = df.astype({"_id": str})

    # Match value and create new DataFrame
    search_value = 'EMP01'
    new_df = df[df['Employee_ID'] == search_value].copy()
    print(df['Employee_ID'][0])

    print(df)
    print(new_df)

fetch_mongo_csv3()
