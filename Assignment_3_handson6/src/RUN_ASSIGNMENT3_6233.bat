@echo off
cd /d "%~dp0"
start "Assignment 3 GUI" py IoT_GUI_6233.py
timeout /t 2 >nul
start "Cube Simulator" py CUBE_SIMULATOR_6233.py
