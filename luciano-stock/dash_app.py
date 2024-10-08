#%% IMPORT PACKAGES
import os
import datetime
import logging
import shutil
import pandas as pd

import dash
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash import html, dcc, dash_table, callback, Input, Output, State

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, KeepTogether
from reportlab.lib import colors

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# USER MODULES
from email_utils import send_email
from google_utils import write_data_to_appsheet, write_data_to_supply_sheet, upload_pdf_to_drive 

#%% START APP
# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = 'Luciano Dashboard'

#%% DEFINE SQL PARAMETERS
# Define the connection parameters
server_name = 'LAPTOP-1JTJJ292\\SQLEXPRESS'  # Replace with your SQL Server instance name or IP address
database_name = 'AS-SW'  # Replace with your database name
username = 'assw'  # Replace with your SQL Server username
password = 'assw2024!'  # Replace with your SQL Server password

# Create a connection string
conn_str = f'DRIVER={{SQL Server}};SERVER={server_name};DATABASE={database_name};UID={username};PWD={password}'

conn_str2 = f'mssql+pyodbc://{username}:{password}@{server_name}/{database_name}?driver=ODBC+Driver+17+for+SQL+Server'

# Define Database Engine (replace conn_str with your actual connection string)
engine = create_engine(conn_str2)

# Create a Session Maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#%% DEFINE STORES
# Dummy data for stores
stores = [
    {'label': 'Bitterkoud Den Haag', 'value': 'BKDH'},
    {'label': 'Luciano Alphen', 'value': 'LA'},
    {'label': 'Luciano Delft Buitenhof', 'value': 'LDB'},
    {'label': 'Luciano Delft Centrum', 'value': 'LDC'},
    {'label': 'Luciano Den Haag', 'value': 'LDH'},
    {'label': 'Luciano Heemstede', 'value': 'LHE'},
    {'label': 'Luciano Hoofddorp', 'value': 'LHD'},
    {'label': 'Luciano Leiden', 'value': 'LL'},
    {'label': 'Luciano Maassluis', 'value': 'LM'},
    {'label': 'Luciano Overveen', 'value': 'LO'},
    {'label': 'Luciano Waddinxveen', 'value': 'LWV'},
    {'label': 'Luciano Wassenaar', 'value': 'LWN'},
    {'label': 'Luciano Wassenaar HQ', 'value': 'LWHQ'},
    {'label': 'Luciano Woerden', 'value': 'LWD'},
    {'label': 'Luciano Zandvoort XL', 'value': 'LZXL'},
    {'label': 'Luciano Zandvoort XS', 'value': 'LZXS'},
    {'label': 'Moments Voorschoten', 'value': 'MV'},
    {'label': 'Eenmalige klant', 'value': 'EK'},
    {'label': 'Breuk', 'value': 'BREUK'},
    {'label': 'Koen van Es', 'value': 'KVE'},
    {'label': 'Rozenstein', 'value': 'ROZ'},
    {'label': 'Broeders', 'value': 'BRO'},
    {'label': 'Sport', 'value': 'SPO'},
    {'label': 'Grand Cafe de Vriend', 'value': 'GCDV'},
    {'label': 'Bistro Tante Bet', 'value': 'BTB'},
    {'label': 'Rooijakkers', 'value': 'ROOIJ'},
]

store_library = {}

for i, store in enumerate(stores, 1):
    store_library[store['label']] = i

#%% DEFINE PAKBON DATAFRAMES [PAGE 1]
# Initial empty DataFrame to store product details
df_products = pd.DataFrame(columns=['Barcode', 'Type', 'Omschrijving', 'Gewicht [kg]'])
df_taart = pd.DataFrame(columns=['Omschrijving', 'Aantal'])
df_diversen = pd.DataFrame(columns=['Omschrijving', 'Aantal'])
df_suikervrij = pd.DataFrame(columns=['Omschrijving', 'Aantal'])
df_gebak = pd.DataFrame(columns=['Omschrijving', 'Aantal'])
df_potjes = pd.DataFrame(columns=['Omschrijving', 'Aantal'])

# Define columns for google sheet supply (TAART + DIVERSEN)
selected_columns = ['Omschrijving', 'Aantal']  # Adjust column names as needed

#%% Define a navigation bar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dcc.Link('PAKBON', href='/', className='nav-link')),
        dbc.NavItem(dcc.Link('IJS', href='/ijs', className='nav-link')),
        dbc.NavItem(dcc.Link('TAART', href='/taart', className='nav-link')),
        dbc.NavItem(dcc.Link('DIVERSEN', href='/diversen', className='nav-link')),
        dbc.NavItem(dcc.Link('SUIKERVRIJ', href='/suikervrij', className='nav-link')),
        dbc.NavItem(dcc.Link('GEBAK', href='/gebak', className='nav-link')),
        dbc.NavItem(dcc.Link('POTJES', href='/potjes', className='nav-link')),
        dbc.NavItem(dcc.Link('ORDERS', href='/orders', className='nav-link')),
        # Add more navigation items here as needed
    ],
    brand="Luciano Voorraad Beheer",
    brand_href="/",
    color="primary",
    dark=True,
)

#%% Define layouts for each page
#%%% page 1 layout
page_1_layout = dbc.Container([
    navbar,
    html.H1('Pakbon maken'),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("WINKEL"),
                dbc.CardBody([
                    dcc.Dropdown(id='store-dropdown', options=stores, placeholder='Selecteer een winkel', className="mb-2"),
                    # dbc.Button('Add Product', id='add-ijs-button', n_clicks=0, color="primary", className="me-1"),
                ])
            ]),
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("NOTITIE"),
                dbc.CardBody([
                    dcc.Textarea(
                        id='note',
                        placeholder='Enter text here...',
                        value='',  # Default value
                        style={'width': '100%', 'height': '200px'}  # Adjust width and height as needed
                    ),
                ])
            ]),
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("ACTIES"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button('Genereer pakbon en stuur naar Luciano Delivery App', id='generate-pdf-button', n_clicks=0, color="success"),
                        ], width=4),  # This column takes 9 out of 12 columns, leaving 3 for the next column
                        dbc.Col([
                            dbc.Button('Laad laatst opgeslagen pakbon in', id='load_last_saved_products-button', n_clicks=0, color="primary"),
                        ], width=4, className="d-flex justify-content-end"),  # This column takes 3 out of 12 columns and aligns its content to the end
                        dbc.Col([
                            dbc.Button('Maak pakbon leeg', id='clear_form-button', n_clicks=0, color="warning"),
                            dbc.Modal(
                                [
                                    dbc.ModalHeader("Formulier leeg maken"),
                                    dbc.ModalBody("Weet u zeker dat u het formulier wilt leegmaken?"),
                                    dbc.ModalFooter(
                                        [
                                            # dbc.Button("Cancel", id="cancel_clear", className="mr-auto"),
                                            dbc.Button("Maak leeg", id="confirm_clear", className="ml-auto"),
                                        ]
                                    ),
                                ],
                                id="confirm_modal",
                                centered=True,
                            ),
                        ], width=4, className="d-flex justify-content-end"),  # This column takes 3 out of 12 columns and aligns its content to the end
                    ]),
                    html.Div(id='pdf-generation-status', className="mt-2")
                ])
            ]),
        ], width=4), 
    ], className="mt-3"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("IJS", id="ijs-header"),
                dbc.CardBody([
                    dbc.Input(id='barcode-input-ijs-page1', type='text', placeholder='Klik eerst hier en scan dan de ijsbakken', debounce=True),
                    html.Div(id='barcode-status-ijs-page1', className="mt-2"),  # This will display the status after checking the barcode
                    html.Div(id='deleted-row-ijs-page1', className="mt-2"),  # This will display the status after checking the barcode 
                    dash_table.DataTable(
                        id='ijs-table-page1',
                        columns=[{'name': i, 'id': i} for i in df_products.columns],
                        data=df_products.to_dict('records'),
                        editable=False,
                        row_deletable=True,
                        # filter_action='native',  # Enable filtering
                        sort_action='native',  # Enable sorting
                        style_table={'overflowX': 'auto'},
                        page_action='none',
                        style_cell={
                            'minWidth': '100px', 'width': '150px', 'maxWidth': '180px',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                        }
                    )
                ])
            ]),
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("TAART", id="taart-header"),
                dbc.CardBody([
                    # dbc.Button('Voeg toe', id='button-input-taart-page1', n_clicks=0, color="success"),
                    dbc.Input(id='barcode-input-taart-page1', type='text', placeholder='Klik eerst hier en scan dan de taart barcode', debounce=True, style={"margin-bottom": "10px"}),
                    dbc.Input(id='taart-count-input-page1',  type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    html.Div(id='barcode-status-taart-page1', className="mt-2"),  # This will display the status after checking the barcode
                    html.Div(id='deleted-row-taart-page1', className="mt-2"),  # This will display the status after checking the barcode 
                    dash_table.DataTable(
                        id='taart-table-page1',
                        columns=[{'name': i, 'id': i} for i in df_taart.columns],
                        data=df_taart.to_dict('records'),
                        editable=False,
                        row_deletable=True,
                        # filter_action='native',  # Enable filtering
                        sort_action='native',  # Enable sorting
                        style_table={'overflowX': 'auto'},
                        page_action='none',
                        style_cell={
                            'minWidth': '100px', 'width': '150px', 'maxWidth': '180px',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                        }
                    )
                ])
            ], style={"margin-bottom": "20px"}),
            dbc.Card([
                dbc.CardHeader("DIVERSEN", id="diversen-header"),
                dbc.CardBody([
                    # dbc.Button('Voeg toe', id='button-input-diversen-page1', n_clicks=0, color="success"),
                    dbc.Input(id='barcode-input-diversen-page1', type='text', placeholder='Klik eerst hier en scan dan de producten', debounce=True, style={"margin-bottom": "10px"}),
                    dbc.Input(id='diversen-count-input-page1',  type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    html.Div(id='barcode-status-diversen-page1', className="mt-2"),  # This will display the status after checking the barcode
                    html.Div(id='deleted-row-diversen-page1', className="mt-2"),  # This will display the status after checking the barcode 
                    dash_table.DataTable(
                        id='diversen-table-page1',
                        columns=[{'name': i, 'id': i} for i in df_diversen.columns],
                        data=df_diversen.to_dict('records'),
                        editable=False,
                        row_deletable=True,
                        # filter_action='native',  # Enable filtering
                        sort_action='native',  # Enable sorting
                        style_table={'overflowX': 'auto'},
                        page_action='none',
                        style_cell={
                            'minWidth': '100px', 'width': '150px', 'maxWidth': '180px',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                        }
                    )
                ])
            ], style={"margin-bottom": "20px"}),
            dbc.Card([
                dbc.CardHeader("SUIKERVRIJ", id="suikervrij-header"),
                dbc.CardBody([
                    # dbc.Button('Voeg toe', id='button-input-suikervrij-page1', n_clicks=0, color="success"),
                    dbc.Input(id='barcode-input-suikervrij-page1', type='text', placeholder='Klik eerst hier en scan dan de producten', debounce=True, style={"margin-bottom": "10px"}),
                    dbc.Input(id='suikervrij-count-input-page1',  type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    html.Div(id='barcode-status-suikervrij-page1', className="mt-2"),  # This will display the status after checking the barcode
                    html.Div(id='deleted-row-suikervrij-page1', className="mt-2"),  # This will display the status after checking the barcode 
                    dash_table.DataTable(
                        id='suikervrij-table-page1',
                        columns=[{'name': i, 'id': i} for i in df_suikervrij.columns],
                        data=df_suikervrij.to_dict('records'),
                        editable=False,
                        row_deletable=True,
                        # filter_action='native',  # Enable filtering
                        sort_action='native',  # Enable sorting
                        style_table={'overflowX': 'auto'},
                        page_action='none',
                        style_cell={
                            'minWidth': '100px', 'width': '150px', 'maxWidth': '180px',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                        }
                    )
                ])
            ], style={"margin-bottom": "20px"}),
            dbc.Card([
                dbc.CardHeader("GEBAK", id="gebak-header"),
                dbc.CardBody([
                    # dbc.Button('Voeg toe', id='button-input-gebak-page1', n_clicks=0, color="success"),
                    dbc.Input(id='barcode-input-gebak-page1', type='text', placeholder='Klik eerst hier en scan dan de producten', debounce=True, style={"margin-bottom": "10px"}),
                    dbc.Input(id='gebak-count-input-page1',  type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    html.Div(id='barcode-status-gebak-page1', className="mt-2"),  # This will display the status after checking the barcode
                    html.Div(id='deleted-row-gebak-page1', className="mt-2"),  # This will display the status after checking the barcode 
                    dash_table.DataTable(
                        id='gebak-table-page1',
                        columns=[{'name': i, 'id': i} for i in df_gebak.columns],
                        data=df_gebak.to_dict('records'),
                        editable=False,
                        row_deletable=True,
                        # filter_action='native',  # Enable filtering
                        sort_action='native',  # Enable sorting
                        style_table={'overflowX': 'auto'},
                        page_action='none',
                        style_cell={
                            'minWidth': '100px', 'width': '150px', 'maxWidth': '180px',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                        }
                    )
                ])
            ], style={"margin-bottom": "20px"}),
            dbc.Card([
                dbc.CardHeader("POTJES", id="potjes-header"),
                dbc.CardBody([
                    # dbc.Button('Voeg toe', id='button-input-potjes-page1', n_clicks=0, color="success"),
                    dbc.Input(id='barcode-input-potjes-page1', type='text', placeholder='Klik eerst hier en scan dan de producten', debounce=True, style={"margin-bottom": "10px"}),
                    dbc.Input(id='potjes-count-input-page1',  type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    html.Div(id='barcode-status-potjes-page1', className="mt-2"),  # This will display the status after checking the barcode
                    html.Div(id='deleted-row-potjes-page1', className="mt-2"),  # This will display the status after checking the barcode 
                    dash_table.DataTable(
                        id='potjes-table-page1',
                        columns=[{'name': i, 'id': i} for i in df_potjes.columns],
                        data=df_potjes.to_dict('records'),
                        editable=False,
                        row_deletable=True,
                        # filter_action='native',  # Enable filtering
                        sort_action='native',  # Enable sorting
                        style_table={'overflowX': 'auto'},
                        page_action='none',
                        style_cell={
                            'minWidth': '100px', 'width': '150px', 'maxWidth': '180px',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                        }
                    )
                ])
            ], style={"margin-bottom": "20px"}),
        ], width=6),
    ], className="mt-3"),
], fluid=True)

#%%% page 2 layout [IJS]
page_2_layout = dbc.Container([
    navbar,
    html.H1('OVERZICHT DATABASE - IJS'),
    # dcc.Link('Ga terug naar PAKBON', href='/'),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("ANNOUNCEMENTS"),
                dbc.CardBody([
                    # dbc.Button("Update Database", id='update-ijs-database-button', color="primary", className="mt-2", n_clicks=0),
                    html.Div(id='barcode-status-ijs-page2', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("SCAN IJSBAK NAAR VOORRAAD"),
                dbc.CardBody([
                    dbc.Input(id='barcode-input-ijs-page2', type='text', placeholder='Klik eerst hier en scan dan de ijsbak', debounce=True),
                ])
            ]),
            html.Br(),
            dbc.Card([
            dbc.CardHeader("SCAN IJSBAK UIT VOORRAAD"),
                dbc.CardBody([
                    dbc.Input(id='barcode-output-ijs-page2', type='text', placeholder='Klik eerst hier en scan dan de ijsbak', debounce=True),
                ])
            ]),
        ], width=2),
        dbc.Col([
            dbc.Card([
                    dbc.CardHeader("VOORRAAD", id="stock-ijs-header"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='stock-table-ijs',
                            # columns=[{'name': i, 'id': i} for i in df_products_page2.columns],
                            # data=df_products_page2.to_dict('records'),
                            # editable=False,
                            # row_deletable=True,
                            # placeholder='Enter search text...',
                            # filter_action='native',  # Enable filtering
                            sort_action='native',  # Enable sorting
                            style_table={'overflowX': 'auto'},
                            # page_action='none',
                            style_cell={
                                'minWidth': '100px', 'width': '150px', 'maxWidth': '180px',
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                            }
                        )
                    ])
                ]),
        ], width=7),
        dbc.Col([
            dbc.Card([
                    dbc.CardHeader("VOORRAAD PER STUK"),
                    dbc.CardBody([
                        html.Div(id='supply-timestamp-ijs-page2', className="mt-2"),
                        dash_table.DataTable(
                            id='stock-count-table-ijs',
                            # editable=False,
                            # row_deletable=True,
                            # filter_action='native',  # Enable filtering
                            # sort_action='native',  # Enable sorting
                            style_table={'overflowX': 'auto'},
                            # page_action='none',
                            style_cell={
                                'minWidth': '100px', 'width': '150px', 'maxWidth': '180px',
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                            }
                        )
                    ])
                ]),
        ], width=3),
    ], className="mt-3"),
], fluid=True)

#%%% page 3 layout [TAART]
page_3_layout = dbc.Container([
    navbar,
    html.H1('OVERZICHT DATABASE - TAART'),
    # dcc.Link('Ga terug naar PAKBON', href='/'),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("ACTIES"),
                dbc.CardBody([
                    dbc.Button("Update Database", id='update-taart-database-button', color="primary", className="mt-2", n_clicks=0),
                    html.Div(id='barcode-status-taart-page3', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("SCAN TAART NAAR VOORRAAD"),
                dbc.CardBody([
                    dbc.Input(id='barcode-input-taart-page3', type='text', placeholder='Vul Taart Barcode in', debounce=True),
                    html.Br(),
                    dbc.Input(id='taart-count-input', type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    # html.Div(id='barcode-input-status-taart-page3', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("SCAN TAART UIT VOORRAAD"),
                dbc.CardBody([
                    dbc.Input(id='barcode-output-taart-page3', type='text', placeholder='Vul Taart Barcode in', debounce=True),
                    html.Br(),
                    dbc.Input(id='taart-count-output', type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    # html.Div(id='barcode-output-status-taart-page3', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("NIEUWE SMAAK"),
                dbc.CardBody([
                    dbc.Input(id='new-taart-barcode', type='text', placeholder='Barcode'),
                    html.Br(),
                    dbc.Input(id='new-taart-description', type='text', placeholder='Omschrijving'),
                    html.Br(),
                    dbc.Button('Voeg taart toe', id='add-taart-button', color="success", className="mt-2", n_clicks=0),
                    html.Div(id='add-taart-status')
                ])
            ]),
        ], width=4),
        dbc.Col([
            dbc.Card([
                    dbc.CardHeader("VOORRAAD"),
                    dbc.CardBody([
                        html.Div(id='supply-timestamp-taart-page3', className="mt-2"),
                        html.Div(id='deleted-row-taart-page3', className="mt-2"),  # This will display the status after checking the barcode
                        dash_table.DataTable(
                            id='stock-table-taart',
                            # editable=False,
                            row_deletable=True,
                            # filter_action='native',  # Enable filtering
                            # sort_action='native',  # Enable sorting
                            style_table={'overflowX': 'auto'},
                            # page_action='none',
                            style_cell={
                                'minWidth': '100px', 'width': '150px', 'maxWidth': '180px',
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                            }
                        )
                    ])
                ]),
        ], width=6),
    ], className="mt-3"),
], fluid=True)

#%%% page 4 layout [DIVERSEN]
page_4_layout = dbc.Container([
    navbar,
    html.H1('OVERZICHT DATABASE - DIVERSEN'),
    # dcc.Link('Ga terug naar PAKBON', href='/'),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("ACTIES"),
                dbc.CardBody([
                    dbc.Button("Update Database", id='update-diversen-database-button', color="primary", className="mt-2", n_clicks=0),
                    html.Div(id='barcode-status-diversen-page4', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("SCAN ITEM NAAR VOORRAAD"),
                dbc.CardBody([
                    dbc.Input(id='barcode-input-diversen-page4', type='text', placeholder='Vul Item Barcode in', debounce=True),
                    html.Br(),
                    dbc.Input(id='diversen-count-input', type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    # html.Div(id='barcode-input-status-taart-page3', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("SCAN ITEM UIT VOORRAAD"),
                dbc.CardBody([
                    dbc.Input(id='barcode-output-diversen-page4', type='text', placeholder='Vul Item Barcode in', debounce=True),
                    html.Br(),
                    dbc.Input(id='diversen-count-output', type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    # html.Div(id='barcode-output-status-taart-page3', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("NIEUW ITEM"),
                dbc.CardBody([
                    dbc.Input(id='new-diversen-barcode', type='text', placeholder='Barcode'),
                    html.Br(),
                    dbc.Input(id='new-diversen-description', type='text', placeholder='Omschrijving'),
                    html.Br(),
                    dbc.Button('Voeg item toe', id='add-diversen-button', color="success", className="mt-2", n_clicks=0),
                    html.Div(id='add-diversen-status')
                ])
            ]),
        ], width=4),
        dbc.Col([
            dbc.Card([
                    dbc.CardHeader("VOORRAAD"),
                    dbc.CardBody([
                        html.Div(id='supply-timestamp-diversen-page4', className="mt-2"),
                        html.Div(id='deleted-row-diversen-page4', className="mt-2"),  # This will display the status after checking the barcode
                        dash_table.DataTable(
                            id='stock-table-diversen',
                            # editable=False,
                            row_deletable=True,
                            # filter_action='native',  # Enable filtering
                            # sort_action='native',  # Enable sorting
                            style_table={'overflowX': 'auto'},
                            # page_action='none',
                            style_cell={
                                'minWidth': '100px', 'width': '150px', 'maxWidth': '180px',
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                            }
                        )
                    ])
                ]),
        ], width=6),
    ], className="mt-3"),
], fluid=True)

#%%% page 5 layout [SUIKERVRIJ]
page_5_layout = dbc.Container([
    navbar,
    html.H1('OVERZICHT DATABASE - SUIKERVRIJ'),
    # dcc.Link('Ga terug naar PAKBON', href='/'),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("ACTIES"),
                dbc.CardBody([
                    dbc.Button("Update Database", id='update-suikervrij-database-button', color="primary", className="mt-2", n_clicks=0),
                    html.Div(id='barcode-status-suikervrij-page5', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("SCAN ITEM NAAR VOORRAAD"),
                dbc.CardBody([
                    dbc.Input(id='barcode-input-suikervrij-page5', type='text', placeholder='Vul Item Barcode in', debounce=True),
                    html.Br(),
                    dbc.Input(id='suikervrij-count-input', type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    # html.Div(id='barcode-input-status-taart-page3', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("SCAN ITEM UIT VOORRAAD"),
                dbc.CardBody([
                    dbc.Input(id='barcode-output-suikervrij-page5', type='text', placeholder='Vul Item Barcode in', debounce=True),
                    html.Br(),
                    dbc.Input(id='suikervrij-count-output', type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    # html.Div(id='barcode-output-status-taart-page3', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("NIEUW ITEM"),
                dbc.CardBody([
                    dbc.Input(id='new-suikervrij-barcode', type='text', placeholder='Barcode'),
                    html.Br(),
                    dbc.Input(id='new-suikervrij-description', type='text', placeholder='Omschrijving'),
                    html.Br(),
                    dbc.Button('Voeg item toe', id='add-suikervrij-button', color="success", className="mt-2", n_clicks=0),
                    html.Div(id='add-suikervrij-status')
                ])
            ]),
        ], width=4),
        dbc.Col([
            dbc.Card([
                    dbc.CardHeader("VOORRAAD"),
                    dbc.CardBody([
                        html.Div(id='supply-timestamp-suikervrij-page5', className="mt-2"),
                        html.Div(id='deleted-row-suikervrij-page5', className="mt-2"),  # This will display the status after checking the barcode
                        dash_table.DataTable(
                            id='stock-table-suikervrij',
                            # editable=False,
                            row_deletable=True,
                            # filter_action='native',  # Enable filtering
                            # sort_action='native',  # Enable sorting
                            style_table={'overflowX': 'auto'},
                            # page_action='none',
                            style_cell={
                                'minWidth': '100px', 'width': '150px', 'maxWidth': '180px',
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                            }
                        )
                    ])
                ]),
        ], width=6),
    ], className="mt-3"),
], fluid=True)

#%%% page 6 layout [GEBAK]
page_6_layout = dbc.Container([
    navbar,
    html.H1('OVERZICHT DATABASE - GEBAK'),
    # dcc.Link('Ga terug naar PAKBON', href='/'),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("ACTIES"),
                dbc.CardBody([
                    dbc.Button("Update Database", id='update-gebak-database-button', color="primary", className="mt-2", n_clicks=0),
                    html.Div(id='barcode-status-gebak-page6', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("SCAN ITEM NAAR VOORRAAD"),
                dbc.CardBody([
                    dbc.Input(id='barcode-input-gebak-page6', type='text', placeholder='Vul Item Barcode in', debounce=True),
                    html.Br(),
                    dbc.Input(id='gebak-count-input', type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    # html.Div(id='barcode-input-status-taart-page3', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("SCAN ITEM UIT VOORRAAD"),
                dbc.CardBody([
                    dbc.Input(id='barcode-output-gebak-page6', type='text', placeholder='Vul Item Barcode in', debounce=True),
                    html.Br(),
                    dbc.Input(id='gebak-count-output', type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    # html.Div(id='barcode-output-status-taart-page3', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("NIEUW ITEM"),
                dbc.CardBody([
                    dbc.Input(id='new-gebak-barcode', type='text', placeholder='Barcode'),
                    html.Br(),
                    dbc.Input(id='new-gebak-description', type='text', placeholder='Omschrijving'),
                    html.Br(),
                    dbc.Button('Voeg item toe', id='add-gebak-button', color="success", className="mt-2", n_clicks=0),
                    html.Div(id='add-gebak-status')
                ])
            ]),
        ], width=4),
        dbc.Col([
            dbc.Card([
                    dbc.CardHeader("VOORRAAD"),
                    dbc.CardBody([
                        html.Div(id='supply-timestamp-gebak-page6', className="mt-2"),
                        html.Div(id='deleted-row-gebak-page6', className="mt-2"),  # This will display the status after checking the barcode
                        dash_table.DataTable(
                            id='stock-table-gebak',
                            # editable=False,
                            row_deletable=True,
                            # filter_action='native',  # Enable filtering
                            # sort_action='native',  # Enable sorting
                            style_table={'overflowX': 'auto'},
                            # page_action='none',
                            style_cell={
                                'minWidth': '100px', 'width': '150px', 'maxWidth': '180px',
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                            }
                        )
                    ])
                ]),
        ], width=6),
    ], className="mt-3"),
], fluid=True)

#%%% page 7 layout [POTJES]
page_7_layout = dbc.Container([
    navbar,
    html.H1('OVERZICHT DATABASE - POTJES'),
    # dcc.Link('Ga terug naar PAKBON', href='/'),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("ACTIES"),
                dbc.CardBody([
                    dbc.Button("Update Database", id='update-potjes-database-button', color="primary", className="mt-2", n_clicks=0),
                    html.Div(id='barcode-status-potjes-page7', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("SCAN ITEM NAAR VOORRAAD"),
                dbc.CardBody([
                    dbc.Input(id='barcode-input-potjes-page7', type='text', placeholder='Vul Item Barcode in', debounce=True),
                    html.Br(),
                    dbc.Input(id='potjes-count-input', type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    # html.Div(id='barcode-input-status-taart-page3', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("SCAN ITEM UIT VOORRAAD"),
                dbc.CardBody([
                    dbc.Input(id='barcode-output-potjes-page7', type='text', placeholder='Vul Item Barcode in', debounce=True),
                    html.Br(),
                    dbc.Input(id='potjes-count-output', type='number', placeholder='Vul aantal in', min=0, debounce=True),
                    # html.Div(id='barcode-output-status-taart-page3', className="mt-2"),  # This will display the status after checking the barcode
                ])
            ]),
            
            html.Br(),
            
            dbc.Card([
                dbc.CardHeader("NIEUW ITEM"),
                dbc.CardBody([
                    dbc.Input(id='new-potjes-barcode', type='text', placeholder='Barcode'),
                    html.Br(),
                    dbc.Input(id='new-potjes-description', type='text', placeholder='Omschrijving'),
                    html.Br(),
                    dbc.Button('Voeg item toe', id='add-potjes-button', color="success", className="mt-2", n_clicks=0),
                    html.Div(id='add-potjes-status')
                ])
            ]),
        ], width=4),
        dbc.Col([
            dbc.Card([
                    dbc.CardHeader("VOORRAAD"),
                    dbc.CardBody([
                        html.Div(id='supply-timestamp-potjes-page7', className="mt-2"),
                        html.Div(id='deleted-row-potjes-page7', className="mt-2"),  # This will display the status after checking the barcode
                        dash_table.DataTable(
                            id='stock-table-potjes',
                            # editable=False,
                            row_deletable=True,
                            # filter_action='native',  # Enable filtering
                            # sort_action='native',  # Enable sorting
                            style_table={'overflowX': 'auto'},
                            # page_action='none',
                            style_cell={
                                'minWidth': '100px', 'width': '150px', 'maxWidth': '180px',
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                            }
                        )
                    ])
                ]),
        ], width=6),
    ], className="mt-3"),
], fluid=True)

#%%% page 8 layout [ORDERS]
page_8_layout = dbc.Container([
    navbar,
    html.H1('OVERZICHT ORDERS - IJS'),
    # dcc.Link('Ga terug naar PAKBON', href='/'),
    html.Br(),
    dbc.Row([
        dbc.Col([
            
            dbc.Card([
                dbc.CardHeader("Zoektermen"),
                dbc.CardBody([
                    dbc.Col(html.Label('Kies Winkel:'), width='auto'),
                    dbc.Col(dcc.Dropdown(id='store-dropdown-page8', options=stores, placeholder='Selecteer een winkel', className="mb-2"), width='auto'),
                    
                    dbc.Col(html.Label('Vul datum in:'), width='auto'),
                    dbc.Col(dbc.Input(id='order-date-page8', type='text', debounce=True), width='auto'),
                    
                    dbc.Col(html.Label('Barcode:'), width='auto'),
                    dbc.Col(dbc.Input(id='barcode-ijs-page8', type='text', debounce=True), width='auto'),
                    
                    dbc.Col(html.Label('Smaak:'), width='auto'),
                    dbc.Col(dbc.Input(id='smaak-ijs-page8', type='text', debounce=True), width='auto'),
                    
                    dbc.Button("Zoek", id="search-button-page8", color="primary", className="mt-3")
                ]),
                
            ]),
            html.Br(),
        ], width=3),
        dbc.Col([
            dbc.Card([
                    dbc.CardHeader("ORDERS", id="orders-header"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            id='orders-table',
                            # columns=[{'name': i, 'id': i} for i in df_products_page2.columns],
                            # data=df_products_page2.to_dict('records'),
                            # editable=False,
                            # row_deletable=True,
                            # placeholder='Enter search text...',
                            # filter_action='native',  # Enable filtering
                            sort_action='native',  # Enable sorting
                            style_table={'overflowX': 'auto'},
                            # page_action='none',
                            style_cell={
                                'minWidth': '100px', 'width': '150px', 'maxWidth': '180px',
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                            }
                        )
                    ])
                ]),
        ], width=7),
        
    ], className="mt-3"),
], fluid=True)

#%%% Update the app.layout to include page routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),  # This tracks the URL
    dcc.Store(id='ijs-table-storage-page1',  storage_type='session'),
    dcc.Store(id='taart-table-storage-page1',  storage_type='session'),
    dcc.Store(id='diversen-table-storage-page1',  storage_type='session'),
    dcc.Store(id='suikervrij-table-storage-page1',  storage_type='session'),
    dcc.Store(id='gebak-table-storage-page1',  storage_type='session'),
    dcc.Store(id='potjes-table-storage-page1',  storage_type='session'),
    html.Div(id='page-content',), # Content will be rendered in this element
])

#%% CALLBACKS
# Callback for dynamic page routing
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
    prevent_initial_call=True
)
def display_page(pathname):
    
    if pathname == '/orders':
        return page_8_layout
    if pathname == '/potjes':
        return page_7_layout
    if pathname == '/gebak':
        return page_6_layout
    if pathname == '/suikervrij':
        return page_5_layout
    if pathname == '/diversen':
        return page_4_layout
    elif pathname == '/taart':
        return page_3_layout
    elif pathname == '/ijs':
        return page_2_layout
    else:  # Default page
        return page_1_layout


#%%% CALLBACKS PAGE 1 [ALL]
@app.callback(
    [Output("ijs-header", "children"),
     Output("taart-header", "children"),
     Output("diversen-header", "children"),
     Output("suikervrij-header", "children"),
     Output("gebak-header", "children"),
     Output("potjes-header", "children"),
     Output('ijs-table-page1', 'data', allow_duplicate=True),
     Output('taart-table-page1', 'data', allow_duplicate=True),
     Output('diversen-table-page1', 'data', allow_duplicate=True),
     Output('suikervrij-table-page1', 'data', allow_duplicate=True),
     Output('gebak-table-page1', 'data', allow_duplicate=True),
     Output('potjes-table-page1', 'data', allow_duplicate=True)
     ],
    [Input('load_last_saved_products-button', 'n_clicks'),
      State('ijs-table-storage-page1', 'data'),
      State('taart-table-storage-page1', 'data'),
      State('diversen-table-storage-page1', 'data'),
      State('suikervrij-table-storage-page1', 'data'),
      State('gebak-table-storage-page1', 'data'),
      State('potjes-table-storage-page1', 'data')
      ],  # Triggered by the new button click
    prevent_initial_call=True
)
def load_last_saved_form(n_clicks, products, taarten, diversen, suikervrij, gebak, potjes):
    # Perform some action here when the new button is clicked
    if n_clicks is not None and n_clicks > 0:
        # Your action here, for example:
        
        row_count = len(products) if products else 0
        header_products = f"IJS: {row_count} bakken"
    
        row_count = sum(row['Aantal'] for row in taarten) if taarten else 0
        header_taarten = f"TAART: {row_count}"
    
        row_count = sum(row['Aantal'] for row in diversen) if diversen else 0
        header_diversen = f"DIVERSEN: {row_count}"
    
        row_count = sum(row['Aantal'] for row in suikervrij) if suikervrij else 0
        header_suikervrij = f"SUIKERVRIJ: {row_count}"
    
        row_count = sum(row['Aantal'] for row in gebak) if gebak else 0
        header_gebak = f"GEBAK: {row_count}"
    
        row_count = sum(row['Aantal'] for row in potjes) if potjes else 0
        header_potjes = f"POTJES: {row_count}"
        
        return header_products, header_taarten, header_diversen, header_suikervrij, header_gebak, header_potjes, products, taarten, diversen, suikervrij, gebak, potjes
    else:
        # If button is not clicked yet, return default value
        return ([],) * 6

@app.callback(
    Output("confirm_modal", "is_open"),
    [Input("clear_form-button", "n_clicks"), 
     Input("confirm_clear", "n_clicks")],
)
def toggle_modal(clear_form_clicks, confirm_clear_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id == "clear_form-button" and clear_form_clicks:
        return True
    elif button_id == "confirm_clear" and confirm_clear_clicks:
        return False
    return False

@app.callback(
    [Output('ijs-table-page1', 'data',  allow_duplicate=True),
      Output('taart-table-page1', 'data',  allow_duplicate=True),
      Output('diversen-table-page1', 'data',  allow_duplicate=True),
      Output('suikervrij-table-page1', 'data',  allow_duplicate=True),
      Output('gebak-table-page1', 'data',  allow_duplicate=True),
      Output('potjes-table-page1', 'data',  allow_duplicate=True),
      Output('ijs-table-storage-page1', 'data',  allow_duplicate=True),
      Output('taart-table-storage-page1', 'data',  allow_duplicate=True),
      Output('diversen-table-storage-page1', 'data',  allow_duplicate=True),
      Output('suikervrij-table-storage-page1', 'data',  allow_duplicate=True),
      Output('gebak-table-storage-page1', 'data',  allow_duplicate=True),
      Output('potjes-table-storage-page1', 'data',  allow_duplicate=True) 
    ],
    [Input('confirm_clear', 'n_clicks')],  # Triggered by the new button click
    prevent_initial_call=True
)
def clear_form(confirm_clear_clicks):
    if confirm_clear_clicks is not None and confirm_clear_clicks > 0:
        return ([],) * 12
    else:
        # Return some default values or data if needed
        return (dash.no_update,) * 12 


#%%%% IJS
@app.callback(
    [Output("ijs-header", "children", allow_duplicate=True),
     Output('barcode-status-ijs-page1', 'children'),
     Output('ijs-table-page1', 'data', allow_duplicate=True),
     Output('ijs-table-storage-page1', 'data', allow_duplicate=True),
     Output('barcode-input-ijs-page1', 'value')],
    [Input('barcode-input-ijs-page1', 'n_submit'),
     State('barcode-input-ijs-page1', 'value'),
     State('ijs-table-page1', 'data')],
    prevent_initial_call=True,
)
def scan_barcode_ijs_page1(_, barcode, rows):
    
    if rows is None:
        rows = []  # Initialize rows as an empty list if it's None
        
    if barcode is None:
        raise PreventUpdate  # No barcode entered, do nothing
    
    barcode = ''.join(char for char in barcode if char != ' ')
    
    # Initialize the alert message
    alert_msg = None
    
    # Create a database session using SessionLocal
    db = SessionLocal()
    
    # Define the select query
    select_query = text("SELECT [DATA01], [DATA03], [DATA02], [ValueNet] FROM [dbo].[DATA] WHERE [DATA01] = :barcode AND [DATA06] = 1")
    
    # Execute the select query using SQLAlchemy
    result = db.execute(select_query, {"barcode": barcode}).fetchone()
    
    if result:
        # The barcode exists in the database and the item is in stock, update the status
        
        # Define the update query
        update_query = text(
            "UPDATE [dbo].[DATA] SET [DATA06] = 0 WHERE [DATA01] = :barcode"
        )
        
        # Execute the update query using SQLAlchemy
        db.execute(update_query, {"barcode": barcode})
        db.commit()  # Commit the update
        
        # Create a new row for the product with actual data
        new_row = {
            'Barcode': result[0],
            'Type': result[1],
            'Omschrijving': result[2],
            'Gewicht [kg]': result[3]
        }
        rows.append(new_row)

        alert_msg = dbc.Alert(f'Barcode {str(barcode)} found in database and item was in stock. Now marked as out of stock.', color="success")
    else:
        # The barcode does not exist in the database or item is not in stock
        
        # Define the existence check query
        exists_query = text(
            "SELECT COUNT(*) FROM [dbo].[DATA] WHERE [DATA01] = :barcode"
        )
        
        # Execute the existence check query using SQLAlchemy
        exists = db.execute(exists_query, {"barcode": barcode}).fetchone()[0]

        if exists > 0:
            # The item exists but is out of stock
            alert_msg = dbc.Alert(f'Barcode {str(barcode)} found in database but item is currently out of stock.', color="warning")
        else:
            # The item does not exist
            alert_msg = dbc.Alert(f'Barcode {str(barcode)} not found in database.', color="danger")
    
    row_count = len(rows)
    header = f"IJS: {row_count} bakken"
    
    # Close the database session
    db.close()
    
    return header, alert_msg, rows, rows, None

@app.callback(
    [Output("ijs-header", "children", allow_duplicate=True),
     Output('deleted-row-ijs-page1', 'children'),
     Output('ijs-table-storage-page1', 'data', allow_duplicate=True)],# You might need to add this component to your layout to display the deleted row information
    [Input('ijs-table-page1', 'data'),
     State('ijs-table-page1', 'data_previous')],
    prevent_initial_call=True,
)
def detect_deleted_row_ijs_page1(current_data, previous_data):
    if not dash.callback_context.triggered:
        # This is the initial load, no data has been deleted
        raise PreventUpdate

    if previous_data is None:
        # This can happen if there's no previous data to compare against
        raise PreventUpdate

    # Convert both lists of dictionaries (current and previous data) into sets of tuples for comparison
    current_set = {tuple(d.items()) for d in current_data} if current_data else set()
    previous_set = {tuple(d.items()) for d in previous_data} if previous_data else set()

    # Find the difference between the two sets; this will be the deleted row(s)
    deleted_rows = previous_set - current_set

    # Convert the deleted rows back into a list of dictionaries to display or use elsewhere
    deleted_rows_dicts = [dict(row) for row in deleted_rows]

    # Initialize the alert message
    alert_msg = None

    if deleted_rows_dicts:
        # If there are deleted rows, process each one
        for deleted_row in deleted_rows_dicts:
            # Extract the ID of the deleted row
            deleted_id = deleted_row.get('Barcode', None)
            # print(deleted_id)
            if deleted_id:
                # Connect to the database and update the InStock status
                try:
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    delete_query = text("UPDATE [dbo].[DATA] SET [DATA06] = 1 WHERE [DATA01] = :deleted_id")
                    db.execute(delete_query, {"deleted_id": deleted_id})
                    
                    # Commit changes to the database
                    db.commit()
                    
                    db.close()
                    
                    row_count = len(current_set)
                    header = f"IJS: {row_count} bakken"
                    
                    alert_msg = dbc.Alert(f"Barcode {deleted_id} updated in database; set as in stock.", color="success")
                except Exception as e:
                    alert_msg = dbc.Alert(f"Failed to update barcode {deleted_id} in database: {str(e)}", color="danger")
            else:
               alert_msg = dbc.Alert("Deleted row did not have a valid ID.", color="danger")
    else:
        # If no rows have been deleted, return an appropriate message
        alert_msg = dbc.Alert("No rows have been deleted.", color="warning")

    return header, alert_msg, current_data

#%%%% TAART
@app.callback(
    [Output("taart-header", "children", allow_duplicate=True),
     Output('barcode-status-taart-page1', 'children'),
     Output('taart-table-page1', 'data', allow_duplicate=True),
     Output('taart-table-storage-page1', 'data', allow_duplicate=True),
     Output('barcode-input-taart-page1', 'value'),
     Output('taart-count-input-page1', 'value')],
    [Input('taart-count-input-page1', 'n_submit'),
     # Input('button-input-taart-page1', 'n_clicks'),
     State('barcode-input-taart-page1', 'value'),
     State('taart-count-input-page1', 'value'),
     State('taart-table-page1', 'data')],
    prevent_initial_call=True,
)
def scan_barcode_taart_page1(_, barcode_input, item_count_input, rows):
    
    if item_count_input is None:
        raise PreventUpdate  # No barcode entered, do nothing
        
    if rows is None:
        rows = []  # Initialize rows as an empty list if it's None
        
    if barcode_input is None:
        raise PreventUpdate  # No barcode entered, do nothing
    
    # Initialize the alert message
    alert_msg = None
    
    # Create a database session using SessionLocal
    db = SessionLocal()
    
    # Define the select query
    select_query = text("SELECT [Omschrijving], [Aantal] FROM [dbo].[TAART] WHERE [Barcode] = :barcode")
    
    # Execute the select query using SQLAlchemy
    result_select = db.execute(select_query, {"barcode": barcode_input}).fetchone()
    
    if result_select:
        
        # The barcode exists in the database and the item is in stock, update the status
        alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} found in database and item was in stock.', color="success")
        
        # Update input table
        if barcode_input is not None and item_count_input is not None:
            
            update_query = text("UPDATE [dbo].[TAART] SET [Aantal] = [Aantal] - :item_count WHERE [Barcode] = :barcode")
            result_update = db.execute(update_query, {"item_count": item_count_input, "barcode": barcode_input})
            
            # Fetch the updated row from the database
            updated_row = db.execute(select_query, {"barcode": barcode_input}).fetchone()

            omschrijving = updated_row[0]
            
            if rows:
                
                # Flag to keep track of whether the row was found in rows
                row_found = False
                
                # Check if the row exists in rows
                for row in rows:
                    if row['Omschrijving'] == omschrijving:
                        # Update the quantity in the existing row
                        row['Aantal'] += item_count_input
                        row_found = True  # Set the flag to True
                    
                # If the row was not found in rows, add a new row
                if not row_found:
                    new_row = {
                        'Omschrijving': omschrijving,
                        'Aantal': item_count_input,
                    }
                    rows.append(new_row)
            else:
                # There are no existing rows, so add a new row
                new_row = {
                    'Omschrijving': omschrijving,
                    'Aantal': item_count_input,
                }
                rows.append(new_row)
                
            # Commit changes to the database
            db.commit()
            
    else:
        # The barcode does not exist in the database or item is not in stock
        
        # Define the existence check query
        exists_query = text(
            "SELECT COUNT(*) FROM [dbo].[TAART] WHERE [Barcode] = :barcode"
        )
        
        # Execute the existence check query using SQLAlchemy
        exists = db.execute(exists_query, {"barcode": barcode_input}).fetchone()[0]

        if exists > 0:
            # The item exists but is out of stock
            alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} found in database but item is currently out of stock.', color="warning")
        else:
            # The item does not exist
            alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} not found in database.', color="danger")
    
    row_count = sum(row['Aantal'] for row in rows)
    header = f"TAART: {row_count}"
    
    # Close the database session
    db.close()
    
    return header, alert_msg, rows, rows, None, None
    
    # return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


@app.callback(
    [Output("taart-header", "children", allow_duplicate=True),
     Output('deleted-row-taart-page1', 'children'),
     Output('taart-table-storage-page1', 'data', allow_duplicate=True)],# You might need to add this component to your layout to display the deleted row information
    [Input('taart-table-page1', 'data'),
     State('taart-table-page1', 'data_previous')],
    prevent_initial_call=True,
)
def detect_deleted_row_taart_page1(current_data, previous_data):
    if not dash.callback_context.triggered:
        # This is the initial load, no data has been deleted
        raise PreventUpdate

    if previous_data is None:
        # This can happen if there's no previous data to compare against
        raise PreventUpdate

    # Convert both lists of dictionaries (current and previous data) into sets of tuples for comparison
    current_set = {tuple(d.items()) for d in current_data} if current_data else set()
    previous_set = {tuple(d.items()) for d in previous_data} if previous_data else set()

    # Find the difference between the two sets; this will be the deleted row(s)
    deleted_rows = previous_set - current_set

    # Convert the deleted rows back into a list of dictionaries to display or use elsewhere
    deleted_rows_dicts = [dict(row) for row in deleted_rows]
    
    current_count = sum(item['Aantal'] for item in current_data) if current_data else 0
    previous_count = sum(item['Aantal'] for item in current_data) if previous_data else 0
    
    row_count = current_count
    header = f"TAART: {row_count}"
    
    # Initialize the alert message
    alert_msg = None

    if deleted_rows_dicts:
        # If there are deleted rows, process each one
        for deleted_row in deleted_rows_dicts:
            # Extract the ID of the deleted row
            deleted_id = deleted_row.get('Omschrijving', None)
            deleted_amount = deleted_row.get('Aantal', None)
            # print(deleted_id)
            if deleted_id:
                # Connect to the database and update the InStock status
                try:
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    delete_query = text("UPDATE [dbo].[TAART] SET [Aantal] = [Aantal] + :deleted_amount WHERE [Omschrijving] = :deleted_id")
                    db.execute(delete_query, {"deleted_amount": deleted_amount, "deleted_id": deleted_id})
                    
                    # Commit changes to the database
                    db.commit()
                    
                    db.close()
                    
                    alert_msg = dbc.Alert(f"Barcode {deleted_id} updated in database; set as in stock.", color="success")
                except Exception as e:
                    alert_msg = dbc.Alert(f"Failed to update barcode {deleted_id} in database: {str(e)}", color="danger")
            else:
               alert_msg = dbc.Alert("Deleted row did not have a valid ID.", color="danger")
    else:
        # If no rows have been deleted, return an appropriate message
        alert_msg = dbc.Alert("No rows have been deleted.", color="warning")

    return header, alert_msg, current_data

#%%%% DIVERSEN
@app.callback(
    [Output("diversen-header", "children", allow_duplicate=True),
     Output('barcode-status-diversen-page1', 'children'),
     Output('diversen-table-page1', 'data', allow_duplicate=True),
     Output('diversen-table-storage-page1', 'data', allow_duplicate=True),
     Output('barcode-input-diversen-page1', 'value'),
     Output('diversen-count-input-page1', 'value')],
    [Input('diversen-count-input-page1', 'n_submit'),
     State('barcode-input-diversen-page1', 'value'),
     State('diversen-count-input-page1', 'value'),
     State('diversen-table-page1', 'data')],
    prevent_initial_call=True,
)
def scan_barcode_diversen_page1(n_clicks, barcode_input, item_count_input, rows):
    
    if item_count_input is None:
        raise PreventUpdate  # No barcode entered, do nothing
    
    if rows is None:
        rows = []  # Initialize rows as an empty list if it's None
        
    if barcode_input is None:
        raise PreventUpdate  # No barcode entered, do nothing
    
    # Initialize the alert message
    alert_msg = None
    
    # Create a database session using SessionLocal
    db = SessionLocal()
    
    # Define the select query
    select_query = text("SELECT [Omschrijving], [Aantal] FROM [dbo].[DIVERSEN] WHERE [Barcode] = :barcode")
    
    # Execute the select query using SQLAlchemy
    result_select = db.execute(select_query, {"barcode": barcode_input}).fetchone()
    
    if result_select:
        
        # The barcode exists in the database and the item is in stock, update the status
        alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} found in database and item was in stock.', color="success")
        
        # Update input table
        if barcode_input is not None and item_count_input is not None:
            
            update_query = text("UPDATE [dbo].[DIVERSEN] SET [Aantal] = [Aantal] - :item_count WHERE [Barcode] = :barcode")
            result_update = db.execute(update_query, {"item_count": item_count_input, "barcode": barcode_input})
            
            # Fetch the updated row from the database
            updated_row = db.execute(select_query, {"barcode": barcode_input}).fetchone()

            omschrijving = updated_row[0]
            
            if rows:
                
                # Flag to keep track of whether the row was found in rows
                row_found = False
                
                # Check if the row exists in rows
                for row in rows:
                    if row['Omschrijving'] == omschrijving:
                        # Update the quantity in the existing row
                        row['Aantal'] += item_count_input
                        row_found = True  # Set the flag to True
                    
                # If the row was not found in rows, add a new row
                if not row_found:
                    new_row = {
                        'Omschrijving': omschrijving,
                        'Aantal': item_count_input,
                    }
                    rows.append(new_row)
            else:
                # There are no existing rows, so add a new row
                new_row = {
                    'Omschrijving': omschrijving,
                    'Aantal': item_count_input,
                }
                rows.append(new_row)
                
            # Commit changes to the database
            db.commit()
            
    else:
        # The barcode does not exist in the database or item is not in stock
        
        # Define the existence check query
        exists_query = text(
            "SELECT COUNT(*) FROM [dbo].[DIVERSEN] WHERE [Barcode] = :barcode"
        )
        
        # Execute the existence check query using SQLAlchemy
        exists = db.execute(exists_query, {"barcode": barcode_input}).fetchone()[0]

        if exists > 0:
            # The item exists but is out of stock
            alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} found in database but item is currently out of stock.', color="warning")
        else:
            # The item does not exist
            alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} not found in database.', color="danger")
    
    row_count = sum(row['Aantal'] for row in rows)
    header = f"DIVERSEN: {row_count}"
    
    # Close the database session
    db.close()
    
    return header, alert_msg, rows, rows, None, None
    

@app.callback(
    [Output("diversen-header", "children", allow_duplicate=True),
     Output('deleted-row-diversen-page1', 'children'),
     Output('diversen-table-storage-page1', 'data', allow_duplicate=True)],# You might need to add this component to your layout to display the deleted row information
    [Input('diversen-table-page1', 'data'),
     State('diversen-table-page1', 'data_previous')],
    prevent_initial_call=True,
)
def detect_deleted_row_diversen_page1(current_data, previous_data):
    if not dash.callback_context.triggered:
        # This is the initial load, no data has been deleted
        raise PreventUpdate

    if previous_data is None:
        # This can happen if there's no previous data to compare against
        raise PreventUpdate

    # Convert both lists of dictionaries (current and previous data) into sets of tuples for comparison
    current_set = {tuple(d.items()) for d in current_data} if current_data else set()
    previous_set = {tuple(d.items()) for d in previous_data} if previous_data else set()

    # Find the difference between the two sets; this will be the deleted row(s)
    deleted_rows = previous_set - current_set

    # Convert the deleted rows back into a list of dictionaries to display or use elsewhere
    deleted_rows_dicts = [dict(row) for row in deleted_rows]
    
    current_count = sum(item['Aantal'] for item in current_data) if current_data else 0
    previous_count = sum(item['Aantal'] for item in current_data) if previous_data else 0
    
    row_count = current_count
    header = f"DIVERSEN: {row_count}"
    
    # Initialize the alert message
    alert_msg = None

    if deleted_rows_dicts:
        # If there are deleted rows, process each one
        for deleted_row in deleted_rows_dicts:
            # Extract the ID of the deleted row
            deleted_id = deleted_row.get('Omschrijving', None)
            deleted_amount = deleted_row.get('Aantal', None)
            # print(deleted_id)
            if deleted_id:
                # Connect to the database and update the InStock status
                try:
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    delete_query = text("UPDATE [dbo].[DIVERSEN] SET [Aantal] = [Aantal] + :deleted_amount WHERE [Omschrijving] = :deleted_id")
                    db.execute(delete_query, {"deleted_amount": deleted_amount, "deleted_id": deleted_id})
                    
                    # Commit changes to the database
                    db.commit()
                    
                    db.close()
                    
                    alert_msg = dbc.Alert(f"Barcode {deleted_id} updated in database; set as in stock.", color="success")
                except Exception as e:
                    alert_msg = dbc.Alert(f"Failed to update barcode {deleted_id} in database: {str(e)}", color="danger")
            else:
               alert_msg = dbc.Alert("Deleted row did not have a valid ID.", color="danger")
    else:
        # If no rows have been deleted, return an appropriate message
        alert_msg = dbc.Alert("No rows have been deleted.", color="warning")

    return header, alert_msg, current_data

#%%%% SUIKERVRIJ
@app.callback(
    [Output("suikervrij-header", "children", allow_duplicate=True),
     Output('barcode-status-suikervrij-page1', 'children'),
     Output('suikervrij-table-page1', 'data', allow_duplicate=True),
     Output('suikervrij-table-storage-page1', 'data', allow_duplicate=True),
     Output('barcode-input-suikervrij-page1', 'value'),
     Output('suikervrij-count-input-page1', 'value')],
    [Input('suikervrij-count-input-page1', 'n_submit'),
     State('barcode-input-suikervrij-page1', 'value'),
     State('suikervrij-count-input-page1', 'value'),
     State('suikervrij-table-page1', 'data')],
    prevent_initial_call=True,
)
def scan_barcode_suikervrij_page1(n_clicks, barcode_input, item_count_input, rows):
    
    if item_count_input is None:
        raise PreventUpdate  # No barcode entered, do nothing
    
    if rows is None:
        rows = []  # Initialize rows as an empty list if it's None
        
    if barcode_input is None:
        raise PreventUpdate  # No barcode entered, do nothing
    
    # Initialize the alert message
    alert_msg = None
    
    # Create a database session using SessionLocal
    db = SessionLocal()
    
    # Define the select query
    select_query = text("SELECT [Omschrijving], [Aantal] FROM [dbo].[SUIKERVRIJ] WHERE [Barcode] = :barcode")
    
    # Execute the select query using SQLAlchemy
    result_select = db.execute(select_query, {"barcode": barcode_input}).fetchone()
    
    if result_select:
        
        # The barcode exists in the database and the item is in stock, update the status
        alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} found in database and item was in stock.', color="success")
        
        # Update input table
        if barcode_input is not None and item_count_input is not None:
            
            update_query = text("UPDATE [dbo].[SUIKERVRIJ] SET [Aantal] = [Aantal] - :item_count WHERE [Barcode] = :barcode")
            result_update = db.execute(update_query, {"item_count": item_count_input, "barcode": barcode_input})
            
            # Fetch the updated row from the database
            updated_row = db.execute(select_query, {"barcode": barcode_input}).fetchone()

            omschrijving = updated_row[0]
            
            if rows:
                
                # Flag to keep track of whether the row was found in rows
                row_found = False
                
                # Check if the row exists in rows
                for row in rows:
                    if row['Omschrijving'] == omschrijving:
                        # Update the quantity in the existing row
                        row['Aantal'] += item_count_input
                        row_found = True  # Set the flag to True
                    
                # If the row was not found in rows, add a new row
                if not row_found:
                    new_row = {
                        'Omschrijving': omschrijving,
                        'Aantal': item_count_input,
                    }
                    rows.append(new_row)
            else:
                # There are no existing rows, so add a new row
                new_row = {
                    'Omschrijving': omschrijving,
                    'Aantal': item_count_input,
                }
                rows.append(new_row)
                
            # Commit changes to the database
            db.commit()
            
    else:
        # The barcode does not exist in the database or item is not in stock
        
        # Define the existence check query
        exists_query = text(
            "SELECT COUNT(*) FROM [dbo].[SUIKERVRIJ] WHERE [Barcode] = :barcode"
        )
        
        # Execute the existence check query using SQLAlchemy
        exists = db.execute(exists_query, {"barcode": barcode_input}).fetchone()[0]

        if exists > 0:
            # The item exists but is out of stock
            alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} found in database but item is currently out of stock.', color="warning")
        else:
            # The item does not exist
            alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} not found in database.', color="danger")
    
    row_count = sum(row['Aantal'] for row in rows)
    header = f"SUIKERVRIJ: {row_count}"
    
    # Close the database session
    db.close()
    
    return header, alert_msg, rows, rows, None, None
    
@app.callback(
    [Output("suikervrij-header", "children", allow_duplicate=True),
     Output('deleted-row-suikervrij-page1', 'children'),
     Output('suikervrij-table-storage-page1', 'data', allow_duplicate=True)],# You might need to add this component to your layout to display the deleted row information
    [Input('suikervrij-table-page1', 'data'),
     State('suikervrij-table-page1', 'data_previous')],
    prevent_initial_call=True,
)
def detect_deleted_row_suikervrij_page1(current_data, previous_data):
    if not dash.callback_context.triggered:
        # This is the initial load, no data has been deleted
        raise PreventUpdate

    if previous_data is None:
        # This can happen if there's no previous data to compare against
        raise PreventUpdate

    # Convert both lists of dictionaries (current and previous data) into sets of tuples for comparison
    current_set = {tuple(d.items()) for d in current_data} if current_data else set()
    previous_set = {tuple(d.items()) for d in previous_data} if previous_data else set()

    # Find the difference between the two sets; this will be the deleted row(s)
    deleted_rows = previous_set - current_set

    # Convert the deleted rows back into a list of dictionaries to display or use elsewhere
    deleted_rows_dicts = [dict(row) for row in deleted_rows]
    
    current_count = sum(item['Aantal'] for item in current_data) if current_data else 0
    previous_count = sum(item['Aantal'] for item in current_data) if previous_data else 0
    
    row_count = current_count
    header = f"SUIKERVRIJ: {row_count}"
    
    # Initialize the alert message
    alert_msg = None

    if deleted_rows_dicts:
        # If there are deleted rows, process each one
        for deleted_row in deleted_rows_dicts:
            # Extract the ID of the deleted row
            deleted_id = deleted_row.get('Omschrijving', None)
            deleted_amount = deleted_row.get('Aantal', None)
            # print(deleted_id)
            if deleted_id:
                # Connect to the database and update the InStock status
                try:
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    delete_query = text("UPDATE [dbo].[SUIKERVRIJ] SET [Aantal] = [Aantal] + :deleted_amount WHERE [Omschrijving] = :deleted_id")
                    db.execute(delete_query, {"deleted_amount": deleted_amount, "deleted_id": deleted_id})
                    
                    # Commit changes to the database
                    db.commit()
                    
                    db.close()
                    
                    alert_msg = dbc.Alert(f"Barcode {deleted_id} updated in database; set as in stock.", color="success")
                except Exception as e:
                    alert_msg = dbc.Alert(f"Failed to update barcode {deleted_id} in database: {str(e)}", color="danger")
            else:
               alert_msg = dbc.Alert("Deleted row did not have a valid ID.", color="danger")
    else:
        # If no rows have been deleted, return an appropriate message
        alert_msg = dbc.Alert("No rows have been deleted.", color="warning")

    return header, alert_msg, current_data

#%%%% GEBAK
@app.callback(
    [Output("gebak-header", "children", allow_duplicate=True),
     Output('barcode-status-gebak-page1', 'children'),
     Output('gebak-table-page1', 'data', allow_duplicate=True),
     Output('gebak-table-storage-page1', 'data', allow_duplicate=True),
     Output('barcode-input-gebak-page1', 'value'),
     Output('gebak-count-input-page1', 'value')],
    [Input('gebak-count-input-page1', 'n_submit'),
     State('barcode-input-gebak-page1', 'value'),
     State('gebak-count-input-page1', 'value'),
     State('gebak-table-page1', 'data')],
    prevent_initial_call=True,
)
def scan_barcode_gebak_page1(n_clicks, barcode_input, item_count_input, rows):
    
    if item_count_input is None:
        raise PreventUpdate  # No barcode entered, do nothing
        
    if rows is None:
        rows = []  # Initialize rows as an empty list if it's None
        
    if barcode_input is None:
        raise PreventUpdate  # No barcode entered, do nothing
    
    # Initialize the alert message
    alert_msg = None
    
    # Create a database session using SessionLocal
    db = SessionLocal()
    
    # Define the select query
    select_query = text("SELECT [Omschrijving], [Aantal] FROM [dbo].[GEBAK] WHERE [Barcode] = :barcode")
    
    # Execute the select query using SQLAlchemy
    result_select = db.execute(select_query, {"barcode": barcode_input}).fetchone()
    
    if result_select:
        
        # The barcode exists in the database and the item is in stock, update the status
        alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} found in database and item was in stock.', color="success")
        
        # Update input table
        if barcode_input is not None and item_count_input is not None:
            
            update_query = text("UPDATE [dbo].[GEBAK] SET [Aantal] = [Aantal] - :item_count WHERE [Barcode] = :barcode")
            result_update = db.execute(update_query, {"item_count": item_count_input, "barcode": barcode_input})
            
            # Fetch the updated row from the database
            updated_row = db.execute(select_query, {"barcode": barcode_input}).fetchone()

            omschrijving = updated_row[0]
            
            if rows:
                
                # Flag to keep track of whether the row was found in rows
                row_found = False
                
                # Check if the row exists in rows
                for row in rows:
                    if row['Omschrijving'] == omschrijving:
                        # Update the quantity in the existing row
                        row['Aantal'] += item_count_input
                        row_found = True  # Set the flag to True
                    
                # If the row was not found in rows, add a new row
                if not row_found:
                    new_row = {
                        'Omschrijving': omschrijving,
                        'Aantal': item_count_input,
                    }
                    rows.append(new_row)
            else:
                # There are no existing rows, so add a new row
                new_row = {
                    'Omschrijving': omschrijving,
                    'Aantal': item_count_input,
                }
                rows.append(new_row)
                
            # Commit changes to the database
            db.commit()
            
    else:
        # The barcode does not exist in the database or item is not in stock
        
        # Define the existence check query
        exists_query = text(
            "SELECT COUNT(*) FROM [dbo].[GEBAK] WHERE [Barcode] = :barcode"
        )
        
        # Execute the existence check query using SQLAlchemy
        exists = db.execute(exists_query, {"barcode": barcode_input}).fetchone()[0]

        if exists > 0:
            # The item exists but is out of stock
            alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} found in database but item is currently out of stock.', color="warning")
        else:
            # The item does not exist
            alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} not found in database.', color="danger")
    
    row_count = sum(row['Aantal'] for row in rows)
    header = f"GEBAK: {row_count}"
    
    # Close the database session
    db.close()
    
    return header, alert_msg, rows, rows, None, None
    

@app.callback(
    [Output("gebak-header", "children", allow_duplicate=True),
     Output('deleted-row-gebak-page1', 'children'),
     Output('gebak-table-storage-page1', 'data', allow_duplicate=True)],# You might need to add this component to your layout to display the deleted row information
    [Input('gebak-table-page1', 'data'),
     State('gebak-table-page1', 'data_previous')],
    prevent_initial_call=True,
)
def detect_deleted_row_gebak_page1(current_data, previous_data):
    if not dash.callback_context.triggered:
        # This is the initial load, no data has been deleted
        raise PreventUpdate

    if previous_data is None:
        # This can happen if there's no previous data to compare against
        raise PreventUpdate

    # Convert both lists of dictionaries (current and previous data) into sets of tuples for comparison
    current_set = {tuple(d.items()) for d in current_data} if current_data else set()
    previous_set = {tuple(d.items()) for d in previous_data} if previous_data else set()

    # Find the difference between the two sets; this will be the deleted row(s)
    deleted_rows = previous_set - current_set

    # Convert the deleted rows back into a list of dictionaries to display or use elsewhere
    deleted_rows_dicts = [dict(row) for row in deleted_rows]
    
    current_count = sum(item['Aantal'] for item in current_data) if current_data else 0
    previous_count = sum(item['Aantal'] for item in current_data) if previous_data else 0
    
    row_count = current_count
    header = f"GEBAK: {row_count}"
    
    # Initialize the alert message
    alert_msg = None

    if deleted_rows_dicts:
        # If there are deleted rows, process each one
        for deleted_row in deleted_rows_dicts:
            # Extract the ID of the deleted row
            deleted_id = deleted_row.get('Omschrijving', None)
            deleted_amount = deleted_row.get('Aantal', None)
            # print(deleted_id)
            if deleted_id:
                # Connect to the database and update the InStock status
                try:
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    delete_query = text("UPDATE [dbo].[GEBAK] SET [Aantal] = [Aantal] + :deleted_amount WHERE [Omschrijving] = :deleted_id")
                    db.execute(delete_query, {"deleted_amount": deleted_amount, "deleted_id": deleted_id})
                    
                    # Commit changes to the database
                    db.commit()
                    
                    db.close()
                    
                    alert_msg = dbc.Alert(f"Barcode {deleted_id} updated in database; set as in stock.", color="success")
                except Exception as e:
                    alert_msg = dbc.Alert(f"Failed to update barcode {deleted_id} in database: {str(e)}", color="danger")
            else:
               alert_msg = dbc.Alert("Deleted row did not have a valid ID.", color="danger")
    else:
        # If no rows have been deleted, return an appropriate message
        alert_msg = dbc.Alert("No rows have been deleted.", color="warning")

    return header, alert_msg, current_data

#%%%% POTJES
@app.callback(
    [Output("potjes-header", "children", allow_duplicate=True),
     Output('barcode-status-potjes-page1', 'children'),
     Output('potjes-table-page1', 'data', allow_duplicate=True),
     Output('potjes-table-storage-page1', 'data', allow_duplicate=True),
     Output('barcode-input-potjes-page1', 'value'),
     Output('potjes-count-input-page1', 'value')],
    [Input('potjes-count-input-page1', 'n_submit'),
     State('barcode-input-potjes-page1', 'value'),
     State('potjes-count-input-page1', 'value'),
     State('potjes-table-page1', 'data')],
    prevent_initial_call=True,
)
def scan_barcode_potjes_page1(n_clicks, barcode_input, item_count_input, rows):
    
    if item_count_input is None:
        raise PreventUpdate  # No barcode entered, do nothing
    
    if rows is None:
        rows = []  # Initialize rows as an empty list if it's None
        
    if barcode_input is None:
        raise PreventUpdate  # No barcode entered, do nothing
    
    # Initialize the alert message
    alert_msg = None
    
    # Create a database session using SessionLocal
    db = SessionLocal()
    
    # Define the select query
    select_query = text("SELECT [Omschrijving], [Aantal] FROM [dbo].[POTJES] WHERE [Barcode] = :barcode")
    
    # Execute the select query using SQLAlchemy
    result_select = db.execute(select_query, {"barcode": barcode_input}).fetchone()
    
    if result_select:
        
        # The barcode exists in the database and the item is in stock, update the status
        alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} found in database and item was in stock.', color="success")
        
        # Update input table
        if barcode_input is not None and item_count_input is not None:
            
            update_query = text("UPDATE [dbo].[POTJES] SET [Aantal] = [Aantal] - :item_count WHERE [Barcode] = :barcode")
            result_update = db.execute(update_query, {"item_count": item_count_input, "barcode": barcode_input})
            
            # Fetch the updated row from the database
            updated_row = db.execute(select_query, {"barcode": barcode_input}).fetchone()

            omschrijving = updated_row[0]
            
            if rows:
                
                # Flag to keep track of whether the row was found in rows
                row_found = False
                
                # Check if the row exists in rows
                for row in rows:
                    if row['Omschrijving'] == omschrijving:
                        # Update the quantity in the existing row
                        row['Aantal'] += item_count_input
                        row_found = True  # Set the flag to True
                    
                # If the row was not found in rows, add a new row
                if not row_found:
                    new_row = {
                        'Omschrijving': omschrijving,
                        'Aantal': item_count_input,
                    }
                    rows.append(new_row)
            else:
                # There are no existing rows, so add a new row
                new_row = {
                    'Omschrijving': omschrijving,
                    'Aantal': item_count_input,
                }
                rows.append(new_row)
                
            # Commit changes to the database
            db.commit()
            
    else:
        # The barcode does not exist in the database or item is not in stock
        
        # Define the existence check query
        exists_query = text(
            "SELECT COUNT(*) FROM [dbo].[POTJES] WHERE [Barcode] = :barcode"
        )
        
        # Execute the existence check query using SQLAlchemy
        exists = db.execute(exists_query, {"barcode": barcode_input}).fetchone()[0]

        if exists > 0:
            # The item exists but is out of stock
            alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} found in database but item is currently out of stock.', color="warning")
        else:
            # The item does not exist
            alert_msg = dbc.Alert(f'Barcode {str(barcode_input)} not found in database.', color="danger")
    
    row_count = sum(row['Aantal'] for row in rows)
    header = f"POTJES: {row_count}"
    
    # Close the database session
    db.close()
    
    return header, alert_msg, rows, rows, None, None
    
@app.callback(
    [Output("potjes-header", "children", allow_duplicate=True),
     Output('deleted-row-potjes-page1', 'children'),
     Output('potjes-table-storage-page1', 'data', allow_duplicate=True)],# You might need to add this component to your layout to display the deleted row information
    [Input('potjes-table-page1', 'data'),
     State('potjes-table-page1', 'data_previous')],
    prevent_initial_call=True,
)
def detect_deleted_row_potjes_page1(current_data, previous_data):
    if not dash.callback_context.triggered:
        # This is the initial load, no data has been deleted
        raise PreventUpdate

    if previous_data is None:
        # This can happen if there's no previous data to compare against
        raise PreventUpdate

    # Convert both lists of dictionaries (current and previous data) into sets of tuples for comparison
    current_set = {tuple(d.items()) for d in current_data} if current_data else set()
    previous_set = {tuple(d.items()) for d in previous_data} if previous_data else set()

    # Find the difference between the two sets; this will be the deleted row(s)
    deleted_rows = previous_set - current_set

    # Convert the deleted rows back into a list of dictionaries to display or use elsewhere
    deleted_rows_dicts = [dict(row) for row in deleted_rows]
    
    current_count = sum(item['Aantal'] for item in current_data) if current_data else 0
    previous_count = sum(item['Aantal'] for item in current_data) if previous_data else 0
    
    row_count = current_count
    header = f"POTJES: {row_count}"
    
    # Initialize the alert message
    alert_msg = None

    if deleted_rows_dicts:
        # If there are deleted rows, process each one
        for deleted_row in deleted_rows_dicts:
            # Extract the ID of the deleted row
            deleted_id = deleted_row.get('Omschrijving', None)
            deleted_amount = deleted_row.get('Aantal', None)
            # print(deleted_id)
            if deleted_id:
                # Connect to the database and update the InStock status
                try:
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    delete_query = text("UPDATE [dbo].[POTJES] SET [Aantal] = [Aantal] + :deleted_amount WHERE [Omschrijving] = :deleted_id")
                    db.execute(delete_query, {"deleted_amount": deleted_amount, "deleted_id": deleted_id})
                    
                    # Commit changes to the database
                    db.commit()
                    
                    db.close()
                    
                    alert_msg = dbc.Alert(f"Barcode {deleted_id} updated in database; set as in stock.", color="success")
                except Exception as e:
                    alert_msg = dbc.Alert(f"Failed to update barcode {deleted_id} in database: {str(e)}", color="danger")
            else:
               alert_msg = dbc.Alert("Deleted row did not have a valid ID.", color="danger")
    else:
        # If no rows have been deleted, return an appropriate message
        alert_msg = dbc.Alert("No rows have been deleted.", color="warning")

    return header, alert_msg, current_data

#%%%% GENERATE PAKBON PDF

@app.callback(
    Output('generate-pdf-button', 'disabled'),
    [Input('generate-pdf-button', 'n_clicks')]
)
def disable_button(n_clicks):
    if n_clicks > 0:
        # print('a', n_clicks)
        return True
    return False

# Combined Callback for generating and mailing pdf
@callback(
    [Output('generate-pdf-button', 'disabled', allow_duplicate=True),
     Output('note', 'value'),
     Output('pdf-generation-status', 'children'),  # For the status message
     Output('ijs-table-page1', 'data', allow_duplicate=True),
     Output('taart-table-page1', 'data', allow_duplicate=True),
     Output('diversen-table-page1', 'data', allow_duplicate=True),
     Output('suikervrij-table-page1', 'data', allow_duplicate=True),
     Output('gebak-table-page1', 'data', allow_duplicate=True),
     Output('potjes-table-page1', 'data', allow_duplicate=True),
     ],  # To clear the table data
    [Input('generate-pdf-button', 'n_clicks')],
    [State('store-dropdown', 'value'),
     State('ijs-table-page1', 'data'),
     State('taart-table-page1', 'data'),
     State('diversen-table-page1', 'data'),
     State('suikervrij-table-page1', 'data'),
     State('gebak-table-page1', 'data'),
     State('potjes-table-page1', 'data'),
     State('note', 'value')],
    prevent_initial_call=True, # Prevents the callback from running when the page loads
)
def generate_and_email_pdf(n_clicks, store, products, taarten, diversen, suikervrij, gebak, potjes, note):
    
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate
    
    if not any([products, taarten, diversen, suikervrij, gebak, potjes]):
        return False, None, dbc.Alert("Please add products before generating a PDF.", color="warning"), [], [], [], [], [], []
    
    if n_clicks is not None and n_clicks > 0:
        
        # print('b', n_clicks)
        
        store_label = next((item['label'] for item in stores if item['value'] == store), None)
        if not store_label:
            return False, None, dbc.Alert("Please select a store.", color="danger"), products, taarten, diversen, suikervrij, gebak, potjes
    
        # Get the current date
        current_datetime = datetime.datetime.now()
    
        # Format the date as yy-mm-dd
        formatted_date1 = current_datetime.strftime('%Y-%m-%d')
        formatted_date2 = current_datetime.strftime('%Y%m%d')
        formatted_date3 = current_datetime.strftime('%Y%m%d_%H%M%S')
        # raw_formatted_date1 = str(formatted_date1)
    
        # Format the date and time as yyyy-mm-dd HH:MM:SS
        formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        # Define the path to the folder where you want to save the PDFs
        pdf_folder = 'Orders_Pdfs'
        
        # Define PDF filename based on the store name for uniqueness
        pdf_filename = f'{store}_{formatted_date3}.pdf'
        
        # Set up the PDF document
        doc = SimpleDocTemplate(pdf_filename, pagesize=A4, rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        elements = []
        styles = getSampleStyleSheet()
        
        # Customize the Title style for the invoice
        styles['Title'].alignment = 0  # 0 is left-aligned, 1 is centered. Change as needed.
        styles['Heading1'].alignment = 0  # Left align the body text
        styles['Heading2'].alignment = 0  # Left align the body text
        styles['Heading3'].alignment = 0  # Left align the body text
        styles['BodyText'].alignment = 0  # Left align the body text
        
        
        # Add content to the PDF - starting with the store title
        # title = Paragraph(f'Store: {store}', styles['Title'])
        title = Paragraph(f'Pakbon {store_label} {formatted_date1}', styles['Title'])
        elements.append(title)
        # elements.append(Spacer(1, 5))  # Add a space after the title
        
        # Adding a paragraph to describe the invoice, if necessary
        description = Paragraph(f'Datum en tijd: {formatted_datetime}', styles['BodyText'])
        elements.append(description)
        # elements.append(Spacer(1, 5))  # Space between description and table
    
        tables = [(products, "IJS"), 
                  (taarten, "TAART"), 
                  (diversen, "DIVERSEN"),
                  (suikervrij, "SUIKERVRIJ"),
                  (gebak, "GEBAK"),
                  (potjes, "POTJES"),
                  ]
    
        for table in tables:
    
            table_data = table[0]
            table_name = table[1]
            
            if table_data:
                
                title = Paragraph(table_name, styles['Heading2'])
                
                special_count = None
                
                if table_name == "IJS":
                    # Setting up the table for product listing
                    data = [['Barcode', 'Type', 'Omschrijving', 'Gewicht [kg]']] + [[p['Barcode'], p['Type'], p['Omschrijving'], p['Gewicht [kg]']] for p in table_data]
                    table = Table(data, colWidths=[100, 60, 150, 75])  # Specify column widths as needed
                    
                    # Calculate totals for each type
                    # Initialize dictionaries to store totals
                    type_count = {}
                    type_weight = {}
                    
                    if products:
                        for product in products:
                            product_type = product['Type'].lower()
                            if product_type not in type_count:
                                type_count[product_type] = 1
                                type_weight[product_type] = product['Gewicht [kg]']
                            else:
                                type_count[product_type] += 1
                                type_weight[product_type] += product['Gewicht [kg]']
                        
                        # Add totals table to the PDF
                        type_totals_data = [['Type', 'Aantal', 'Totaal Gewicht [kg]']]
                        for product_type, count in type_count.items():
                            type_totals_data.append([product_type, count, round(type_weight[product_type], 2)])
                        
                        # Adding a paragraph to describe the totals table
                        total_products = len(products)
                        table_total_footer = Paragraph(f'Totaal {table_name}: {total_products}', styles['Heading3'])
                        totals_description = Paragraph("", styles['Heading2'])
                   
                        # Setting up the table for totals
                        totals_table = Table(type_totals_data, colWidths=[100, 60, 100])  # Specify column widths as needed
                        totals_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                            ('ALIGNMENT', (0, 0), (-1, -1), 'LEFT'),  # Align text to the left
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                            ('BOX', (0, 0), (-1, -1), 2, colors.black),
                        ]))
                        totals_table.hAlign = 'LEFT'  # Options are 'LEFT', 'CENTER', 'RIGHT'
                        totals_table_pack = KeepTogether([totals_description, totals_table, table_total_footer])
                        
                else:
                    
                    # Setting up the table for product listing
                    data = [['Omschrijving', 'Aantal']] + [[p['Omschrijving'], p['Aantal']] for p in table_data]
                    table = Table(data, colWidths=[150, 60])  # Specify column widths as needed
                    
                    table_total = sum(item['Aantal'] for item in table_data)
                    # table_total_footer = Paragraph(f'Totaal {table_name}: {table_total}', styles['Heading3'])
                    
                    if table_name == "TAART":
                        special_count = next((item['Aantal'] for item in table_data if 'Speciaal bestelde ijstaart' in item['Omschrijving']), None)
                        
                        special_table_total_footer = Paragraph(f'Totaal SPECIAL {table_name}: {special_count}', styles['Heading3'])
                    
                    table_total = table_total - special_count if special_count else table_total
                    table_total_footer = Paragraph(f'Totaal {table_name}: {table_total}', styles['Heading3'])
                        
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.white),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGNMENT', (0,0), (-1,-1), 'LEFT'),  # Align text to the left
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('GRID', (0,0), (-1,-1), 1, colors.black),
                    ('BOX', (0,0), (-1,-1), 2, colors.black),
                ]))
                table.hAlign = 'LEFT'  # Options are 'LEFT', 'CENTER', 'RIGHT'
                
                if table_name == "IJS":
                    elements.append(title)
                    elements.append(table)
                    
                else:
                    table_pack = KeepTogether([title, table, table_total_footer, special_table_total_footer]) if special_count else KeepTogether([title, table, table_total_footer])
                    elements.append(table_pack)
                
                if table_name == "IJS":
                    elements.append(totals_table_pack)
                
        # Add note to the PDF
        if note:
            note_header = Paragraph('Opmerking', styles['Heading3'])
            note_paragraph = Paragraph(f'{note}', styles['BodyText'])
            note_complete = KeepTogether([note_header, note_paragraph])
            elements.append(note_complete)
            
        # Build the PDF
        doc.build(elements)
    
        if store and (products or taarten or diversen or suikervrij or gebak or potjes):
            
            try:
                # Create a database session using SessionLocal
                db = SessionLocal()
                
                # Iterate over each product and insert it into the database
                for product in products:
                    barcode_order = product['Barcode']
                    description_order = product['Omschrijving'],
                    description_order = description_order[0].strip('()')
                    
                    insert_query = text(f"INSERT INTO [dbo].[ORDERS] (Barcode, Omschrijving, Winkel, [Order Datum]) VALUES ('{barcode_order}','{description_order}','{store_label}','{formatted_date1}')")
                    db.execute(insert_query)
                
                # Commit the transaction
                db.commit()
                
                # Close the database session
                db.close()
            
            except Exception as e:
                print(f"Error putting products in dbo.ORDERS: {e}")
                
            # Move the file
            try:
                # Construct the destination path
                destination_path = os.path.join(pdf_folder, pdf_filename)
                
                # If the file already exists in the destination folder, remove it
                if os.path.exists(destination_path):
                    os.remove(destination_path)
                    print(f"Bestaande pakbon verwijderd: {destination_path}")

                # Move the file to the destination folder
                shutil.move(pdf_filename, pdf_folder)
                print(f"Pakbon {store}_{formatted_date3} geplaatst in {pdf_folder}")

            except Exception as e:
                print(f"Error moving file: {e}")
                
            
            # After sending the email successfully
            try:
                # send_email(
                #     f"Pakbon {store} {formatted_date1}",
                #     "Hier is een PDF van de pakbon doorgestuurd vanuit Luciano Voorraad Beheer.",
                #     "luukaltenburg@gmail.com",  # Replace with actual recipient's email
                #     os.path.join(pdf_folder, pdf_filename)
                # )
                
                store_id = store_library[store_label]
                new_entry = [
                    f'{store}_{formatted_date3}',     # Order ID
                    f'{store_id}',    # Customer ID
                    f'{formatted_date1}',   # Order Date
                    "FALSE",      # Status
                    f"Orders_Pdfs/{store}_{formatted_date3}.pdf",  # File
                    "",  # Signature
                    "",   # Timestamp
                    "",  # Note
                    "FALSE", # Rekening?
                ]
                
                write_data_to_appsheet(new_entry)
                
                upload_pdf_to_drive(destination_path)

                # Return success message and empty the table
                return False, None, dbc.Alert(f"Pakbon {store_label} {formatted_date1} generated and uploaded to the app!", color="success"), [], [], [], [], [], []
            except Exception as e:
                # Return error message and keep the table data unchanged
                return False, None, dbc.Alert(f"An error occurred: {str(e)}", color="danger"), [], [], [], [], [], []
        else:
            # Alerts for missing information, keep the table data unchanged
            alert_msg = "Please select a store and add products before generating a Pakbon."
            if store:
                alert_msg = "Please add products before generating a Pakbon."
            elif products:
                alert_msg = "Please select a store before generating a Pakbon."
                return False, None, dbc.Alert(alert_msg, color="warning")

#%%% CALLBACKS PAGE 2  [IJS]
# Callback to populate the stock overview table on Page 2
@app.callback(
    [Output("stock-ijs-header", "children"),
     Output('supply-timestamp-ijs-page2', 'children'),
     Output('stock-table-ijs', 'data'),
     Output('stock-count-table-ijs', 'data')],
    [Input('url', 'pathname')],
) 
def show_stock_table_ijs(pathname):
    if pathname == '/ijs':
        try:
            # Create a database session using SessionLocal
            db = SessionLocal()
            
            # df_products_page2 = pd.DataFrame(columns=['Barcode', 'Omschrijving', 'Gewicht [kg]', 'Type', 'THT', 'Medewerker'])
            
            # Execute the query using SQLAlchemy
            # query = "SELECT [WgtDateTime], [ID], [Scale], [Description], [ValueNet], [Type] FROM [dbo].[DATA] WHERE [InStock] = 1"
            query = "SELECT [DATA01] as Barcode, [DATA02] as Omschrijving, [ValueNet] as Gewicht, [DATA03] as Type, [DATA04] as THT, [DATA05] as Medewerker, [WgtDate] as Weegdatum FROM [dbo].[DATA] WHERE [DATA06] = 1"
            stock_df = pd.read_sql(query, db.bind)
            
            # Fetch barcodes from ORDERS table
            query_orders = "SELECT [Barcode] FROM [dbo].[ORDERS]"
            orders_df = pd.read_sql(query_orders, db.bind)
            
            # Check if barcodes in DATA table also exist in ORDERS table
            common_barcodes = set(stock_df['Barcode']).intersection(set(orders_df['Barcode']))
            
            # Update rows in DATA table where Barcode exists in both tables
            if common_barcodes:
                for common_barcode in common_barcodes:
                    query = text("UPDATE [dbo].[DATA] SET [DATA06] = 0 WHERE [DATA01] = :common_barcode").params(common_barcode=common_barcode)
                    result = db.execute(query)
                db.commit()
                
            row_count = stock_df.shape[0]
            header = f"VOORRAAD: {row_count} bakken"
            
            # Group by Description and calculate the count
            count_df = stock_df.groupby('Omschrijving').size().reset_index(name='Aantal')

            # Convert DataFrame to dictionary and return data
            stock_data = stock_df.to_dict('records')
            
            count_data = count_df.to_dict('records')
            
            write_data_to_supply_sheet("IJS", count_df)
            
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            alert_msg = dbc.Alert(formatted_datetime, color="primary")
            
            return header, alert_msg, stock_data, count_data
        
        except Exception as e:
            logging.error("Error fetching data:", e)  # Consider using logging for error messages
            return None, [], []  # Return empty list or display an error message
        finally:
            # Ensure session is closed even on exceptions
            db.close()
    raise PreventUpdate  # Don't update if not on Page 2
    
    
@app.callback(
    [Output("stock-ijs-header", "children", allow_duplicate=True),
     Output('supply-timestamp-ijs-page2', 'children', allow_duplicate=True),
     Output('barcode-status-ijs-page2', 'children'),
     Output('stock-table-ijs', 'data', allow_duplicate=True),
     Output('stock-count-table-ijs', 'data', allow_duplicate=True),
     Output('barcode-input-ijs-page2', 'value'),
     Output('barcode-output-ijs-page2', 'value')],
    [Input('barcode-input-ijs-page2', 'n_submit'),
      Input('barcode-output-ijs-page2', 'n_submit'),
      State('barcode-input-ijs-page2', 'value'),
      State('barcode-output-ijs-page2', 'value')],
    prevent_initial_call=True,
)
def scan_barcode_ijs_page2(dummy1, dummy2, barcode_input, barcode_output):
    if barcode_input is None and barcode_output is None:
        raise PreventUpdate  # No barcode entered, do nothing

    try:
        
        # Initialize the alert message
        alerts = []
        
        # Create a database session
        db = SessionLocal()
        
        
        # Update barcode status (if input is not None)
        if barcode_input:
            
            # Fetch the specific barcode from the ORDERS table
            query_specific_barcode = f"SELECT [Barcode] FROM [dbo].[ORDERS] WHERE [Barcode] = '{barcode_input}'"
            specific_barcode_df = pd.read_sql(query_specific_barcode, db.bind)
            
            barcode_input = ''.join(char for char in barcode_input if char != ' ')
            
            # Check if the specific barcode exists in the ORDERS table
            if not specific_barcode_df.empty:
                alerts.append(dbc.Alert(f'Barcode {barcode_input} already ordered.', color="warning"))
                query = text("UPDATE [dbo].[DATA] SET [DATA06] = 0 WHERE [DATA01] = :barcode").params(barcode=barcode_input)
                result = db.execute(query)
            else:
                query = text("UPDATE [dbo].[DATA] SET [DATA06] = 1 WHERE [DATA01] = :barcode").params(barcode=barcode_input)
                result = db.execute(query)
                
                if result.rowcount == 0:
                    alerts.append(dbc.Alert(f'Barcode {barcode_input} not in database.', color="danger"))
                else:
                    alerts.append(dbc.Alert(f'Barcode {barcode_input} found in database and set to in stock.', color="success"))
            
            db.commit()
                
            # db.execute(query)
            # alerts.append(dbc.Alert(f'Barcode {barcode_input} found in database and set to in stock.', color="success"))
            # db.commit()

        # Update barcode status (if output is not None)
        if barcode_output:
            barcode_output = ''.join(char for char in barcode_output if char != ' ')
            query = text("UPDATE [dbo].[DATA] SET [DATA06] = 0 WHERE [DATA01] = :barcode").params(barcode=barcode_output)
            result = db.execute(query)
            if result.rowcount == 0:
                alerts.append(dbc.Alert(f'Barcode {barcode_output} not found in database.', color="danger"))
            else:
                alerts.append(dbc.Alert(f'Barcode {barcode_output} found in database and set out of stock.', color="success"))
                db.commit()
                
            # db.execute(query)
            # alerts.append(dbc.Alert(f'Barcode {barcode_output} found in database and set out of stock.', color="success"))
            # db.commit()

        # Get updated data for the DataTable
        query = "SELECT [DATA01] as Barcode, [DATA02] as Omschrijving, [ValueNet] as Gewicht, [DATA03] as Type, [DATA04] as THT, [DATA05] as Medewerker, [WgtDate] as Weegdatum FROM [dbo].[DATA] WHERE [DATA06] = 1"
        stock_df = pd.read_sql(query, db.bind)
        
        row_count = stock_df.shape[0]
        
        header = f"VOORRAAD: {row_count} bakken"
        # Group by Description and calculate the count
        count_df = stock_df.groupby('Omschrijving').size().reset_index(name='Aantal')
        
        stock_data = stock_df.to_dict('records')
        
        count_data = count_df.to_dict('records')
        
        write_data_to_supply_sheet("IJS", count_df)
        
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            
        alert_msg = dbc.Alert(formatted_datetime, color="primary")

    except Exception as e:
        logging.error("Error fetching or updating data:", e)
        # Handle errors gracefully (e.g., display an error message)
        return None, None, None, None, None, None, None  # Example for resetting all outputs on error

    finally:
        # Close the session even on exceptions
        db.close()

    return header, alert_msg, alerts[0] if len(alerts) > 0 else None, stock_data, count_data, None, None

#%%% CALLBACKS PAGE 3  [TAART]
# Callback to populate the stock overview table on Page 3
@app.callback(
    [Output('supply-timestamp-taart-page3', 'children'),
     Output('stock-table-taart', 'data')],
    [Input('url', 'pathname')],
    # prevent_initial_call=True
)
def show_stock_table_taart(pathname):
    if pathname == '/taart':
        try:
            # Create a database session using SessionLocal
            db = SessionLocal()

            # Execute the query using SQLAlchemy
            query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[TAART]"
            stock_df = pd.read_sql(query, db.bind)

            # Convert DataFrame to dictionary and return data
            data = stock_df.to_dict('records')
            
            write_data_to_supply_sheet("TAART", stock_df[selected_columns])
            
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            alert_msg = dbc.Alert(formatted_datetime, color="primary")
            
            return alert_msg, data
        except Exception as e:
            logging.error("Error fetching data:", e)  # Consider using logging for error messages
            return None, []  # Return empty list or display an error message
        finally:
            # Ensure session is closed even on exceptions
            db.close()
    raise PreventUpdate  # Don't update if not on Page 3
    
@app.callback(
    [Output('supply-timestamp-taart-page3', 'children', allow_duplicate=True),
     Output('barcode-status-taart-page3', 'children'),
     Output('stock-table-taart', 'data', allow_duplicate=True),
     Output('barcode-input-taart-page3', 'value'),
     Output('taart-count-input', 'value'),
     Output('barcode-output-taart-page3', 'value'),
     Output('taart-count-output', 'value')], 
    [Input('update-taart-database-button', 'n_clicks')],
    [State('barcode-input-taart-page3', 'value'),
     State('taart-count-input', 'value'),
     State('barcode-output-taart-page3', 'value'),
     State('taart-count-output', 'value')],
    prevent_initial_call=True
)
def update_stock_table_taart(n_clicks, barcode_input, item_count_input, barcode_output, item_count_output):
    # Check if the update button is clicked and inputs are provided
    if n_clicks > 0:
        
        try:
            
            alerts = []
            data = []
            
            # Create a database session using SessionLocal
            db = SessionLocal()
            
            # Update input table
            if barcode_input is not None and item_count_input is not None:
                
                update_query = text("UPDATE [dbo].[TAART] SET [Aantal] = [Aantal] + :item_count WHERE [Barcode] = :barcode")
                result = db.execute(update_query, {"item_count": item_count_input, "barcode": barcode_input})
                
                if result.rowcount == 0:
                    alerts.append(dbc.Alert(f'Barcode {barcode_input} not found in database.', color="danger"))
                else:
                    alerts.append(dbc.Alert(f'Barcode {barcode_input} found in database and stock was adjusted.', color="success"))
                    
            # Update output table
            if barcode_output is not None and item_count_output is not None:
                
                update_query = text("UPDATE [dbo].[TAART] SET [Aantal] = [Aantal] - :item_count WHERE [Barcode] = :barcode")
                result = db.execute(update_query, {"item_count": item_count_output, "barcode": barcode_output})
                
                if result.rowcount == 0:
                    alerts.append(dbc.Alert(f'Barcode {barcode_output} not found in database.', color="danger"))
                else:
                    alerts.append(dbc.Alert(f'Barcode {barcode_output} found in database and stock was adjusted.', color="success"))

            # Commit changes to the database
            db.commit()
            
            # Create a database session using SessionLocal
            db = SessionLocal()
            query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[TAART]"
            stock_df = pd.read_sql(query, db.bind)

            # Convert DataFrame to dictionary and return data
            data = stock_df.to_dict('records')
            
            db.close()
            
            write_data_to_supply_sheet("TAART", stock_df[selected_columns])
            
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            alert_msg = dbc.Alert(formatted_datetime, color="primary")
            
            return alert_msg, alerts[0] if len(alerts) > 0 else None, data, None, None, None, None
        except Exception as e:
            logging.error("Error updating stock table:", e)  # Consider using logging for error messages
            return dash.no_update, dbc.Alert(f"An error occurred: {str(e)}", color="danger"), [], None, None, None, None
    
    # If the update button is not clicked or if inputs are not provided, return no updates
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output('add-taart-status', 'children'),
     Output('stock-table-taart', 'data', allow_duplicate=True),
     Output('new-taart-barcode', 'value'),
     Output('new-taart-description', 'value')],
    [Input('add-taart-button', 'n_clicks')],
    [State('new-taart-barcode', 'value'),
     State('new-taart-description', 'value')],
    prevent_initial_call=True
)
def add_taart_to_database(n_clicks, barcode, description):
    
    item_count = 0
    
    if n_clicks:
        if barcode and description:
            try:
                
                # Create a database session using SessionLocal
                db = SessionLocal()
                
                insert_query = text(f"INSERT INTO [dbo].[TAART] (Barcode, Omschrijving, Aantal) VALUES ('{barcode}','{description}',{item_count})")
                db.execute(insert_query)
                
                # Commit changes to the database
                db.commit()
                
                # Create a database session using SessionLocal
                db = SessionLocal()
                query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[TAART]"
                stock_df = pd.read_sql(query, db.bind)

                # Convert DataFrame to dictionary and return data
                data = stock_df.to_dict('records')
                
                db.close()
                
                # write_data_to_supply_sheet("TAART", stock_df[selected_columns])
                
                return dbc.Alert("New item added to the database.", color="success"), data, None, None
            except Exception as e:
                logging.error("Error adding item to database:", e)
                return dbc.Alert(f"An error occurred: {str(e)}", color="danger"), dash.no_update, dash.no_update, dash.no_update
        else:
            return dbc.Alert("Please provide both description and item count.", color="warning"), dash.no_update, dash.no_update, dash.no_update
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output('deleted-row-taart-page3', 'children'),
     Output('stock-table-taart', 'data', allow_duplicate=True)],# You might need to add this component to your layout to display the deleted row information
    [Input('stock-table-taart', 'data'),
     State('stock-table-taart', 'data_previous')],
    prevent_initial_call=True,
)
def detect_deleted_row_taart_page3(current_data, previous_data):
    if not dash.callback_context.triggered:
        # This is the initial load, no data has been deleted
        raise PreventUpdate

    if previous_data is None:
        # This can happen if there's no previous data to compare against
        raise PreventUpdate

    # Convert both lists of dictionaries (current and previous data) into sets of tuples for comparison
    current_set = {tuple(d.items()) for d in current_data} if current_data else set()
    previous_set = {tuple(d.items()) for d in previous_data} if previous_data else set()

    # Find the difference between the two sets; this will be the deleted row(s)
    deleted_rows = previous_set - current_set

    # Convert the deleted rows back into a list of dictionaries to display or use elsewhere
    deleted_rows_dicts = [dict(row) for row in deleted_rows]

    # Initialize the alert message
    alert_msg = None

    if deleted_rows_dicts:
        # If there are deleted rows, process each one
        for deleted_row in deleted_rows_dicts:
            # Extract the ID of the deleted row
            deleted_id = deleted_row.get('Barcode', None)
            # print(deleted_id)
            if deleted_id:
                # Connect to the database and update the InStock status
                try:
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    delete_query = text("DELETE FROM [dbo].[TAART] WHERE [Barcode] = :deleted_id")
                    db.execute(delete_query, {"deleted_id": deleted_id})
                    
                    # Commit changes to the database
                    db.commit()
                    
                    db.close()
                    
                    query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[TAART]"
                    stock_df = pd.read_sql(query, db.bind)
                    
                    # write_data_to_supply_sheet("TAART", stock_df[selected_columns])
                   
                    alert_msg = dbc.Alert(f"Barcode {deleted_id} deleted from database.", color="success")
                except Exception as e:
                    alert_msg = dbc.Alert(f"Failed to update barcode {deleted_id} in database: {str(e)}", color="danger")
            else:
               alert_msg = dbc.Alert("Deleted row did not have a valid ID.", color="danger")
    else:
        # If no rows have been deleted, return an appropriate message
        alert_msg = dbc.Alert("No rows have been deleted.", color="warning")

    return alert_msg, current_data

#%%% CALLBACKS PAGE 4 [DIVERSEN]
# Callback to populate the stock overview table on Page 4
@app.callback(
    [Output('supply-timestamp-diversen-page4', 'children'),
     Output('stock-table-diversen', 'data')],
    [Input('url', 'pathname')],
    # prevent_initial_call=True
)
def show_stock_table_diversen(pathname):
    if pathname == '/diversen':
        try:
            # Create a database session using SessionLocal
            db = SessionLocal()

            # Execute the query using SQLAlchemy
            query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[DIVERSEN]"
            stock_df = pd.read_sql(query, db.bind)

            # Convert DataFrame to dictionary and return data
            data = stock_df.to_dict('records')
            
            write_data_to_supply_sheet("DIVERSEN", stock_df[selected_columns])
            
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            alert_msg = dbc.Alert(formatted_datetime, color="primary")
            
            return alert_msg, data
        except Exception as e:
            logging.error("Error fetching data:", e)  # Consider using logging for error messages
            return None, []  # Return empty list or display an error message
        finally:
            # Ensure session is closed even on exceptions
            db.close()
    raise PreventUpdate  # Don't update if not on Page 4
    
    
@app.callback(
    [Output('supply-timestamp-diversen-page4', 'children', allow_duplicate=True),
     Output('barcode-status-diversen-page4', 'children'),
     Output('stock-table-diversen', 'data', allow_duplicate=True),
     Output('barcode-input-diversen-page4', 'value'),
     Output('diversen-count-input', 'value'),
     Output('barcode-output-diversen-page4', 'value'),
     Output('diversen-count-output', 'value')], 
    [Input('update-diversen-database-button', 'n_clicks')],
    [State('barcode-input-diversen-page4', 'value'),
     State('diversen-count-input', 'value'),
     State('barcode-output-diversen-page4', 'value'),
     State('diversen-count-output', 'value')],
    prevent_initial_call=True
)
def update_stock_table_diversen(n_clicks, barcode_input, item_count_input, barcode_output, item_count_output):
    # Check if the update button is clicked and inputs are provided
    if n_clicks > 0:
        
        try:
            
            alerts = []
            data = []
            
            # Create a database session using SessionLocal
            db = SessionLocal()
            
            # Update input table
            if barcode_input is not None and item_count_input is not None:
                
                update_query = text("UPDATE [dbo].[DIVERSEN] SET [Aantal] = [Aantal] + :item_count WHERE [Barcode] = :barcode")
                result = db.execute(update_query, {"item_count": item_count_input, "barcode": barcode_input})
                
                if result.rowcount == 0:
                    alerts.append(dbc.Alert(f'Barcode {barcode_input} not found in database.', color="danger"))
                else:
                    alerts.append(dbc.Alert(f'Barcode {barcode_input} found in database and stock was adjusted.', color="success"))
                    
                # alerts.append(dbc.Alert(f'Barcode {barcode_input} found in database and stock was adjusted.', color="success"))

            # Update output table
            if barcode_output is not None and item_count_output is not None:
                
                update_query = text("UPDATE [dbo].[DIVERSEN] SET [Aantal] = [Aantal] - :item_count WHERE [Barcode] = :barcode")
                result = db.execute(update_query, {"item_count": item_count_output, "barcode": barcode_output})
                
                if result.rowcount == 0:
                    alerts.append(dbc.Alert(f'Barcode {barcode_output} not found in database.', color="danger"))
                else:
                    alerts.append(dbc.Alert(f'Barcode {barcode_output} found in database and stock was adjusted.', color="success"))

            # Commit changes to the database
            db.commit()
            
            # Create a database session using SessionLocal
            db = SessionLocal()
            query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[DIVERSEN]"
            stock_df = pd.read_sql(query, db.bind)

            # Convert DataFrame to dictionary and return data
            data = stock_df.to_dict('records')
            
            db.close()
            
            write_data_to_supply_sheet("DIVERSEN", stock_df[selected_columns])  
            
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            alert_msg = dbc.Alert(formatted_datetime, color="primary")

            return alert_msg, alerts[0] if len(alerts) > 0 else None, data, None, None, None, None
        except Exception as e:
            logging.error("Error updating stock table:", e)  # Consider using logging for error messages
            return dbc.Alert(f"An error occurred: {str(e)}", color="danger"), [], None, None, None, None
    
    # If the update button is not clicked or if inputs are not provided, return no updates
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output('add-diversen-status', 'children'),
     Output('stock-table-diversen', 'data', allow_duplicate=True),
     Output('new-diversen-barcode', 'value'),
     Output('new-diversen-description', 'value')],
    [Input('add-diversen-button', 'n_clicks')],
    [State('new-diversen-barcode', 'value'),
     State('new-diversen-description', 'value')],
    prevent_initial_call=True
)
def add_diversen_to_database(n_clicks, barcode, description):
    
    item_count = 0
    
    if n_clicks:
        if barcode and description:
            try:
                
                # Create a database session using SessionLocal
                db = SessionLocal()
                
                insert_query = text(f"INSERT INTO [dbo].[DIVERSEN] (Barcode, Omschrijving, Aantal) VALUES ('{barcode}','{description}',{item_count})")
                db.execute(insert_query)
                
                # Commit changes to the database
                db.commit()
                
                # Create a database session using SessionLocal
                db = SessionLocal()
                query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[DIVERSEN]"
                stock_df = pd.read_sql(query, db.bind)

                # Convert DataFrame to dictionary and return data
                data = stock_df.to_dict('records')
                
                db.close()
                
                # write_data_to_supply_sheet("DIVERSEN", stock_df[selected_columns])
                
                return dbc.Alert("New item added to the database.", color="success"), data, None, None
            except Exception as e:
                logging.error("Error adding item to database:", e)
                return dbc.Alert(f"An error occurred: {str(e)}", color="danger"), dash.no_update, dash.no_update, dash.no_update
        else:
            return dbc.Alert("Please provide both description and item count.", color="warning"), dash.no_update, dash.no_update, dash.no_update
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output('deleted-row-diversen-page4', 'children'),
     Output('stock-table-diversen', 'data', allow_duplicate=True)],# You might need to add this component to your layout to display the deleted row information
    [Input('stock-table-diversen', 'data'),
     State('stock-table-diversen', 'data_previous')],
    prevent_initial_call=True,
)
def detect_deleted_row_diversen_page4(current_data, previous_data):
    if not dash.callback_context.triggered:
        # This is the initial load, no data has been deleted
        raise PreventUpdate

    if previous_data is None:
        # This can happen if there's no previous data to compare against
        raise PreventUpdate

    # Convert both lists of dictionaries (current and previous data) into sets of tuples for comparison
    current_set = {tuple(d.items()) for d in current_data} if current_data else set()
    previous_set = {tuple(d.items()) for d in previous_data} if previous_data else set()

    # Find the difference between the two sets; this will be the deleted row(s)
    deleted_rows = previous_set - current_set

    # Convert the deleted rows back into a list of dictionaries to display or use elsewhere
    deleted_rows_dicts = [dict(row) for row in deleted_rows]

    # Initialize the alert message
    alert_msg = None

    if deleted_rows_dicts:
        # If there are deleted rows, process each one
        for deleted_row in deleted_rows_dicts:
            # Extract the ID of the deleted row
            deleted_id = deleted_row.get('Barcode', None)
            # print(deleted_id)
            if deleted_id:
                # Connect to the database and update the InStock status
                try:
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    delete_query = text("DELETE FROM [dbo].[DIVERSEN] WHERE [Barcode] = :deleted_id")
                    db.execute(delete_query, {"deleted_id": deleted_id})
                    
                    # Commit changes to the database
                    db.commit()
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[DIVERSEN]"
                    stock_df = pd.read_sql(query, db.bind)

                    db.close()
                    
                    # write_data_to_supply_sheet("DIVERSEN", stock_df[selected_columns])
                    
                    alert_msg = dbc.Alert(f"Barcode {deleted_id} deleted from database.", color="success")
                except Exception as e:
                    alert_msg = dbc.Alert(f"Failed to update barcode {deleted_id} in database: {str(e)}", color="danger")
            else:
               alert_msg = dbc.Alert("Deleted row did not have a valid ID.", color="danger")
    else:
        # If no rows have been deleted, return an appropriate message
        alert_msg = dbc.Alert("No rows have been deleted.", color="warning")

    return alert_msg, current_data

#%%% CALLBACKS PAGE 5 [SUIKERVRIJ]
# Callback to populate the stock overview table on Page 5
@app.callback(
    [Output('supply-timestamp-suikervrij-page5', 'children'),
     Output('stock-table-suikervrij', 'data')],
    [Input('url', 'pathname')],
    # prevent_initial_call=True
)
def show_stock_table_suikervrij(pathname):
    if pathname == '/suikervrij':
        try:
            # Create a database session using SessionLocal
            db = SessionLocal()

            # Execute the query using SQLAlchemy
            query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[SUIKERVRIJ]"
            stock_df = pd.read_sql(query, db.bind)

            # Convert DataFrame to dictionary and return data
            data = stock_df.to_dict('records')
            
            write_data_to_supply_sheet("SUIKERVRIJ", stock_df[selected_columns])
            
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            alert_msg = dbc.Alert(formatted_datetime, color="primary")
            
            return alert_msg, data
        except Exception as e:
            logging.error("Error fetching data:", e)  # Consider using logging for error messages
            return None, []  # Return empty list or display an error message
        finally:
            # Ensure session is closed even on exceptions
            db.close()
    raise PreventUpdate  # Don't update if not on Page 4
    
    
@app.callback(
    [Output('supply-timestamp-suikervrij-page5', 'children', allow_duplicate=True),
     Output('barcode-status-suikervrij-page5', 'children'),
     Output('stock-table-suikervrij', 'data', allow_duplicate=True),
     Output('barcode-input-suikervrij-page5', 'value'),
     Output('suikervrij-count-input', 'value'),
     Output('barcode-output-suikervrij-page5', 'value'),
     Output('suikervrij-count-output', 'value')], 
    [Input('update-suikervrij-database-button', 'n_clicks')],
    [State('barcode-input-suikervrij-page5', 'value'),
     State('suikervrij-count-input', 'value'),
     State('barcode-output-suikervrij-page5', 'value'),
     State('suikervrij-count-output', 'value')],
    prevent_initial_call=True
)
def update_stock_table_suikervrij(n_clicks, barcode_input, item_count_input, barcode_output, item_count_output):
    # Check if the update button is clicked and inputs are provided
    if n_clicks > 0:
        
        try:
            
            alerts = []
            data = []
            
            # Create a database session using SessionLocal
            db = SessionLocal()
            
            # Update input table
            if barcode_input is not None and item_count_input is not None:
                
                update_query = text("UPDATE [dbo].[SUIKERVRIJ] SET [Aantal] = [Aantal] + :item_count WHERE [Barcode] = :barcode")
                result = db.execute(update_query, {"item_count": item_count_input, "barcode": barcode_input})
                
                if result.rowcount == 0:
                    alerts.append(dbc.Alert(f'Barcode {barcode_input} not found in database.', color="danger"))
                else:
                    alerts.append(dbc.Alert(f'Barcode {barcode_input} found in database and stock was adjusted.', color="success"))
                    
                # alerts.append(dbc.Alert(f'Barcode {barcode_input} found in database and stock was adjusted.', color="success"))

            # Update output table
            if barcode_output is not None and item_count_output is not None:
                
                update_query = text("UPDATE [dbo].[SUIKERVRIJ] SET [Aantal] = [Aantal] - :item_count WHERE [Barcode] = :barcode")
                result = db.execute(update_query, {"item_count": item_count_output, "barcode": barcode_output})
                
                if result.rowcount == 0:
                    alerts.append(dbc.Alert(f'Barcode {barcode_output} not found in database.', color="danger"))
                else:
                    alerts.append(dbc.Alert(f'Barcode {barcode_output} found in database and stock was adjusted.', color="success"))

            # Commit changes to the database
            db.commit()
            
            # Create a database session using SessionLocal
            db = SessionLocal()
            query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[SUIKERVRIJ]"
            stock_df = pd.read_sql(query, db.bind)

            # Convert DataFrame to dictionary and return data
            data = stock_df.to_dict('records')
            
            db.close()
            
            write_data_to_supply_sheet("SUIKERVRIJ", stock_df[selected_columns])  
            
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            alert_msg = dbc.Alert(formatted_datetime, color="primary")

            return alert_msg, alerts[0] if len(alerts) > 0 else None, data, None, None, None, None
        except Exception as e:
            logging.error("Error updating stock table:", e)  # Consider using logging for error messages
            return dbc.Alert(f"An error occurred: {str(e)}", color="danger"), [], None, None, None, None
    
    # If the update button is not clicked or if inputs are not provided, return no updates
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output('add-suikervrij-status', 'children'),
     Output('stock-table-suikervrij', 'data', allow_duplicate=True),
     Output('new-suikervrij-barcode', 'value'),
     Output('new-suikervrij-description', 'value')],
    [Input('add-suikervrij-button', 'n_clicks')],
    [State('new-suikervrij-barcode', 'value'),
     State('new-suikervrij-description', 'value')],
    prevent_initial_call=True
)
def add_suikervrij_to_database(n_clicks, barcode, description):
    
    item_count = 0
    
    if n_clicks:
        if barcode and description:
            try:
                
                # Create a database session using SessionLocal
                db = SessionLocal()
                
                insert_query = text(f"INSERT INTO [dbo].[SUIKERVRIJ] (Barcode, Omschrijving, Aantal) VALUES ('{barcode}','{description}',{item_count})")
                db.execute(insert_query)
                
                # Commit changes to the database
                db.commit()
                
                # Create a database session using SessionLocal
                db = SessionLocal()
                query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[SUIKERVRIJ]"
                stock_df = pd.read_sql(query, db.bind)

                # Convert DataFrame to dictionary and return data
                data = stock_df.to_dict('records')
                
                db.close()
                
                # write_data_to_supply_sheet("SUIKERVRIJ", stock_df[selected_columns])
                
                return dbc.Alert("New item added to the database.", color="success"), data, None, None
            except Exception as e:
                logging.error("Error adding item to database:", e)
                return dbc.Alert(f"An error occurred: {str(e)}", color="danger"), dash.no_update, dash.no_update, dash.no_update
        else:
            return dbc.Alert("Please provide both description and item count.", color="warning"), dash.no_update, dash.no_update, dash.no_update
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output('deleted-row-suikervrij-page5', 'children'),
     Output('stock-table-suikervrij', 'data', allow_duplicate=True)],# You might need to add this component to your layout to display the deleted row information
    [Input('stock-table-suikervrij', 'data'),
     State('stock-table-suikervrij', 'data_previous')],
    prevent_initial_call=True,
)
def detect_deleted_row_suikervrij_page5(current_data, previous_data):
    if not dash.callback_context.triggered:
        # This is the initial load, no data has been deleted
        raise PreventUpdate

    if previous_data is None:
        # This can happen if there's no previous data to compare against
        raise PreventUpdate

    # Convert both lists of dictionaries (current and previous data) into sets of tuples for comparison
    current_set = {tuple(d.items()) for d in current_data} if current_data else set()
    previous_set = {tuple(d.items()) for d in previous_data} if previous_data else set()

    # Find the difference between the two sets; this will be the deleted row(s)
    deleted_rows = previous_set - current_set

    # Convert the deleted rows back into a list of dictionaries to display or use elsewhere
    deleted_rows_dicts = [dict(row) for row in deleted_rows]

    # Initialize the alert message
    alert_msg = None

    if deleted_rows_dicts:
        # If there are deleted rows, process each one
        for deleted_row in deleted_rows_dicts:
            # Extract the ID of the deleted row
            deleted_id = deleted_row.get('Barcode', None)
            # print(deleted_id)
            if deleted_id:
                # Connect to the database and update the InStock status
                try:
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    delete_query = text("DELETE FROM [dbo].[SUIKERVRIJ] WHERE [Barcode] = :deleted_id")
                    db.execute(delete_query, {"deleted_id": deleted_id})
                    
                    # Commit changes to the database
                    db.commit()
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[SUIKERVRIJ]"
                    stock_df = pd.read_sql(query, db.bind)

                    db.close()
                    
                    # write_data_to_supply_sheet("SUIKERVRIJ", stock_df[selected_columns])
                    
                    alert_msg = dbc.Alert(f"Barcode {deleted_id} deleted from database.", color="success")
                except Exception as e:
                    alert_msg = dbc.Alert(f"Failed to update barcode {deleted_id} in database: {str(e)}", color="danger")
            else:
               alert_msg = dbc.Alert("Deleted row did not have a valid ID.", color="danger")
    else:
        # If no rows have been deleted, return an appropriate message
        alert_msg = dbc.Alert("No rows have been deleted.", color="warning")

    return alert_msg, current_data

#%%% CALLBACKS PAGE 6 [GEBAK]
# Callback to populate the stock overview table on Page 6
@app.callback(
    [Output('supply-timestamp-gebak-page6', 'children'),
     Output('stock-table-gebak', 'data')],
    [Input('url', 'pathname')],
    # prevent_initial_call=True
)
def show_stock_table_gebak(pathname):
    if pathname == '/gebak':
        try:
            # Create a database session using SessionLocal
            db = SessionLocal()

            # Execute the query using SQLAlchemy
            query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[GEBAK]"
            stock_df = pd.read_sql(query, db.bind)

            # Convert DataFrame to dictionary and return data
            data = stock_df.to_dict('records')
            
            write_data_to_supply_sheet("GEBAK", stock_df[selected_columns])
            
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            alert_msg = dbc.Alert(formatted_datetime, color="primary")
            
            return alert_msg, data
        except Exception as e:
            logging.error("Error fetching data:", e)  # Consider using logging for error messages
            return None, []  # Return empty list or display an error message
        finally:
            # Ensure session is closed even on exceptions
            db.close()
    raise PreventUpdate  # Don't update if not on Page 4
    
    
@app.callback(
    [Output('supply-timestamp-gebak-page6', 'children', allow_duplicate=True),
     Output('barcode-status-gebak-page6', 'children'),
     Output('stock-table-gebak', 'data', allow_duplicate=True),
     Output('barcode-input-gebak-page6', 'value'),
     Output('gebak-count-input', 'value'),
     Output('barcode-output-gebak-page6', 'value'),
     Output('gebak-count-output', 'value')], 
    [Input('update-gebak-database-button', 'n_clicks')],
    [State('barcode-input-gebak-page6', 'value'),
     State('gebak-count-input', 'value'),
     State('barcode-output-gebak-page6', 'value'),
     State('gebak-count-output', 'value')],
    prevent_initial_call=True
)
def update_stock_table_gebak(n_clicks, barcode_input, item_count_input, barcode_output, item_count_output):
    # Check if the update button is clicked and inputs are provided
    if n_clicks > 0:
        
        try:
            
            alerts = []
            data = []
            
            # Create a database session using SessionLocal
            db = SessionLocal()
            
            # Update input table
            if barcode_input is not None and item_count_input is not None:
                
                update_query = text("UPDATE [dbo].[GEBAK] SET [Aantal] = [Aantal] + :item_count WHERE [Barcode] = :barcode")
                result = db.execute(update_query, {"item_count": item_count_input, "barcode": barcode_input})
                
                if result.rowcount == 0:
                    alerts.append(dbc.Alert(f'Barcode {barcode_input} not found in database.', color="danger"))
                else:
                    alerts.append(dbc.Alert(f'Barcode {barcode_input} found in database and stock was adjusted.', color="success"))
                    
                # alerts.append(dbc.Alert(f'Barcode {barcode_input} found in database and stock was adjusted.', color="success"))

            # Update output table
            if barcode_output is not None and item_count_output is not None:
                
                update_query = text("UPDATE [dbo].[GEBAK] SET [Aantal] = [Aantal] - :item_count WHERE [Barcode] = :barcode")
                result = db.execute(update_query, {"item_count": item_count_output, "barcode": barcode_output})
                
                if result.rowcount == 0:
                    alerts.append(dbc.Alert(f'Barcode {barcode_output} not found in database.', color="danger"))
                else:
                    alerts.append(dbc.Alert(f'Barcode {barcode_output} found in database and stock was adjusted.', color="success"))

            # Commit changes to the database
            db.commit()
            
            # Create a database session using SessionLocal
            db = SessionLocal()
            query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[GEBAK]"
            stock_df = pd.read_sql(query, db.bind)

            # Convert DataFrame to dictionary and return data
            data = stock_df.to_dict('records')
            
            db.close()
            
            write_data_to_supply_sheet("GEBAK", stock_df[selected_columns])  
            
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            alert_msg = dbc.Alert(formatted_datetime, color="primary")

            return alert_msg, alerts[0] if len(alerts) > 0 else None, data, None, None, None, None
        except Exception as e:
            logging.error("Error updating stock table:", e)  # Consider using logging for error messages
            return dbc.Alert(f"An error occurred: {str(e)}", color="danger"), [], None, None, None, None
    
    # If the update button is not clicked or if inputs are not provided, return no updates
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output('add-gebak-status', 'children'),
     Output('stock-table-gebak', 'data', allow_duplicate=True),
     Output('new-gebak-barcode', 'value'),
     Output('new-gebak-description', 'value')],
    [Input('add-gebak-button', 'n_clicks')],
    [State('new-gebak-barcode', 'value'),
     State('new-gebak-description', 'value')],
    prevent_initial_call=True
)
def add_gebak_to_database(n_clicks, barcode, description):
    
    item_count = 0
    
    if n_clicks:
        if barcode and description:
            try:
                
                # Create a database session using SessionLocal
                db = SessionLocal()
                
                insert_query = text(f"INSERT INTO [dbo].[GEBAK] (Barcode, Omschrijving, Aantal) VALUES ('{barcode}','{description}',{item_count})")
                db.execute(insert_query)
                
                # Commit changes to the database
                db.commit()
                
                # Create a database session using SessionLocal
                db = SessionLocal()
                query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[GEBAK]"
                stock_df = pd.read_sql(query, db.bind)

                # Convert DataFrame to dictionary and return data
                data = stock_df.to_dict('records')
                
                db.close()
                
                # write_data_to_supply_sheet("GEBAK", stock_df[selected_columns])
                
                return dbc.Alert("New item added to the database.", color="success"), data, None, None
            except Exception as e:
                logging.error("Error adding item to database:", e)
                return dbc.Alert(f"An error occurred: {str(e)}", color="danger"), dash.no_update, dash.no_update, dash.no_update
        else:
            return dbc.Alert("Please provide both description and item count.", color="warning"), dash.no_update, dash.no_update, dash.no_update
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output('deleted-row-gebak-page6', 'children'),
     Output('stock-table-gebak', 'data', allow_duplicate=True)],# You might need to add this component to your layout to display the deleted row information
    [Input('stock-table-gebak', 'data'),
     State('stock-table-gebak', 'data_previous')],
    prevent_initial_call=True,
)
def detect_deleted_row_gebak_page6(current_data, previous_data):
    if not dash.callback_context.triggered:
        # This is the initial load, no data has been deleted
        raise PreventUpdate

    if previous_data is None:
        # This can happen if there's no previous data to compare against
        raise PreventUpdate

    # Convert both lists of dictionaries (current and previous data) into sets of tuples for comparison
    current_set = {tuple(d.items()) for d in current_data} if current_data else set()
    previous_set = {tuple(d.items()) for d in previous_data} if previous_data else set()

    # Find the difference between the two sets; this will be the deleted row(s)
    deleted_rows = previous_set - current_set

    # Convert the deleted rows back into a list of dictionaries to display or use elsewhere
    deleted_rows_dicts = [dict(row) for row in deleted_rows]

    # Initialize the alert message
    alert_msg = None

    if deleted_rows_dicts:
        # If there are deleted rows, process each one
        for deleted_row in deleted_rows_dicts:
            # Extract the ID of the deleted row
            deleted_id = deleted_row.get('Barcode', None)
            # print(deleted_id)
            if deleted_id:
                # Connect to the database and update the InStock status
                try:
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    delete_query = text("DELETE FROM [dbo].[GEBAK] WHERE [Barcode] = :deleted_id")
                    db.execute(delete_query, {"deleted_id": deleted_id})
                    
                    # Commit changes to the database
                    db.commit()
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[GEBAK]"
                    stock_df = pd.read_sql(query, db.bind)

                    db.close()
                    
                    # write_data_to_supply_sheet("GEBAK", stock_df[selected_columns])
                    
                    alert_msg = dbc.Alert(f"Barcode {deleted_id} deleted from database.", color="success")
                except Exception as e:
                    alert_msg = dbc.Alert(f"Failed to update barcode {deleted_id} in database: {str(e)}", color="danger")
            else:
               alert_msg = dbc.Alert("Deleted row did not have a valid ID.", color="danger")
    else:
        # If no rows have been deleted, return an appropriate message
        alert_msg = dbc.Alert("No rows have been deleted.", color="warning")

    return alert_msg, current_data

#%%% CALLBACKS PAGE 7 [POTJES]
# Callback to populate the stock overview table on Page 7
@app.callback(
    [Output('supply-timestamp-potjes-page7', 'children'),
     Output('stock-table-potjes', 'data')],
    [Input('url', 'pathname')],
    # prevent_initial_call=True
)
def show_stock_table_potjes(pathname):
    if pathname == '/potjes':
        try:
            # Create a database session using SessionLocal
            db = SessionLocal()

            # Execute the query using SQLAlchemy
            query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[POTJES]"
            stock_df = pd.read_sql(query, db.bind)

            # Convert DataFrame to dictionary and return data
            data = stock_df.to_dict('records')
            
            write_data_to_supply_sheet("POTJES", stock_df[selected_columns])
            
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            alert_msg = dbc.Alert(formatted_datetime, color="primary")
            
            return alert_msg, data
        except Exception as e:
            logging.error("Error fetching data:", e)  # Consider using logging for error messages
            return None, []  # Return empty list or display an error message
        finally:
            # Ensure session is closed even on exceptions
            db.close()
    raise PreventUpdate  # Don't update if not on Page 4
    
    
@app.callback(
    [Output('supply-timestamp-potjes-page7', 'children', allow_duplicate=True),
     Output('barcode-status-potjes-page7', 'children'),
     Output('stock-table-potjes', 'data', allow_duplicate=True),
     Output('barcode-input-potjes-page7', 'value'),
     Output('potjes-count-input', 'value'),
     Output('barcode-output-potjes-page7', 'value'),
     Output('potjes-count-output', 'value')], 
    [Input('update-potjes-database-button', 'n_clicks')],
    [State('barcode-input-potjes-page7', 'value'),
     State('potjes-count-input', 'value'),
     State('barcode-output-potjes-page7', 'value'),
     State('potjes-count-output', 'value')],
    prevent_initial_call=True
)
def update_stock_table_potjes(n_clicks, barcode_input, item_count_input, barcode_output, item_count_output):
    # Check if the update button is clicked and inputs are provided
    if n_clicks > 0:
        
        try:
            
            alerts = []
            data = []
            
            # Create a database session using SessionLocal
            db = SessionLocal()
            
            # Update input table
            if barcode_input is not None and item_count_input is not None:
                
                update_query = text("UPDATE [dbo].[POTJES] SET [Aantal] = [Aantal] + :item_count WHERE [Barcode] = :barcode")
                result = db.execute(update_query, {"item_count": item_count_input, "barcode": barcode_input})
                
                if result.rowcount == 0:
                    alerts.append(dbc.Alert(f'Barcode {barcode_input} not found in database.', color="danger"))
                else:
                    alerts.append(dbc.Alert(f'Barcode {barcode_input} found in database and stock was adjusted.', color="success"))
                    
                # alerts.append(dbc.Alert(f'Barcode {barcode_input} found in database and stock was adjusted.', color="success"))

            # Update output table
            if barcode_output is not None and item_count_output is not None:
                
                update_query = text("UPDATE [dbo].[POTJES] SET [Aantal] = [Aantal] - :item_count WHERE [Barcode] = :barcode")
                result = db.execute(update_query, {"item_count": item_count_output, "barcode": barcode_output})
                
                if result.rowcount == 0:
                    alerts.append(dbc.Alert(f'Barcode {barcode_output} not found in database.', color="danger"))
                else:
                    alerts.append(dbc.Alert(f'Barcode {barcode_output} found in database and stock was adjusted.', color="success"))

            # Commit changes to the database
            db.commit()
            
            # Create a database session using SessionLocal
            db = SessionLocal()
            query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[POTJES]"
            stock_df = pd.read_sql(query, db.bind)

            # Convert DataFrame to dictionary and return data
            data = stock_df.to_dict('records')
            
            db.close()
            
            write_data_to_supply_sheet("POTJES", stock_df[selected_columns])  
            
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            alert_msg = dbc.Alert(formatted_datetime, color="primary")

            return alert_msg, alerts[0] if len(alerts) > 0 else None, data, None, None, None, None
        except Exception as e:
            logging.error("Error updating stock table:", e)  # Consider using logging for error messages
            return dbc.Alert(f"An error occurred: {str(e)}", color="danger"), [], None, None, None, None
    
    # If the update button is not clicked or if inputs are not provided, return no updates
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output('add-potjes-status', 'children'),
     Output('stock-table-potjes', 'data', allow_duplicate=True),
     Output('new-potjes-barcode', 'value'),
     Output('new-potjes-description', 'value')],
    [Input('add-potjes-button', 'n_clicks')],
    [State('new-potjes-barcode', 'value'),
     State('new-potjes-description', 'value')],
    prevent_initial_call=True
)
def add_potjes_to_database(n_clicks, barcode, description):
    
    item_count = 0
    
    if n_clicks:
        if barcode and description:
            try:
                
                # Create a database session using SessionLocal
                db = SessionLocal()
                
                insert_query = text(f"INSERT INTO [dbo].[POTJES] (Barcode, Omschrijving, Aantal) VALUES ('{barcode}','{description}',{item_count})")
                db.execute(insert_query)
                
                # Commit changes to the database
                db.commit()
                
                # Create a database session using SessionLocal
                db = SessionLocal()
                query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[POTJES]"
                stock_df = pd.read_sql(query, db.bind)

                # Convert DataFrame to dictionary and return data
                data = stock_df.to_dict('records')
                
                db.close()
                
                # write_data_to_supply_sheet("POTJES", stock_df[selected_columns])
                
                return dbc.Alert("New item added to the database.", color="success"), data, None, None
            except Exception as e:
                logging.error("Error adding item to database:", e)
                return dbc.Alert(f"An error occurred: {str(e)}", color="danger"), dash.no_update, dash.no_update, dash.no_update
        else:
            return dbc.Alert("Please provide both description and item count.", color="warning"), dash.no_update, dash.no_update, dash.no_update
    
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    [Output('deleted-row-potjes-page7', 'children'),
     Output('stock-table-potjes', 'data', allow_duplicate=True)],# You might need to add this component to your layout to display the deleted row information
    [Input('stock-table-potjes', 'data'),
     State('stock-table-potjes', 'data_previous')],
    prevent_initial_call=True,
)
def detect_deleted_row_potjes_page7(current_data, previous_data):
    if not dash.callback_context.triggered:
        # This is the initial load, no data has been deleted
        raise PreventUpdate

    if previous_data is None:
        # This can happen if there's no previous data to compare against
        raise PreventUpdate

    # Convert both lists of dictionaries (current and previous data) into sets of tuples for comparison
    current_set = {tuple(d.items()) for d in current_data} if current_data else set()
    previous_set = {tuple(d.items()) for d in previous_data} if previous_data else set()

    # Find the difference between the two sets; this will be the deleted row(s)
    deleted_rows = previous_set - current_set

    # Convert the deleted rows back into a list of dictionaries to display or use elsewhere
    deleted_rows_dicts = [dict(row) for row in deleted_rows]

    # Initialize the alert message
    alert_msg = None

    if deleted_rows_dicts:
        # If there are deleted rows, process each one
        for deleted_row in deleted_rows_dicts:
            # Extract the ID of the deleted row
            deleted_id = deleted_row.get('Barcode', None)
            # print(deleted_id)
            if deleted_id:
                # Connect to the database and update the InStock status
                try:
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    delete_query = text("DELETE FROM [dbo].[POTJES] WHERE [Barcode] = :deleted_id")
                    db.execute(delete_query, {"deleted_id": deleted_id})
                    
                    # Commit changes to the database
                    db.commit()
                    
                    # Create a database session using SessionLocal
                    db = SessionLocal()
                    query = "SELECT [Barcode], [Omschrijving], [Aantal] FROM [dbo].[POTJES]"
                    stock_df = pd.read_sql(query, db.bind)

                    db.close()
                    
                    # write_data_to_supply_sheet("POTJES", stock_df[selected_columns])
                    
                    alert_msg = dbc.Alert(f"Barcode {deleted_id} deleted from database.", color="success")
                except Exception as e:
                    alert_msg = dbc.Alert(f"Failed to update barcode {deleted_id} in database: {str(e)}", color="danger")
            else:
               alert_msg = dbc.Alert("Deleted row did not have a valid ID.", color="danger")
    else:
        # If no rows have been deleted, return an appropriate message
        alert_msg = dbc.Alert("No rows have been deleted.", color="warning")

    return alert_msg, current_data

#%%% CALLBACKS PAGE 8 [ORDERS]
# Callback to populate the stock overview table on Page 8
@app.callback(
    [Output("orders-header", "children"),
     Output('orders-table', 'data')],
    [Input('search-button-page8', 'n_clicks')],
    [State('store-dropdown-page8', 'value'),
     State('order-date-page8', 'value'),
     State('barcode-ijs-page8', 'value'),
     State('smaak-ijs-page8', 'value')]
)
def search_orders_table(n_clicks, store, order_date, barcode, smaak):
    if n_clicks:
        try:
            # Create a database session using SessionLocal
            db = SessionLocal()
            
            store_label = next((item['label'] for item in stores if item['value'] == store), None)
            
            # Execute the query using SQLAlchemy
            # query = "SELECT [WgtDateTime], [ID], [Scale], [Description], [ValueNet], [Type] FROM [dbo].[DATA] WHERE [InStock] = 1"
            query_orders = "SELECT [Barcode] as Barcode, [Omschrijving] as Omschrijving, [Winkel] as Winkel, [Order Datum] as Datum FROM [dbo].[ORDERS] WHERE 1=1"
            
            # Add filters based on input values
            if store_label:
                query_orders  += f" AND [Winkel] = '{store_label}'"
            if order_date:
                query_orders  += f" AND [Order Datum] = '{order_date}'"
            if barcode:
                query_orders  += f" AND [Barcode] LIKE '%{barcode}%'"
            if smaak:
                query_orders  += f" AND [Omschrijving] LIKE '%{smaak}%'"
            
            orders_df  = pd.read_sql(query_orders, db.bind)
            
            # Fetch related data from the DATA table
            if not orders_df.empty:
                barcodes = "','".join(orders_df['Barcode'].unique())
                query_data = f"""
                SELECT [DATA01] as Barcode, [WgtDate], [DATA05]
                FROM [dbo].[DATA]
                WHERE [DATA01] IN ('{barcodes}')
                """
                data_df = pd.read_sql(query_data, db.bind)
                
                # Merge the data from DATA table with orders_df
                merged_df = orders_df.merge(data_df, how='left', left_on='Barcode', right_on='Barcode')
                
                # Rename the columns
                merged_df.rename(columns={
                    'WgtDate': 'Weegdatum',
                    'DATA05': 'Medewerker'
                }, inplace=True)
                
                row_count = merged_df.shape[0]
                header = f"ORDERS - Aantal: {row_count} bakken"
                stock_data = merged_df.to_dict('records')
                
                return header, stock_data
            
            row_count = orders_df.shape[0]
            header = f"ORDERS - Aantal: {row_count} bakken"
            stock_data = orders_df.to_dict('records')
            return header, stock_data
        
        except Exception as e:
            logging.error("Error fetching data:", e)  # Consider using logging for error messages
            return None, []  # Return empty list or display an error message
        finally:
            # Ensure session is closed even on exceptions
            db.close()
    raise PreventUpdate  # Don't update if not on Page 2
    
    
if __name__ == '__main__':
    app.run_server(debug=True)
