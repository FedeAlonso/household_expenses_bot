import sqlite3
import os
from pathlib import Path
import logging


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
        logging.info("Opened database successfully")
        conn.close()


def create_table_if_not_exists(db_name='household_expenses.db'):

    conn = sqlite3.connect(db_name)
    conn.execute('''CREATE TABLE IF NOT EXISTS EXPENSES
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            DATE   INT    NOT NULL,
            USER   TEXT    NOT NULL,         
            EXPENSE_TYPE   TEXT    NOT NULL,
            EXPENSE_DESCRIPTION    TEXT    NOT NULL,
            EXPENSE_AMOUNT REAL    NOT NULL);''')
    logging.info("Table created (OR NOT) successfully")
    conn.close()


def insert_in_db(expense_info, db_name='household_expenses.db'):

    conn = sqlite3.connect(db_name)
    logging.info("INSERT: Opened database successfully")
    query = f"""
        INSERT INTO EXPENSES (DATE,USER,EXPENSE_TYPE,EXPENSE_DESCRIPTION,EXPENSE_AMOUNT) 
        VALUES ({expense_info["date"]}, '{expense_info["user"]}', '{expense_info["expense_type"]}', '{expense_info["expense_description"]}', {expense_info["expense_amount"]} )
    """
    logging.info(f"INSERT: Query: {query}")
    conn.execute(query)
    conn.commit()
    logging.info("INSERT: Records created successfully")
    conn.close()


def delete_from_db(expenses_list, db_name='household_expenses.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    wrong_deletions = []
    for expense in expenses_list:
        query = f"DELETE FROM EXPENSES WHERE ID={expense}"
        cursor.execute(query)
        conn.commit()
        affected_rows = cursor.rowcount
        if affected_rows == 0:
            wrong_deletions.append(expense)
    cursor.close()
    conn.close()
    return wrong_deletions



def get_table_content(db_name='household_expenses.db', limit=20):
    conn = sqlite3.connect(db_name)
    query = f"SELECT * FROM EXPENSES ORDER BY ID DESC LIMIT {limit}"
    logging.info(f"GET: Query: {query}")
    cursor = conn.execute(query)
    json_content = {}
    for row in cursor:
        json_content[row[0]] = {
            "date": row[1],
            "user": row[2],
            "expense_type": row[3],
            "expense_description": row[4],
            "expense_amount": row[5]
        }
        logging.info(f"GET: {row[0]}  {row[1]}  {row[2]}  {row[3]}  {row[4]}  {row[5]}")
    conn.close()
    return json_content


# def print_table_content(db_name='household_expenses.db'):
#     conn = sqlite3.connect(db_name)
#     query = "SELECT * FROM EXPENSES"
#     logging.info(f"INSERT: Query: {query}")
#     cursor = conn.execute(query)
#     message = ""
#     for row in cursor:
#         message += f"{row[0]}  {row[1]}  {row[2]}  {row[3]}  {row[4]}  {row[5]}\n" 
#     print(message)
#     conn.close()
