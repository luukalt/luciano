@echo off

REM Define the path to the lock file
set LOCK_FILE=C:\Users\luuka\Documents\Github\luciano-stock\dash_app.lock

REM Check if the lock file exists (indicating that the Dash app is already running)
if exist "%LOCK_FILE%" (
    REM If the lock file exists, display a message and exit
    echo Another instance of the Dash app is already running.
    pause
    exit /b
)

REM If the lock file doesn't exist, create it
echo Creating lock file...
type nul > "%LOCK_FILE%"

REM Start the Dash app and web browser
start msedge.exe http://127.0.0.1:8050
call C:\Users\luuka\python-envs\env311\Scripts\activate
cd C:\Users\luuka\Documents\Github\luciano-stock
python dash_app.py

REM After the Dash app exits, delete the lock file
echo Deleting lock file...
del "%LOCK_FILE%"

pause
