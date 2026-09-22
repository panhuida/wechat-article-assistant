@echo off
setlocal DisableDelayedExpansion
for %%I in ("%~dp0..") do set "WECHAT_ASSISTANT_HOME=%%~fI"
set "PYTHONUTF8=1"
if not exist "%WECHAT_ASSISTANT_HOME%\.venv\Scripts\python.exe" (
    >&2 echo Python environment missing. Run uv sync in "%WECHAT_ASSISTANT_HOME%".
    exit /b 1
)
"%WECHAT_ASSISTANT_HOME%\.venv\Scripts\python.exe" -X utf8 "%WECHAT_ASSISTANT_HOME%\wechat-cli.py" %*
exit /b %errorlevel%
