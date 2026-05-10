@echo off
REM Windows launcher — double-click this file to start the app.
REM On first run it builds a local Python venv and installs PySide6 + dependencies.
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo --------------------------------------------------
echo   Rusca Kelime Studyosu — launcher
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
    echo HATA: Python bulunamadi.
    echo.
    echo Cozum: https://www.python.org/downloads/windows/
    echo Python 3.12 indir, kur. Kurulumda
    echo      "Add Python to PATH" kutucugunu MUTLAKA isaretle.
    echo.
    echo Sonra bu dosyaya tekrar cift tikla.
    echo.
    pause
    exit /b 1
)

echo - Python kullaniliyor: %PY%
%PY% --version

set VENV=.venv
set VENV_PY=%VENV%\Scripts\python.exe

if not exist "%VENV_PY%" (
    echo Virtualenv olusturuluyor (.venv)...
    %PY% -m venv "%VENV%"
    if errorlevel 1 (
        echo HATA: venv olusturulamadi.
        pause
        exit /b 1
    )
)

echo Bagimliliklar kontrol ediliyor (ilk acilis 3-5 dk surebilir)...
"%VENV_PY%" -m pip install --upgrade pip --quiet
"%VENV_PY%" -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo HATA: Bagimliliklar kurulamadi. Yukaridaki mesajlari oku.
    pause
    exit /b 1
)

echo Uygulama baslatiliyor...
echo --------------------------------------------------
echo.

"%VENV_PY%" app.py
if errorlevel 1 (
    echo.
    echo --------------------------------------------------
    echo HATA: Uygulama hatayla kapandi.
    pause
    exit /b 1
)
