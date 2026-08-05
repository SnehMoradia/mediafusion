@echo off
title Playlist Downloader App
echo Starting Playlist Downloader Application...
echo.

IF NOT EXIST "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Installing dependencies...
    call venv\Scripts\activate
    pip install -r requirements.txt
) ELSE (
    call venv\Scripts\activate
)

echo Starting Flask server on http://localhost:5050
start "" "http://localhost:5050"
python app.py
pause
