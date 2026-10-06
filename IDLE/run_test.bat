@echo off
title Test AI Urban Farming Assistant
echo ===================================================
echo Running 16-Step Verification Test...
echo ===================================================
echo.
cd /d "%~dp0"
python test_flow.py
echo.
pause
