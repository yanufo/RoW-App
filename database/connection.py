import mysql.connector as mysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )