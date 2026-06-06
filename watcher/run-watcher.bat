@echo off
REM Starts the Terror Infinity watcher engine in this folder.
title TI-Watcher
cd /d "%~dp0"
echo Starting watcher engine...
node watcher.js
echo.
echo Watcher stopped. Press any key to close.
pause >nul
