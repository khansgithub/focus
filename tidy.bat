@echo off
REM Check if argument was provided
if "%~1"=="" (
    echo Usage: %~nx0 filename.py
    exit /b 1
)

set FILE=%~1

echo Running formatters and linters on %FILE%...

isort %FILE%
black %FILE%
ruff check %FILE% --fix
mypy %FILE%

echo Done.