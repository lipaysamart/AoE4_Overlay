@echo off
rem Start AoE4 Overlay from source without a console window
cd /d %~dp0src
start "" "%~dp0venv\Scripts\pythonw.exe" AoE4_Overlay.py
