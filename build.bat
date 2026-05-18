@echo off
REM Noise Revenger - PyInstaller Build Script
REM This script builds the distributable package

echo ========================================
echo Noise Revenger - Building Distribution
echo ========================================
echo.

REM Clean previous builds
if exist "dist" (
    echo Cleaning previous build...
    rmdir /s /q dist
)
if exist "build" (
    rmdir /s /q build
)

REM Run PyInstaller
echo Running PyInstaller...
uv run pyinstaller noise_revenger.spec

if errorlevel 1 (
    echo.
    echo BUILD FAILED!
    exit /b 1
)

echo.
echo Copying config and sounds to dist folder...

REM Copy config directory
if not exist "dist\NoiseRevenger\config" mkdir "dist\NoiseRevenger\config"
copy /Y "config\settings.yaml" "dist\NoiseRevenger\config\"

REM Copy sounds directory
if not exist "dist\NoiseRevenger\sounds" mkdir "dist\NoiseRevenger\sounds"
copy /Y "sounds\*.wav" "dist\NoiseRevenger\sounds\" 2>nul

REM Create logs directory
if not exist "dist\NoiseRevenger\logs" mkdir "dist\NoiseRevenger\logs"
if not exist "dist\NoiseRevenger\logs\clips" mkdir "dist\NoiseRevenger\logs\clips"

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Distribution folder: dist\NoiseRevenger\
echo.
echo Directory structure:
echo   NoiseRevenger/
echo   ├── NoiseRevenger.exe    (main executable)
echo   ├── config/
echo   │   └── settings.yaml    (editable config)
echo   ├── sounds/              (replaceable audio files)
echo   │   ├── alert_mild.wav
echo   │   ├── alert_medium.wav
echo   │   └── alert_strong.wav
echo   └── logs/                (runtime logs)
echo.
echo To distribute: zip the entire dist\NoiseRevenger folder
echo and send to your friend. They just need to extract and
echo run NoiseRevenger.exe.
echo.
