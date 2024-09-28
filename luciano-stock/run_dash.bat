@echo off
start msedge.exe http://127.0.0.1:8050
call C:\Users\ijssa\OneDrive\Bureaublad\luciano-stock\python-envs\env311\Scripts\activate
cd C:\Users\ijssa\OneDrive\Bureaublad\luciano-stock
python dash_app.py
pause

