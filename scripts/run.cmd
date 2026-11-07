@echo off
rem langstats launcher for Windows (cmd.exe / PowerShell).
rem Finds a Python 3.9+ interpreter and runs langstats.py with the given arguments.
rem Set LANGSTATS_PYTHON to force a specific interpreter.
setlocal
set "SCRIPT=%~dp0langstats.py"
set "CHECK=import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"
if defined LANGSTATS_PYTHON goto custom
python3 -c "%CHECK%" >nul 2>&1 && goto python3
python -c "%CHECK%" >nul 2>&1 && goto python
py -3 -c "%CHECK%" >nul 2>&1 && goto pylauncher
echo langstats: Python 3.9+ not found, tried python3, python and py -3. Set LANGSTATS_PYTHON. 1>&2
exit /b 0
:custom
"%LANGSTATS_PYTHON%" "%SCRIPT%" %*
exit /b %errorlevel%
:python3
python3 "%SCRIPT%" %*
exit /b %errorlevel%
:python
python "%SCRIPT%" %*
exit /b %errorlevel%
:pylauncher
py -3 "%SCRIPT%" %*
exit /b %errorlevel%
