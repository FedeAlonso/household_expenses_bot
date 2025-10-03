# Configuration files

## config.json
Rename the "config_example.json" to "config.json".

### Fields
```json
{
    "output_folder": "_output",
    "log_filename": "household_expenses.log",
    "db_filename": "household_expenses.db",
    "allowed_users": [00001, 00002],
    "texts": {
        "user_not_allowed": "Sorry but you are not allowed to use this bot.\nPlease contact the admin.",
        "main_actions_add_expense": "ADD EXPENSE",
        "main_actions_delete_expense": "DELETE EXPENSE",
        "main_actions_generate_report": "CREATE REPORT",
        "main_type_buttons_text": ["GROCERIES", "HOUSE", "OTHERS"],
        "others_button_text": "OTHERS",
        "cancel_button_text": "CANCEL",
        "yes_button_text": "YES",
        "no_button_text": "NO",
        "restart_text": "In order to restart the process type /start",
        "select_main_action": "What do you want to do?",
        "start_new_expense": "Which type of expense do you want to add",
        "select_expense_to_delete": "Which expense do you want to delete? Write down the ID (multiple selection by separating the values with commas)",
        "no_expenses_to_delete": "The IDs are not numerical.",
        "deletion_result_OK": "The following expenses were deleted successfully: {expenses}.",
        "deletion_result_KO": "There were some errors trying to delte the following expenses: {expenses}", 
        "confirm_expenses_to_delete": "The following expenses are going to be deleted. Are you sure?",
        "receive_expense_type_message": "Expense Type: {expense_type}\nAdd a description (e.g.: store name)",
        "receive_expense_description_message": "Expense Description: {expense_description}.\nAdd the expense amount",
        "receive_expense_amount_message": "Expense Type: {expense_type}\nExpense Description: {expense_description}\nExpense Amount: {expense_amount}\nIs it OK?",
        "insert_result_KO": "ERROR: Something happened when trying to insert the expense in the DATABASE.",
        "receive_finish_gathering_info_message": "The following information has been inserted in the database\n"

    },
    "gdrive": {
        "active": false,
        "credentials_file": "conf/gdrive_credentials.json",
        "sheet_name": "household_expenses_sheet",
        "share_mails": ["mail1@gmail.com", "mail2@gmail.com"]
    }
}
```
- _output_folder_: Folder where all the output files (logs, reports, db...) are going to be generated. It does not need to exist previously
- _log_filename_: Log file name
- _db_filename_: DB file name
- _allowed users_: An array with the Telegram User ID's of the contributors to the household management. If you don't know it, an easy way of obtaining it is by running the bot, and checking the log. You'll find some trace like 
```log
2025-10-03 23:53:02,222 - __main__ - INFO - Not Allowed user: '<your_user>' with username '<your_user_id>' and id '<your_user_id>'
```
- _texts_: Texts used during the flow of the different executions
- _gdrive_: Google Drive configuration. **More info bellow**
- _gdrive -> active_: Set to true if you want to use Google Drive
- _gdrive -> creadentials_file_: Location of the file which contains the Google Drive credentials
- _gdrive -> sheet_name_: Sheet name
- _gdrive -> share_mails_: Google users which will have access to the shared sheet

## gdrive_credentials.json
**_gdrive -> active_ should be set to true**

Rename the "gdrive_credentials_example.json" file to "gdrive_credentials.json".

Here comes the tricky part. We need to create a Service Account in Google Cloud:
1. First, we need to create a project in [Google Cloud](https://console.cloud.google.com/welcome). For example, call it "household_expenses"
2. Go into the project and enable the **Google Drive API** and **Google Sheets API**
3. Create a **Service Account** within the project, giving it the **Owner** role
4. Open the Service Account, go to the **Keys** section, and create a new key in JSON format
5. Voilà

### Fields
```json
{
    "type": "service_account",
    "project_id": "project_id",
    "private_key_id": "private_key_id",
    "private_key": "-----BEGIN PRIVATE KEY-----\nxxxXXXxxx\n-----END PRIVATE KEY-----\n",
    "client_email": "project_id@project_id.iam.gserviceaccount.com",
    "client_id": "1",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/project_id%40project_id.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}
```