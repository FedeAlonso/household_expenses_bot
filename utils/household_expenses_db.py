import sqlite3
import os
from pathlib import Path
import logging


def create_db_if_not_exist(db_name='household_expenses.db'):
    """
    Create Household Expenses database

    :param str db_name: path of the database file
    """
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
    """
    Create Expenses table

    :param str db_name: path of the database file
    """
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
    """
    Insert in table expenses

    :param dict expense_info: Dictionary with the expense info
    :param str db_name: path of the database file
    :return: Row ID of the new row, or -1 if something went wrong
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    logging.info("INSERT: Opened database successfully")
    query = f"""
        INSERT INTO EXPENSES (DATE,USER,EXPENSE_TYPE,EXPENSE_DESCRIPTION,EXPENSE_AMOUNT) 
        VALUES ({expense_info["date"]}, '{expense_info["user"]}', '{expense_info["expense_type"]}', '{expense_info["expense_description"]}', {expense_info["expense_amount"]} )
    """
    logging.info(f"INSERT: Query: {query}")
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()
    
    # Verify Insertion
    if cursor.rowcount <= 0:
        logging.warn(f"INSERT: ERROR. rowcount: {cursor.rowcount}")
        return -1
    logging.info(f"INSERT: Successfully. ROW ID: {cursor.lastrowid}")
    return cursor.lastrowid



def delete_from_db(expenses_list, db_name='household_expenses.db'):
    """
    Delete one or more rows from the table EXPENSES

    :param list expenses_list: List with the IDs of the rows to delete
    :param str db_name: path of the database file
    :return: List with the IDs that have not been deleted
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    wrong_deletions = []
    for expense in expenses_list:
        query = f"DELETE FROM EXPENSES WHERE ID={expense}"
        cursor.execute(query)
        conn.commit()
        if cursor.rowcount <= 0:
            wrong_deletions.append(expense)
            logging.warn(f"DELETE: Expense {expense} not deleted")
        else:
            logging.info(f"DELETE: Expense {expense} deleted")
    cursor.close()
    conn.close()
    return wrong_deletions



def get_table_content(db_name='household_expenses.db', limit=20):
    """
    Get the last <limit> rows of the table EXPENSES

    :param str db_name: path of the database file
    :param int limit: Number of rows to retrieve
    :return: Dict of dicts with the info of those rows
    """
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
