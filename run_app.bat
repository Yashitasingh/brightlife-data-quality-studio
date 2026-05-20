@echo off
start cmd /k "uvicorn backend.app.main:app --reload"
timeout /t 3
start cmd /k "streamlit run frontend/app.py"
