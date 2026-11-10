@echo off
rem Kullanim: calistir.bat baslangic.json komutlar.jsonl > sonuclar.jsonl
chcp 65001 >nul
rem "python" yoksa (veya Microsoft Store kisayoluysa) py baslaticisini dene.
python --version >nul 2>&1
if errorlevel 1 (
    py -3 "%~dp0calistir.py" %*
) else (
    python "%~dp0calistir.py" %*
)
