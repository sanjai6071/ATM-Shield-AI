@echo off
title Senco Face Concealment & Masking Monitor
cd /d "%~dp0"

echo ===================================================================
echo   SENCO FACE CONCEALMENT & MASKING SURVEILLANCE ENGINE
echo ===================================================================
echo [1] Running Webcam Stream (Device 0)...
echo Press 'q' inside the video window to stop.
echo Press 's' to manually save an incident snapshot.
echo ===================================================================

python main_stream.py --source 0

pause
