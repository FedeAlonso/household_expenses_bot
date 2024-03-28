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



def insert_in_sheet(expense, gdrive_info):
    """
    Insert expense in worksheet
    Example of expense:
    {
        "id": 5,
        "date": "20230101",
        "expense_type": "example_type",
        "expense_description": "example_description",
        "expense_amount": 123.45
    }
    """
    
    # Get sheet
    sht = get_sheet(gdrive_info.get("sheet_name"), gdrive_info.get("share_mails"))
    # Get the year from date, and then open the correspondant worksheet
    year = expense.get('date')[:4]
    wksht = get_worksheet(sht, year)
    
    # Get the month from date, in order to write in the appropiate columns
    month = expense.get('date')[4:6]
    month_date_column =  ((int(month) -1) * 5) + 1
    
    # Get the elements of the DATE column of the month in order to get the first empty row
    next_empty_row = len(wksht.col_values(month_date_column)) + 1

    # Fill the empty row with the info:
    update_values(wksht, next_empty_row, month_date_column, [expense.get("id", None),
                                                                int(expense.get("date", 0)),
                                                                expense.get("expense_type", None),
                                                                expense.get("expense_description", None),
                                                                expense.get("expense_amount", None)])


def delete_from_sheet(expenses_list, gdrive_info, year=None):
    """
    Delete an expense given its ID
    """

    # Get sheet and worksheet
    sht = get_sheet(gdrive_info.get("sheet_name"), gdrive_info.get("users_name"))
    # The worksheet name is the year
    if year is None:  year=date.today().strftime("%Y")
    wksht = get_worksheet(sht, year)

    # Get the ID columns
    id_columns = []
    for i,v in enumerate( wksht.row_values(2)):
        if v == "ID": id_columns.append(i+1)

    for expense_id in expenses_list:
        # Search the ID in the ID rows
        value_found = False
        value = []
        for id_column in id_columns[::-1]:
            for i,v in enumerate( wksht.col_values(id_column)):
                # print(f"COUNT: {count}  -  ID COLUMN: {id_column}  -  VALUE: {v}")
                # count += 1
                if v == str(expense_id):
                    value_found = True
                    value = [id_column-1, i+1]
                    break
            if value_found: 
                # Clear the cells
                a1_range_orig = f"{xl_col_to_name(value[0])}{value[1]}"
                a1_range_dest = f"{xl_col_to_name(value[0]+4)}{value[1]}"
                wksht.update(range_name=f'{a1_range_orig}:{a1_range_dest}', values=[['', '', '', '', '']])
                break
    
    #TODO: Recuperar esto, seria interesante poder devolver true y false tanto aqui como en el insert y anadir info al mensaje para el usuario
    #     if not value_found: return False

    #     # Clear the cells
    #     if value_found:
    #         a1_range_orig = f"{xl_col_to_name(value[0])}{value[1]}"
    #         a1_range_dest = f"{xl_col_to_name(value[0]+4)}{value[1]}"
    #         wksht.update(range_name=f'{a1_range_orig}:{a1_range_dest}', values=[['', '', '', '', '']])
    
    # return True
            


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
        # Sleep in order to avoid quota issues
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


# #TODO: Borrar la sobreescritura de sheet_name y de users_to_share
# sheet_name = 'example_sheet_5'
# users_to_share = ["fede488@gmail.com"]
# # GET SHEET
# sht = get_sheet(sheet_name, users_to_share)

# # # GET WORKSHEET
# # actual_year = date.today().strftime("%Y")
# # worksheet_name = "test_0"
# # wksht = get_worksheet(sht, worksheet_name)

# # # #BORRAMOS WORKSHEET Y RECREAMOS:
# # # wksht = sht.worksheet(worksheet_name)
# # # sht.del_worksheet(wksht)
# # # wksht = get_worksheet(sht, worksheet_name)

asd = [{"id": 5, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 6, "date":"20230102","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 7, "date":"20230101","type":"example_type3"},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
    #    {"id": 17, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
    #    {"id": 8, "date":"20230101","type":"example_type","description":"example_description","amount":123.45},
    #    {"id": 9, "date":"20230202","type":"example_type2","description":"example_description2","amount":123.45},
    #    {"id": 10, "date":"20230201","type":"example_type3","description":"example_description","amount":123.45},
    #    {"id": 11, "date":"20230302","type":"example_type4","description":"example_description2","amount":123.45},
    #    {"id": 12, "date":"20230301","type":"example_type5","description":"example_description","amount":123.45},
    #    {"id": 13, "date":"20230302","type":"example_type6","description":"example_description2","amount":123.1},
    #    {"id": 14, "date":"20230301","type":"example_type7","description":"example_description","amount":123.45},
    #    {"id": 15, "date":"20230402","type":"example_type8","description":"example_description2","amount":123.45},
    #    {"id": 16, "date":"20230401","type":"example_type9","description":"example_description","amount":123.45},
       {"id": 78, "date":"20230402","type":"example_type9","description":"example_description2","amount":11.45},
       {"id": 77, "date":"20230402","type":"example_type9","description":"example_description3","amount":131.45}]

# insert_in_sheet(sht, asd)
# example_sheet_5

gdrive= {
        "active": True,
        "credentials_file": "conf/gdrive_credentials.json",
        "sheet_name": "household_expenses_test_2",
        "share_mails": ["fede488@gmail.com", "celia.moya88@gmail.com"],
        "write_request_quota": 60
    }
for elem in asd:
    insert_in_sheet(elem, gdrive)


# worksheet_name = "2023"
# wksht = get_worksheet(sht, worksheet_name)
# delete_from_sheet(77, wksht)
delete_from_sheet([77], gdrive, "2023")

# import pdb
# pdb.set_trace()