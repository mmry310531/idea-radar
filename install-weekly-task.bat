@echo off
chcp 65001 >nul 2>&1
setlocal
cd /d "%~dp0"

REM ============================================================
REM  把 radar.bat 註冊成「每週二 03:00 自動跑」的 Windows 排程。
REM  只需要跑這一次。之後就完全不用管它。
REM  想取消：把下面那行 schtasks /create 換成 /delete 再跑一次，
REM  或直接在「工作排程器」裡刪掉 IdeaRadar。
REM ============================================================

echo.
echo   把 Idea Radar 註冊成每週二 03:00 自動執行
echo   ----------------------------------------
echo   target: "%~dp0radar.bat"
echo.

schtasks /create ^
  /tn "IdeaRadar" ^
  /tr "\"%~dp0radar.bat\" quiet" ^
  /sc weekly /d TUE /st 03:00 ^
  /f

if %errorlevel%==0 (
  echo.
  echo   [OK] 註冊完成。
  echo.
  echo   注意：電腦在那個時間必須是開機的（睡眠不算）。
  echo   如果你的桌機常關機，改用 GitHub Actions 版本比較實際，
  echo   設定方式在 radar-setup.md。
  echo.
  echo   想馬上測一次： schtasks /run /tn IdeaRadar
) else (
  echo.
  echo   [X] 註冊失敗。多半是權限問題 —
  echo       在這個 .bat 上按右鍵，選「以系統管理員身分執行」再試一次。
)

echo.
pause
