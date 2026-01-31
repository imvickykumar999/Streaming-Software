@echo off
setlocal

:: --- CONFIGURATION ---
set COMPANY_NAME=24x7LiveStream
set PFX_PATH=C:\Users\surface\Documents\24x7.pfx
set PFX_PASS=YourPassword123
:: Note: Double-check your Windows SDK version folder (e.g., 10.0.22621.0)
set SIGNTOOL_PATH="C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"

echo [1/3] Preparing PyInstaller...
pip install pyinstaller --quiet

echo [2/3] Building Instagram Stream EXE...
:: --noconfirm ensures it overwrites the previous build without asking
pyinstaller --onefile --windowed --icon=IGTV.jpg --name=24x7Live_Instagram --noconfirm InstagramLiveStreamFolder.py

echo [3/3] Signing the Executable for %COMPANY_NAME%...
%SIGNTOOL_PATH% sign /f %PFX_PATH% /p %PFX_PASS% /fd SHA256 /t http://timestamp.digicert.com "dist\24x7Live_Instagram.exe"

echo.
echo ---------------------------------------------------
echo SUCCESS! Your signed Instagram EXE is in the 'dist' folder.
echo ---------------------------------------------------
pause