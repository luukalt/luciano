from __future__ import print_function
import os.path
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID of the target spreadsheet.
SPREADSHEET_ID = '1vfBDEo1d1XVWZAffVwOGa1AvWc6HSRPKt23LuZPGbvY'
RANGE_NAME = 'Orders'

def get_google_sheets_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('sheets', 'v4', credentials=creds)

def get_last_row_index(service, spreadsheet_id, range_name):
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    values = result.get('values', [])
    return len(values) + 1  # Adding 1 to get the index of the next row

def write_to_sheet(service, spreadsheet_id, range_name, data):
    try:
        # Call the Sheets API to update the spreadsheet
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body={"values": data}
        ).execute()
        print("Data successfully written to Google Sheets.")
        print(result)
    except HttpError as err:
        print("An error occurred:", err)

def main():
    service = get_google_sheets_service()
    last_row_index = get_last_row_index(service, SPREADSHEET_ID, RANGE_NAME)
    data_to_write = [
        # Add your order data here, e.g.,
        ["12345", "Cust123", "2024-02-21", "Pending", "", "", "", "Sample note"]
    ]
    # Adjusting the range to start from the next row after the last entry
    range_name_with_offset = f'{RANGE_NAME}!A{last_row_index}'
    write_to_sheet(service, SPREADSHEET_ID, range_name_with_offset, data_to_write)

if __name__ == '__main__':
    main()
