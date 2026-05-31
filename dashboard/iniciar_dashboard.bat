@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PYTHON="C:\Users\paulo.ferreira\AppData\Local\Programs\Python\Python313\python.exe"

echo.
echo ========================================
echo   Dashboard CAGED - Ceara
echo ========================================
echo.

echo [1/2] Preparando dados...
%PYTHON% "%~dp0prepare_data.py"
if errorlevel 1 (
    echo ERRO ao preparar dados.
    pause
    exit /b 1
)

echo.
echo [2/2] Iniciando servidor local...
echo.
%PYTHON% "%~dp0server.py"

pause
