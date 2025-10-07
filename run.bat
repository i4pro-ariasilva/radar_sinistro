@echo off
cd /d "%~dp0"
echo 🌦️ Iniciando Radar de Sinistro...
streamlit run app.py --server.port 8501
pause