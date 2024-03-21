import calendar
import time
import gspread
import logging
import pandas as pd
from datetime import date
from oauth2client.service_account import ServiceAccountCredentials

# https://docs.gspread.org/en/latest/user-guide.html#deleting-a-worksheet


def get_sheet(sheet_name, users_to_share=None): 
    """
    Get sheet by name. 
    If the sheet does not exist, creates it and share with users
    """
    try:
        sht = client.open(sheet_name)
    except gspread.exceptions.SpreadsheetNotFound:
        sht = client.create(sheet_name)
        for user in users_to_share:
            sht.share(user, perm_type='user', role='writer')
    
    return sht


def get_worksheet(sheet, worksheet_name):
    """
    Gets worksheet_name from sheet.
    Creates that worksheet if it does not exist and configure it
    """
    try:
        wksht = sheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        wksht = sheet.add_worksheet(worksheet_name, 1000, 80)
        months = [calendar.month_name[i].upper() for i in range(1,13)]
        for i,v in enumerate(months):
            month_cell_column = (i*4) + 1
            wksht.update_cell(1, month_cell_column, v)

            # Add month columns headers
            wksht.update_cell(2, month_cell_column, "DATE")
            wksht.update_cell(2, month_cell_column + 1, "TYPE")
            wksht.update_cell(2, month_cell_column + 2, "DESCRIPTION")
            wksht.update_cell(2, month_cell_column + 3, "AMOUNT")
    # We have a quota of 60 req/min, so we need to batch the write requests
    time.sleep(61)
    return wksht


def insert_in_sheet(sheet, insertion_list):
    """
    Insert list of amounts in worksheet
    Example of amount:
    {
        "date": "20230101",
        "type": "example_type",
        "description": "example_description",
        "amount": 123.45
    }
    """
    
    counter = 0
    for amount in insertion_list:        

        # We have a quota of 60 req/min, so we need to batch the write requests
        if counter >= 10:
            time.sleep(61)
            counter = 0

        # Get the year from date, and then open the correspondant worksheet
        year = amount.get('date')[:4]
        wksht = get_worksheet(sheet, year)
        
        # Get the month from date, in order to write in the correspondant columns
        month = amount.get('date')[4:6]
        month_date_column =  ((int(month) -1) * 4) + 1
        
        # Get the elements of the DATE column of the month in order to get the first empty row
        next_empty_row = len(wksht.col_values(month_date_column)) + 1

        # Fill the empty row with the info:
        wksht.update_cell(next_empty_row, month_date_column, amount.get("date", None))
        wksht.update_cell(next_empty_row, month_date_column + 1, amount.get("type", None))
        wksht.update_cell(next_empty_row, month_date_column + 2, amount.get("description", None))
        wksht.update_cell(next_empty_row, month_date_column + 3, amount.get("amount", None))
        counter += 1








# Connect to Google Sheets
scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name("conf/gdrive_credentials.json", scope)
client = gspread.authorize(credentials)


#TODO: Borrar la sobreescritura de sheet_name y de users_to_share
sheet_name = 'example_sheet_4'
users_to_share = ["fede488@gmail.com"]
# GET SHEET
sht = get_sheet(sheet_name, users_to_share)

# GET WORKSHEET
actual_year = date.today().strftime("%Y")
worksheet_name = "test_0"
wksht = get_worksheet(sht, worksheet_name)

# #BORRAMOS WORKSHEET Y RECREAMOS:
# wksht = sht.worksheet(worksheet_name)
# sht.del_worksheet(wksht)
# wksht = get_worksheet(sht, worksheet_name)

asd = [{"date":"20230101","type":"example_type","description":"example_description","amount":123.45},{"date":"20230102","type":"example_type2","description":"example_description2","amount":123.45},{"date":"20230101","type":"example_type3"}]

import pdb
pdb.set_trace()