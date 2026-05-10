@echo off
REM Windows launcher — double-click to start Russian Vocab Studio.
REM Builds a local Python venv and installs PySide6 + dependencies on first run.
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo --------------------------------------------------
echo   Russian Vocab Studio — launcher
echo   %DATE% %TIME%
echo   Folder: %CD%
echo --------------------------------------------------

REM ---- Find Python 3.10+ ----
set PY=
for %%P in (python python3 py) do (
    if not defined PY (
        %%P --version >nul 2>&1
        if !errorlevel! equ 0 (
            for /f "tokens=2" %%V in ('%%P --version 2^>^&1') do (
                set ver=%%V
                set major=!ver:~0,1!
                if "!major!"=="3" set PY=%%P
            )
        )
    )
)

if "%PY%"=="" (
    echo.
    echo ERROR: Python not found.
    echo.
    echo Fix: install Python 3.12 from https://www.python.org/downloads/windows/
    echo During installation MAKE SURE you tick:
    echo      [x] Add Python to PATH
    echo.
    echo Then double-click this file again.
    echo.
    pause
    exit /b 1
)

echo - Using Python: %PY%
%PY% --version

set VENV=.venv
set VENV_PY=%VENV%\Scripts\python.exe

if not exist "%VENV_PY%" (
    echo Creating virtualenv (.venv)...
    %PY% -m venv "%VENV%"
    if errorlevel 1 (
        echo ERROR: failed to create virtualenv.
        pause
        exit /b 1
    )
)

echo Checking dependencies (first run can take 3-5 minutes)...
"%VENV_PY%" -m pip install --upgrade pip --quiet
"%VENV_PY%" -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: failed to install dependencies. See messages above.
    pause
    exit /b 1
)

echo Launching app...
echo --------------------------------------------------
echo.

"%VENV_PY%" app.py
if errorlevel 1 (
    echo.
    echo --------------------------------------------------
    echo ERROR: the app exited with an error.
    pause
    exit /b 1
)
