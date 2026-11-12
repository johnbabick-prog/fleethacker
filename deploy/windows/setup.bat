@echo off
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0setup.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   Something went wrong. See the error above.
    pause
)
