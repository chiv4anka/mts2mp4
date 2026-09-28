@echo off
setlocal
cd /d "%~dp0"
title Build mts2mp4

echo === Build mts2mp4.exe ===
echo Folder: %CD%
echo.

if not exist ffmpeg.exe (
    echo [ERROR] ffmpeg.exe not found in this folder.
    echo Put ffmpeg.exe next to build script and mts2mp4.py
    goto :end
)
if not exist mts2mp4.py (
    echo [ERROR] mts2mp4.py not found in this folder.
    goto :end
)

set PY=
python --version >nul 2>&1 && set PY=python
if not defined PY (
    py -3 --version >nul 2>&1 && set PY=py -3
)
if not defined PY (
    echo [ERROR] Python not found.
    echo Install Python 3.9+ from python.org and tick "Add python.exe to PATH".
    goto :end
)
echo Using: %PY%
echo.

%PY% -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo [ERROR] Could not install PyInstaller. Check internet connection.
    goto :end
)

%PY% -m PyInstaller --noconfirm --onefile --windowed --name mts2mp4 --add-binary "ffmpeg.exe;." mts2mp4.py
if errorlevel 1 (
    echo [ERROR] Build failed. See messages above.
    goto :end
)

echo.
echo DONE. Your file: %CD%\dist\mts2mp4.exe

:end
echo.
pause
