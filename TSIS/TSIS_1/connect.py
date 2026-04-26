# connect.py
import psycopg2
from config import (
    PHONEBOOK_DATABASE,
    PHONEBOOK_USER,
    PHONEBOOK_PASSWORD,
    PHONEBOOK_HOST,
    PHONEBOOK_PORT,
)


def open_db_session():
    return psycopg2.connect(
        host=PHONEBOOK_HOST,
        port=PHONEBOOK_PORT,
        dbname=PHONEBOOK_DATABASE,
        user=PHONEBOOK_USER,
        password=PHONEBOOK_PASSWORD,
    )
