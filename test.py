from __future__ import print_function
import os.path
# import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def test_read_access(service, spreadsheet_id, range_name):
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        print("Read access test successful.")
    except Exception as e:
        print("Read access test failed:", e)

def test_write_access(service, spreadsheet_id, range_name):
    try:
        value_input_option = "RAW"  # Use "RAW" for plain text
        value_range_body = {
            "values": [["Test Data"]]
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            body=value_range_body
        ).execute()
        print("Write access test successful.")
    except Exception as e:
        print("Write access test failed:", e)

if __name__ == '__main__':
    
    """Writes data to the supply sheet."""
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # The ID and range of the sample spreadsheet.
    SAMPLE_SPREADSHEET_ID = '1_ndw8fGpmkJSPuV3damUE8FePXLySymcxuyTGKLdy78'

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
            
    # Initialize the Sheets service
    service = build('sheets', 'v4', credentials=creds)

    # Define the spreadsheet ID and range for the tests
    spreadsheet_id = '1vfBDEo1d1XVWZAffVwOGa1AvWc6HSRPKt23LuZPGbvY'
    range_name = 'Orders!A2:A2'  # Use a range that exists in your spreadsheet

    # Perform read access test
    test_read_access(service, spreadsheet_id, range_name)

    # Perform write access test
    test_write_access(service, spreadsheet_id, range_name)
