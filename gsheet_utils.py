from __future__ import print_function
import os.path
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def data_to_write():
    # Dummy data for a new order entry
    new_entry = [
        "ORD12345",     # Order ID
        "CUST67890",    # Customer ID
        "2024-02-21",   # Order Date
        "Pending",      # Status
        "example.pdf",  # File
        "example.png",  # Signature
        "2024-02-21",   # Timestamp
        "This is a note"  # Note
    ]
    return [new_entry]

def clear_sheet(service, spreadsheet_id, range_name):
    """Clears the specified range in a Google Sheet."""
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        body={}
    ).execute()

def write_dataframe_to_sheet(dataframe, spreadsheet_id, range_name, credentials):
    """Writes a DataFrame to a Google Sheet."""
    try:
        service = build('sheets', 'v4', credentials=credentials)
        
        # Clear existing data in the sheet
        clear_sheet(service, spreadsheet_id, range_name)
        
        # Convert DataFrame to list of lists
        values = [dataframe.columns.tolist()] + dataframe.values.tolist()
        
        # Call the Sheets API to update the values
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": values}
        ).execute()

        print("Data written successfully!")
        print(result)
    except HttpError as err:
        print(err)

def write_data_to_supply_sheet(sheet_name, data):
    """Writes data to the supply sheet."""
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # The ID and range of the sample spreadsheet.
    SAMPLE_SPREADSHEET_ID = '1_ndw8fGpmkJSPuV3damUE8FePXLySymcxuyTGKLdy78'
    SAMPLE_RANGE_NAME = f'{sheet_name}!A:B'

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=3000)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    write_dataframe_to_sheet(data, SAMPLE_SPREADSHEET_ID, SAMPLE_RANGE_NAME, creds)
        
def write_data_to_appsheet(data):

    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # The ID and range of a sample spreadsheet.
    # SAMPLE_SPREADSHEET_ID = '1Pi3i4RSFXuqQ7xlXOpSLAb-c5j6F2en9WmscCxFHbNI'
    SAMPLE_SPREADSHEET_ID = '1vfBDEo1d1XVWZAffVwOGa1AvWc6HSRPKt23LuZPGbvY'
    SAMPLE_RANGE_NAME = 'Orders!A:H'
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    creds = None
    if os.path.exists('token.json'):
        # os.remove('token.json')
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=3000)
            # creds = flow.run_local_server()
            
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('sheets', 'v4', credentials=creds)
        
        # Get the current data in the "Orders" tab
        result = service.spreadsheets().values().get(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=SAMPLE_RANGE_NAME
        ).execute()
        values = result.get('values', [])

        # Check if the Order ID already exists
        existing_order_ids = [row[0] for row in values]
        order_id = data[0]
        # print(existing_order_ids[0])
        if order_id in existing_order_ids:
            # If the Order ID exists, find the index of the row
            row_index = existing_order_ids.index(order_id) + 1
 
            # Define the new range for the data
            new_range_name = f'Orders!A{row_index}:H{row_index}'

        else:
            # Calculate the next row number for the new entry
            next_row_number = len(values) + 1
            # Define the new range for the data
            new_range_name = f'Orders!A{next_row_number}:H{next_row_number}'

            start_index = len(values)
            number_of_rows = 1
            insert_rows(service, SAMPLE_SPREADSHEET_ID, start_index, number_of_rows)

        # Prepare your data to be written to the sheet
        value_data = [data]
            
        # Call the Sheets API to update the values
        result = service.spreadsheets().values().update(
            spreadsheetId=SAMPLE_SPREADSHEET_ID,
            range=new_range_name,
            valueInputOption="USER_ENTERED",
            body={"values": value_data}
        )
        
        response = result.execute()

        print("Data written successfully!")
        print(response)
    except HttpError as err:
        print(err)

def insert_rows(service, spreadsheet_id, start_index, number_of_rows):
    body = {
        "range": {
            "sheetId": "1102244011",  # Sheet name or ID
            "dimension": "ROWS",
            "startIndex": start_index,  # Index where you want to start inserting rows
            "endIndex": start_index + number_of_rows  # End index (exclusive)
        },
        "inheritFromBefore": False  # If true, the new rows will inherit formatting from the row above
    }

    request = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "insertDimension": body
                }
            ]
        }
    )

    response = request.execute()
    return response

if __name__ == '__main__':

    new_entry = [
        "ORD12345",     # Order ID
        "CUST67890",    # Customer ID
        "2024-02-21",   # Order Date
        "Pending",      # Status
        "example.pdf",  # File
        "example.png",  # Signature
        "2024-02-21",   # Timestamp
        "This is a note"  # Note
    ]

    write_data_to_appsheet([new_entry])
    