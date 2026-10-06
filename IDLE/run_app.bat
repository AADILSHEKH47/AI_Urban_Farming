@echo off
title AI Urban Farming Assistant
echo ===================================================
echo Starting AI Urban Farming Assistant...
echo ===================================================
echo.
cd /d "%~dp0"
python -m streamlit run app.py
pause
