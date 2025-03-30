@echo off
echo ClaudeNation ID App Setup for WSL
echo ================================
echo.

REM Get the current directory
set CURRENT_DIR=%CD%

REM Extract WSL path components
for /f "tokens=1,2,3,4,5 delims=\" %%a in ("%CURRENT_DIR%") do (
    set WSL_DISTRO=%%b
    set WSL_PATH=/%%c/%%d/%%e
)

echo Setting up in WSL distribution: %WSL_DISTRO%
echo WSL Path: %WSL_PATH%
echo.

REM Create a temp script to run in WSL
echo #!/bin/bash > wsl_setup.sh
echo cd %WSL_PATH% >> wsl_setup.sh
echo echo "Setting up Python virtual environment..." >> wsl_setup.sh
echo python3 -m venv venv >> wsl_setup.sh
echo source venv/bin/activate >> wsl_setup.sh
echo echo "Installing dependencies..." >> wsl_setup.sh
echo pip install -r requirements.txt >> wsl_setup.sh
echo echo "Setup complete!" >> wsl_setup.sh
echo echo "Creating launcher script..." >> wsl_setup.sh
echo echo "#!/bin/bash" ^> run_app.sh >> wsl_setup.sh
echo echo "cd %WSL_PATH%" ^>^> run_app.sh >> wsl_setup.sh
echo echo "source venv/bin/activate" ^>^> run_app.sh >> wsl_setup.sh
echo echo "streamlit run app.py" ^>^> run_app.sh >> wsl_setup.sh
echo chmod +x run_app.sh >> wsl_setup.sh

REM Run the script in WSL
wsl chmod +x wsl_setup.sh
wsl ./wsl_setup.sh
wsl rm wsl_setup.sh

REM Create Windows shortcut to run the app
echo Set WshShell = CreateObject("WScript.Shell") > %TEMP%\CreateShortcut.vbs
echo strDesktop = WshShell.SpecialFolders("Desktop") >> %TEMP%\CreateShortcut.vbs
echo Set objShortcut = WshShell.CreateShortcut(strDesktop ^& "\ClaudeNation ID App (WSL).lnk") >> %TEMP%\CreateShortcut.vbs
echo objShortcut.TargetPath = "wsl" >> %TEMP%\CreateShortcut.vbs
echo objShortcut.Arguments = "bash -c 'cd %WSL_PATH% && ./run_app.sh'" >> %TEMP%\CreateShortcut.vbs
echo objShortcut.WorkingDirectory = "%USERPROFILE%" >> %TEMP%\CreateShortcut.vbs
echo objShortcut.WindowStyle = 1 >> %TEMP%\CreateShortcut.vbs
echo objShortcut.Description = "ClaudeNation ID System (WSL)" >> %TEMP%\CreateShortcut.vbs
echo objShortcut.Save >> %TEMP%\CreateShortcut.vbs

cscript /nologo %TEMP%\CreateShortcut.vbs
del %TEMP%\CreateShortcut.vbs

echo.
echo Setup complete!
echo A shortcut 'ClaudeNation ID App (WSL)' has been created on your desktop.
echo.
echo Would you like to start the app now? (Y/N)
set /p choice=

if /i "%choice%"=="Y" (
    wsl bash -c "cd %WSL_PATH% && ./run_app.sh"
) else (
    echo You can start the app later by double-clicking the desktop shortcut.
)

pause