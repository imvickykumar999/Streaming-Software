@echo off
setlocal

:: --- CONFIGURATION ---
set COMPANY_NAME=24x7LiveStream
set PFX_PATH=C:\Users\surface\Documents\24x7.pfx
set PFX_PASS=YourPassword123
:: Note: Verify your signtool path. It usually matches the version folder below.
set SIGNTOOL_PATH="C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"

echo [1/3] Installing/Updating PyInstaller...
pip install pyinstaller --quiet

echo [2/3] Building YouTube Stream EXE...
:: --name sets the final filename. --noconfirm overwrites old builds automatically.
pyinstaller --onefile --windowed --icon=YouTubeLiveStream.jpg --name=24x7Live_YouTube --noconfirm YouTubeLiveStreamFolder.py

echo [3/3] Signing the Executable with %COMPANY_NAME%...
%SIGNTOOL_PATH% sign /f %PFX_PATH% /p %PFX_PASS% /fd SHA256 /t http://timestamp.digicert.com "dist\24x7Live_YouTube.exe"

echo.
echo ---------------------------------------------------
echo SUCCESS! Your signed EXE is in the 'dist' folder.
echo ---------------------------------------------------
pause