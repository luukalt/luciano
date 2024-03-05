# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 23:47:52 2024

@author: luuka
"""

import pyodbc

# Define the connection parameters
server_name = 'DESKTOP-B05JCBI\\SQLEXPRESS'  # Replace with your SQL Server instance name or IP address
database_name = 'IceCreams'  # Replace with your database name
username = 'gas'  # Replace with your SQL Server username
password = 'gas2024'  # Replace with your SQL Server password

# Create a connection string
connection_string = f'DRIVER={{SQL Server}};SERVER={server_name};DATABASE={database_name};UID={username};PWD={password}'

try:
    # Establish a database connection
    connection = pyodbc.connect(connection_string)

    # Create a cursor object for executing SQL queries
    cursor = connection.cursor()

    # Example: Execute a SQL query to select all rows from the IceCreamFlavors table
    cursor.execute("SELECT * FROM IceCreamFlavors")

    # Fetch and print results
    for row in cursor.fetchall():
        print(row)

except pyodbc.Error as e:
    print("Error connecting to the database:", e)

finally:
    # Close the cursor and database connection
    if 'cursor' in locals():
        cursor.close()
    if 'connection' in locals():
        connection.close()
