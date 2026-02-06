@echo off
title The Blade of Truth - Launch All Apps
color 0A
powershell -ExecutionPolicy Bypass -File "%~dp0Activate-All-Apps.ps1"
pause
