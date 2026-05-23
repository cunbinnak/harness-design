@echo off
setlocal EnableDelayedExpansion
set "BRIDGE=%~dp0ide_bridge.py"
where py >nul 2>nul (
  py "%BRIDGE%" %*
  exit /b !ERRORLEVEL!
)
where python >nul 2>nul (
  python "%BRIDGE%" %*
  exit /b !ERRORLEVEL!
)
echo {"permission":"allow"}
exit /b 0
