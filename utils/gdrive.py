import calendar
import time
import gspread
import logging
import pandas as pd
from datetime import date
from xlsxwriter.utility import xl_col_to_name
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
            month_cell_column = (i*5) + 1
            update_cell(wksht, 1, month_cell_column, v)

            # Add month columns headers
            update_values(wksht, 2, month_cell_column, ["ID", "DATE", "TYPE", "DESCRIPTION", "AMOUNT"])
            # update_cell(wksht, 2, month_cell_column, "ID")
            # update_cell(wksht, 2, month_cell_column + 1, "DATE")
            # update_cell(wksht, 2, month_cell_column + 2, "TYPE")
            # update_cell(wksht, 2, month_cell_column + 3, "DESCRIPTION")
            # update_cell(wksht, 2, month_cell_column + 4, "AMOUNT")

    # We have a quota of 60 req/min, so we need to batch the write requests
    # time.sleep(61)
    return wksht


def insert_in_sheet(sheet, insertion_list):
    """
    Insert list of amounts in worksheet
    Example of amount:
    {
        "id": 5,
        "date": "20230101",
        "type": "example_type",
        "description": "example_description",
        "amount": 123.45
    }
    """
    
    for i, amount in enumerate(insertion_list):
        print(i)

        # Get the year from date, and then open the correspondant worksheet
        year = amount.get('date')[:4]
        wksht = get_worksheet(sheet, year)
        
        # Get the month from date, in order to write in the correspondant columns
        month = amount.get('date')[4:6]
        month_date_column =  ((int(month) -1) * 5) + 1
        
        # Get the elements of the DATE column of the month in order to get the first empty row
        next_empty_row = len(wksht.col_values(month_date_column)) + 1

        # Fill the empty row with the info:
        update_values(wksht, next_empty_row, month_date_column, [amount.get("id", None),
                                                                 int(amount.get("date", 0)),
                                                                 amount.get("type", None),
                                                                 amount.get("description", None),
                                                                 amount.get("amount", None)])
        # update_cell(wksht, next_empty_row, month_date_column, amount.get("id", None))
        # update_cell(wksht, next_empty_row, month_date_column + 1, amount.get("date", None))
        # update_cell(wksht, next_empty_row, month_date_column + 2, amount.get("type", None))
        # update_cell(wksht, next_empty_row, month_date_column + 3, amount.get("description", None))
        # update_cell(wksht, next_empty_row, month_date_column + 4, amount.get("amount", None))



def update_cell(wksht, row, column, value=None):
    """
    Update a cell trying to not get the quota 429 error (60 req/min by default)
    """
    try:
        wksht.update_cell(row, column, value)
        time.sleep(2)
    except Exception:
        print("GDRIVE: Quota error detected. Sleeping a few seconds")
        time.sleep(10)
        wksht.update_cell(row, column, value)


def update_values(wksht, row, column, new_values=[]):
    """
    Update a cell trying to not get the quota 429 error (60 req/min by default)
    """
    # Convert to A1 notation
    a1_column_1 = xl_col_to_name(column-1)
    a1_column_2 = xl_col_to_name(column+3)
    a1_range = f"{a1_column_1}{row}:{a1_column_2}{row}"
    try:
        wksht.update(range_name=a1_range, values=[new_values])
        time.sleep(1.5)
    except Exception:
        print("GDRIVE: Quota error detected. Sleeping a few seconds")
        time.sleep(10)
        wksht.update(range_name=a1_range, values=[new_values])




# Connect to Google Sheets
scope = ['https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name("conf/gdrive_credentials.json", scope)
client = gspread.authorize(credentials)


#TODO: Borrar la sobreescritura de sheet_name y de users_to_share
sheet_name = 'example_sheet_5'
users_to_share = ["fede488@gmail.com"]
# GET SHEET
sht = get_sheet(sheet_name, users_to_share)

# # GET WORKSHEET
# actual_year = date.today().strftime("%Y")
# worksheet_name = "test_0"
# wksht = get_worksheet(sht, worksheet_name)

# # #BORRAMOS WORKSHEET Y RECREAMOS:
# # wksht = sht.worksheet(worksheet_name)
# # sht.del_worksheet(wksht)
# # wksht = get_worksheet(sht, worksheet_name)

asd = [{"id": 5, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 6, "date":"20230102","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 7, "date":"20230101","type":"example_type3"},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
       {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
       {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
       {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
       {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
       {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
       {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
       {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
       {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45}]

insert_in_sheet(sht, asd)

# import pdb
# pdb.set_trace()