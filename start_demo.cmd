@echo off
cd /d "%~dp0"
echo A abrir a consola em http://127.0.0.1:8765 ...
".venv\Scripts\python.exe" scripts\gate_ui.py
pause
