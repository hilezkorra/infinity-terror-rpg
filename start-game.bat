@echo off
REM ============================================================
REM  AI RPG  —  Terror Infinity Launcher
REM  Opens the polished launcher window. "Start Game" inside it
REM  boots the watcher engine and enters the game.
REM ============================================================
title AI RPG

set "URL=http://localhost/terror-infinity-rpg/launcher.html"

REM Locate Microsoft Edge for app-mode (frameless window)
set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"

if exist "%EDGE%" (
  start "" "%EDGE%" --app=%URL% --autoplay-policy=no-user-gesture-required --start-fullscreen
) else (
  REM Fallback: try Chrome, else default browser
  set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
  if exist "%CHROME%" (
    start "" "%CHROME%" --app=%URL% --autoplay-policy=no-user-gesture-required --start-fullscreen
  ) else (
    start "" %URL%
  )
)
