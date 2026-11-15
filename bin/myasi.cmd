@echo off
rem myasi wrapper for cmd.exe. Prefers the py launcher (python may point to another venv).
setlocal
set "SCRIPT=%~dp0..\scripts\myasi.py"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0myasi.py"
set PYTHONDONTWRITEBYTECODE=1
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%SCRIPT%" %*
) else (
  python "%SCRIPT%" %*
)
exit /b %errorlevel%
