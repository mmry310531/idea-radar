@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM ============================================================
REM  Idea 法規雷達 - 雙擊就跑
REM  第一次執行會自動建立基線 (state.json)，之後每次只報異動。
REM  被排程呼叫時請加參數 quiet，才不會卡在 pause。
REM ============================================================

echo.
echo   Idea Radar
echo   ----------------------------------------
echo   folder: %cd%
echo.

REM ---------- 1. 找 Python ----------
set "PY="
py -3 --version >nul 2>&1
if %errorlevel%==0 set "PY=py -3"
if not defined PY (
  python --version >nul 2>&1
  if !errorlevel!==0 set "PY=python"
)
if not defined PY goto :nopython

for /f "tokens=*" %%V in ('%PY% --version 2^>^&1') do set "PYVER=%%V"
echo   [1/4] Python: !PYVER!

REM ---------- 2. 確認 requests ----------
%PY% -c "import requests" >nul 2>&1
if not %errorlevel%==0 (
  echo   [2/4] installing requests ...
  %PY% -m pip install --quiet --disable-pip-version-check requests
  %PY% -c "import requests" >nul 2>&1
  if not !errorlevel!==0 goto :nopip
) else (
  echo   [2/4] requests: ok
)

REM ---------- 3. 第一次跑就建基線 ----------
set "MODE="
if not exist "state.json" (
  set "MODE=--init"
  echo   [3/4] first run - building baseline ^(no digest this time^)
) else (
  echo   [3/4] incremental scan
)

REM ---------- 4. 跑 ----------
echo   [4/4] scanning ...
echo   ----------------------------------------
echo.
%PY% radar.py --out out %MODE%
set "RC=%errorlevel%"
echo.
echo   ----------------------------------------

REM 被排程呼叫時 (quiet) 一律直接結束，不開記事本、不 pause，
REM 否則排程會卡在等人按鍵，下週就再也不會跑了。
if "%~1"=="quiet" goto :eof

if not "%RC%"=="0" (
  echo   radar.py exited with code %RC%
  goto :finish
)

REM ---------- 打開最新的摘要 ----------
set "LATEST="
for /f "delims=" %%F in ('dir /b /o-d "out\digest-*.md" 2^>nul') do (
  if not defined LATEST set "LATEST=out\%%F"
)

if defined LATEST (
  echo   opening: !LATEST!
  start "" notepad "!LATEST!"
) else (
  echo   no digest produced.
)

:finish
echo.
pause
goto :eof

REM ============================================================
:nopython
echo.
echo   [X] 找不到 Python。
echo.
echo       到 https://www.python.org/downloads/ 裝一個，
echo       安裝畫面第一頁記得勾 "Add python.exe to PATH"，
echo       裝完把這個視窗關掉、重新雙擊一次就好。
echo.
pause
goto :eof

:nopip
echo.
echo   [X] requests 裝不起來（多半是公司網路擋 pip）。
echo.
echo       手動試試看：
echo         %PY% -m pip install requests
echo       還是不行的話，用手機熱點跑一次安裝就好，之後就不用再裝。
echo.
pause
goto :eof
