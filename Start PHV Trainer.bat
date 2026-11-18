@echo off
setlocal DisableDelayedExpansion
set "PHV_APP_PATH=%~dp0app\index.html"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\launch.ps1"
if errorlevel 1 (
  echo Could not open PHV Exam Trainer. Open app\index.html in your browser instead.
  pause
)
endlocal
