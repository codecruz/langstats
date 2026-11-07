@echo off
rem langstats launcher for Windows (cmd.exe / PowerShell).
rem Runs langstats.py with a Python 3.9+ interpreter. The interpreter found the
rem first time is cached in %LANGSTATS_HOME%\.python. Set LANGSTATS_PYTHON to force one.
setlocal
set "SCRIPT=%~dp0cli.py"
set "DATA=%LANGSTATS_HOME%"
if not defined DATA set "DATA=%USERPROFILE%\.claude\langstats"
set "CACHE=%DATA%\.python"
if defined LANGSTATS_PYTHON goto custom
set "PY="
if exist "%CACHE%" set /p PY=<"%CACHE%"
if not defined PY goto discover
%PY% -I "%SCRIPT%" %*
if not errorlevel 9009 exit /b %errorlevel%
del "%CACHE%" >nul 2>&1
:discover
set "CHECK=import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"
python3 -c "%CHECK%" >nul 2>&1 && (set "PY=python3" & goto found)
python -c "%CHECK%" >nul 2>&1 && (set "PY=python" & goto found)
py -3 -c "%CHECK%" >nul 2>&1 && (set "PY=py -3" & goto found)
echo langstats: Python 3.9+ not found, tried python3, python and py -3. Set LANGSTATS_PYTHON. 1>&2
exit /b 0
:found
if not exist "%DATA%" mkdir "%DATA%" >nul 2>&1
>"%CACHE%" echo %PY%
%PY% -I "%SCRIPT%" %*
exit /b %errorlevel%
:custom
"%LANGSTATS_PYTHON%" -I "%SCRIPT%" %*
exit /b %errorlevel%
