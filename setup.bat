@echo off
echo ClaudeNation ID App Setup
echo ========================
echo.

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.8 or newer.
    echo Visit https://www.python.org/downloads/ to download Python.
    pause
    exit /b 1
)

echo Setting up virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Creating shortcut to launch the app...
echo.

REM Create a VBS script to make the shortcut
echo Set WshShell = CreateObject^("WScript.Shell"^) > CreateShortcut.vbs
echo strDesktop = WshShell.SpecialFolders^("Desktop"^) >> CreateShortcut.vbs
echo Set objShortcut = WshShell.CreateShortcut^(strDesktop ^& "\ClaudeNation ID App.lnk"^) >> CreateShortcut.vbs
echo objShortcut.TargetPath = "%~dp0run_app.bat" >> CreateShortcut.vbs
echo objShortcut.WorkingDirectory = "%~dp0" >> CreateShortcut.vbs
echo objShortcut.IconLocation = "%~dp0claudenation01light.jpg" >> CreateShortcut.vbs
echo objShortcut.Description = "ClaudeNation ID System" >> CreateShortcut.vbs
echo objShortcut.Save >> CreateShortcut.vbs

cscript /nologo CreateShortcut.vbs
del CreateShortcut.vbs

REM Create the batch file to run the app
echo @echo off > run_app.bat
echo call venv\Scripts\activate.bat >> run_app.bat
echo echo Starting ClaudeNation ID App... >> run_app.bat
echo echo. >> run_app.bat
echo echo Please wait, the app will open in your browser shortly. >> run_app.bat
echo echo. >> run_app.bat
echo streamlit run app.py >> run_app.bat
echo pause >> run_app.bat

echo.
echo Setup complete!
echo A shortcut 'ClaudeNation ID App' has been created on your desktop.
echo.
echo Would you like to start the app now? (Y/N)
set /p choice=

if /i "%choice%"=="Y" (
    call run_app.bat
) else (
    echo You can start the app later by double-clicking the desktop shortcut.
)

pause