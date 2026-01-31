@echo off
setlocal

:: --- CONFIGURATION ---
set COMPANY_NAME=24x7LiveStream
set PFX_PATH=C:\Users\surface\Documents\24x7.pfx
set PFX_PASS=YourPassword123
:: Update this path to your actual signtool location if different
set SIGNTOOL_PATH="C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"

echo [1/4] Installing PyInstaller...
pip install pyinstaller --quiet

echo [2/4] Building Instagram Stream EXE...
cd IGstream
pyinstaller --onefile --windowed --icon=IGTV.jpg --name=24x7Live_Instagram InstagramLiveStreamFolder.py
cd ..

echo [3/4] Building YouTube Stream EXE...
cd YTstream
pyinstaller --onefile --windowed --icon=YouTubeLiveStream.jpg --name=24x7Live_YouTube YouTubeLiveStreamFolder.py
cd ..

echo [4/4] Signing Executables...
%SIGNTOOL_PATH% sign /f %PFX_PATH% /p %PFX_PASS% /fd SHA256 /t http://timestamp.digicert.com "IGstream\dist\24x7Live_Instagram.exe"
%SIGNTOOL_PATH% sign /f %PFX_PATH% /p %PFX_PASS% /fd SHA256 /t http://timestamp.digicert.com "YTstream\dist\24x7Live_YouTube.exe"

echo.
echo ---------------------------------------------------
echo DONE! Your signed EXEs are in their respective /dist folders.
echo ---------------------------------------------------
pause