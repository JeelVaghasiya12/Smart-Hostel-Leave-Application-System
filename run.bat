@echo off
title Hostel Leave Application
cd /d "%~dp0"
echo ===================================================
echo Starting Hostel Leave Application...
echo http://127.0.0.1:5000
echo ===================================================
start http://127.0.0.1:5000
.\venv\Scripts\python.exe app.py
pause
