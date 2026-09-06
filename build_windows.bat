@echo off
setlocal enabledelayedexpansion
title Compilar scrcpy_update para Windows

echo ============================================================
echo   Compilador de scrcpy_update para Windows (.exe)
echo ============================================================
echo.

:: 1. Verificar Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado en PATH.
    echo Por favor, instala Python 3.10+ y asegurate de marcar "Add to PATH".
    pause
    exit /b 1
)

:: 2. Auto-incrementar version
set "SCRIPT_DIR=%~dp0"
set "VERSION_FILE=%SCRIPT_DIR%VERSION"

if not exist "%VERSION_FILE%" (
    echo 1.0.0 > "%VERSION_FILE%"
)

set /p CURRENT_VERSION=<"%VERSION_FILE%"
:: Limpiar posibles espacios
for /f "tokens=* delims= " %%a in ("%CURRENT_VERSION%") do set CURRENT_VERSION=%%a

for /f "tokens=1,2,3 delims=." %%a in ("%CURRENT_VERSION%") do (
    set V_MAJOR=%%a
    set V_MINOR=%%b
    set V_PATCH=%%c
)

set /a V_PATCH+=1
set "NEW_VERSION=%V_MAJOR%.%V_MINOR%.%V_PATCH%"
echo %NEW_VERSION% > "%VERSION_FILE%"
echo [*] Version incrementada a: %NEW_VERSION%

:: Actualizar APP_VERSION en main.py usando python
python -c "v='%NEW_VERSION%'; p='main.py'; open(p, 'w', encoding='utf-8').write('\n'.join([f'APP_VERSION = \"{v}\"' if line.startswith('APP_VERSION =') else line for line in open(p, encoding='utf-8').read().splitlines()]))"

:: 3. Instalar dependencias necesarias
echo [*] Verificando dependencias...
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

:: 4. Obtener ruta de customtkinter para adjuntar temas y assets
for /f "delims=" %%i in ('python -c "import customtkinter, os; print(os.path.dirname(customtkinter.__file__))"') do set "CTK_PATH=%%i"

:: 5. Limpieza previa
if exist "%SCRIPT_DIR%build\pyinstaller_work_win" rmdir /s /q "%SCRIPT_DIR%build\pyinstaller_work_win"
if not exist "%SCRIPT_DIR%dist" mkdir "%SCRIPT_DIR%dist"

:: 6. Compilar con PyInstaller
echo [*] Compilando ejecutable standalone para Windows...
pyinstaller ^
    --onefile ^
    --name "scrcpy_update" ^
    --add-data "%CTK_PATH%;customtkinter" ^
    --add-data "%SCRIPT_DIR%.env;." ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "customtkinter" ^
    --collect-all "customtkinter" ^
    --distpath "%SCRIPT_DIR%dist" ^
    --workpath "%SCRIPT_DIR%build\pyinstaller_work_win" ^
    --specpath "%SCRIPT_DIR%build" ^
    --noconfirm ^
    --clean ^
    "%SCRIPT_DIR%main.py"

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo   [OK] Compilacion completada con exito!
    echo   Archivo generado: dist\scrcpy_update.exe
    echo ============================================================
) else (
    echo.
    echo [ERROR] La compilacion ha fallado. Revisa la salida de PyInstaller.
)

pause
