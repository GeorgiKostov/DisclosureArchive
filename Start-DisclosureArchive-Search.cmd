@echo off
setlocal

set "ROOT=%~dp0"
set "DB=%ROOT%indexes\uap_release.sqlite"
set "PY=%ROOT%.venv\Scripts\python.exe"
set "URL=http://127.0.0.1:8765"

cd /d "%ROOT%"

if not exist "%PY%" (
  echo Could not find the project Python environment:
  echo   %PY%
  echo.
  echo Run setup first, then try this launcher again.
  pause
  exit /b 1
)

if not exist "%DB%" (
  echo Could not find the search database:
  echo   %DB%
  echo.
  echo Rebuild or copy indexes\uap_release.sqlite, then try this launcher again.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$portOpen = Test-NetConnection -ComputerName 127.0.0.1 -Port 8765 -InformationLevel Quiet -WarningAction SilentlyContinue; if ($portOpen) { Start-Process '%URL%'; exit 0 } else { exit 1 }"

if %ERRORLEVEL% EQU 0 (
  echo DisclosureArchive Search is already running.
  echo Opened %URL%
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 2" >nul 2>nul
  exit /b 0
)

echo Starting DisclosureArchive Search...
echo.
echo Browser URL:
echo   %URL%
echo.
echo Keep this window open while searching. Close it to stop the local server.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 2; Start-Process '%URL%'" >nul 2>nul
"%PY%" -m ufo_indexer.web --db "%DB%" --host 127.0.0.1 --port 8765

endlocal
