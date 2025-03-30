@echo off 
call venv\Scripts\activate.bat 
echo Starting ClaudeNation ID App... 
echo. 
echo Please wait, the app will open in your browser shortly. 
echo. 
streamlit run app.py 
pause 
