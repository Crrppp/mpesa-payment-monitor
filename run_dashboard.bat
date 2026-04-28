@echo off
call venv\Scripts\activate
cd dashboard
streamlit run app.py
pause