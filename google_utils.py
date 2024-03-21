from __future__ import print_function
import os.path
import datetime

# import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

def authenticate():
    
    SCOPES = ['https://www.googleapis.com/auth/drive',
              'https://www.googleapis.com/auth/spreadsheets']

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
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
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds
    
#%% UPDATE SUPPLY SHEET
def write_data_to_supply_sheet(sheet_name, data):
    """Writes data to the supply sheet."""
    
    # Authenticate
    creds = authenticate()
    
    # The ID and range of the sample spreadsheet.
    SPREADSHEET_ID = '1_ndw8fGpmkJSPuV3damUE8FePXLySymcxuyTGKLdy78'
    RANGE_NAME = f'{sheet_name}!A:B'
    
    try:
        service = build('sheets', 'v4', credentials=creds)
        
        # Clear existing data in the sheet
        clear_sheet(service, SPREADSHEET_ID, RANGE_NAME)
        
        # Convert DataFrame to list of lists
        values = [data.columns.tolist()] + data.values.tolist()
        
        # Call the Sheets API to update the values
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption="USER_ENTERED",
            body={"values": values}
        ).execute()
        
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        print(f"{formatted_datetime}: Voorraad geupdated (google_sheet_id: {SPREADSHEET_ID} , updated range: {result['updatedRange']})")
    except HttpError as err:
        print(err)

def clear_sheet(service, spreadsheet_id, range_name):
    """Clears the specified range in a Google Sheet."""
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        body={}
    ).execute()
    

#%% UPDATE PAKBON SHEET    
def write_data_to_appsheet(data):

    # The ID and range of a sample spreadsheet.
    SPREADSHEET_ID = '1vfBDEo1d1XVWZAffVwOGa1AvWc6HSRPKt23LuZPGbvY'
    RANGE_NAME = 'Orders!A:H'
    
    creds = authenticate()
            
    try:
        service = build('sheets', 'v4', credentials=creds)
        
        # Get the current data in the "Orders" tab
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
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
            insert_rows(service, SPREADSHEET_ID, start_index, number_of_rows)

        # Prepare your data to be written to the sheet
        # value_data = [data]
        value_data = [data]
        
        [["Test Data", "Test Data", "Test Data", "Test Data", "Test Data", "Test Data", "Test Data", "Test Data"]]
        
        # Call the Sheets API to update the values
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=new_range_name,
            valueInputOption="USER_ENTERED",
            body={"values": value_data}
        ).execute()
        
        print(f"Pakbon {data[0]} succesvol toegevoegd aan Luciano Delivery App! (google_sheet_id: {SPREADSHEET_ID})")
        # print(data)
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
    ).execute()

    # response = request.execute()
    # return response

#%% PAKBON PDF UPLOAD
def upload_pdf_to_drive(pdf_path):
    """ 
    pdf_path: Path to the PDF file to upload
    folder_id: ID of the Google Drive folder where you want to upload the PDF
    """
    
    # ID of the Google Drive folder where you want to upload the PDF
    folder_id = '1MqPvv1ATRoMh3sRu9qDEuH6ty3nE0HmR'
    
    # Authenticate
    creds = authenticate()
    
    try:
        service = build('drive', 'v3', credentials=creds)
    
        # Create file metadata
        file_metadata = {
            'name': os.path.basename(pdf_path),
            'parents': [folder_id]
        }
    
        # Upload PDF file
        media = MediaFileUpload(pdf_path, mimetype='application/pdf')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print('File ID: %s' % file.get('id'))
        
    except HttpError as err:
        print(err)

if __name__ == '__main__':

    # new_entry = [
    #     "ORD12345",     # Order ID
    #     "CUST67890",    # Customer ID
    #     "2024-02-21",   # Order Date
    #     "FALSE",      # Status
    #     "example.pdf",  # File
    #     '',  # Signature
    #     '',   # Timestamp
    #     ''  # Note
    # ]

    # write_data_to_appsheet(new_entry)
    
    pdf_path = 'Orders_Pdfs\BKDH_2024-03-08.pdf'
    
    # ID of the Google Drive folder where you want to upload the PDF
    folder_id = '1MqPvv1ATRoMh3sRu9qDEuH6ty3nE0HmR'
    
    # Upload the PDF to the specified folder
    upload_pdf_to_drive(pdf_path, folder_id)