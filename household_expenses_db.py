import sqlite3
import os
from pathlib import Path


def create_db_if_not_exist(db_name='household_expenses.db'):

    #Check if db not exists:
    if not Path(db_name).is_file():
        # Check if the db file should be contained in a folder that does not exist
        db_path_list = db_name.split(os.path.sep)
        if len(db_path_list) > 1:
            db_path_directory = db_name.replace(db_path_list[-1], "")
            if not Path(db_path_directory).is_dir():
                Path(db_path_directory).mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_name)
        print("Opened database successfully")
        conn.close()


def create_table_if_not_exists(db_name='household_expenses.db'):

    conn = sqlite3.connect(db_name)
    conn.execute('''CREATE TABLE IF NOT EXISTS EXPENSES
            (ID INT PRIMARY KEY,
            DATE   INT    NOT NULL,
            USER   TEXT    NOT NULL,         
            EXPENSE_TYPE   TEXT    NOT NULL,
            EXPENSE_DESCRIPTION    TEXT    NOT NULL,
            EXPENSE_AMOUNT REAL    NOT NULL);''')
    print("Table created (OR NOT) successfully")
    conn.close()


def insert_in_db(expense_info, db_name='household_expenses.db'):

    conn = sqlite3.connect(db_name)
    print("Opened database successfully")
    conn.execute(f"""
        INSERT INTO EXPENSES (DATE,USER,EXPENSE_TYPE,EXPENSE_DESCRIPTION,EXPENSE_AMOUNT) 
        VALUES ({expense_info["date"]}, '{expense_info["user"]}', '{expense_info["expense_type"]}', '{expense_info["expense_description"]}', {expense_info["expense_amount"]} )
    """)
    conn.commit()
    print("Records created successfully")
    conn.close()


def print_table_content(db_name='household_expenses.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.execute("SELECT * FROM EXPENSES")
    message = ""
    for row in cursor:
        message += f"{row[0]}  {row[1]}  {row[2]}  {row[3]}  {row[4]}  {row[5]}\n" 
    print(message)
    conn.close()
