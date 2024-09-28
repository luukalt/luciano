@echo off
start /B cmd /k "cd /d C:\Users\ijssa\OneDrive\Bureaublad\luciano-stock\python-envs && env311\Scripts\activate && spyder"
timeout /t 5 >nul
taskkill /f /im cmd.exe
exit