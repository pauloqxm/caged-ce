@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Convertendo novo_caged.csv para o formato de dados_caged.csv...
echo.

"C:\Users\paulo.ferreira\AppData\Local\Programs\Python\Python313\python.exe" "%~dp0converter_caged.py"

if errorlevel 1 (
    echo.
    echo ERRO na conversao.
    pause
    exit /b 1
)

echo.
pause
