@echo off
title Serveo Tunnel Auto-Restart
cd /d "C:\Репозиторий github\TV\HLS"

tasklist /fi "imagename eq python.exe" | find "live_stream.py" >nul
if errorlevel 1 (
    echo [Server] Launching the translator
    start /min py live.py
    timeout /t 5
) else (
    echo [Server] The translator is running.
)

taskkill /f /im ssh.exe 2>nul
timeout /t 1

:loop
echo Connect to Tunnel...
ssh -i "%USERPROFILE%\.ssh\serveo_key" ^
    -o ServerAliveInterval=30 ^
    -o ServerAliveCountMax=3 ^
    -o TCPKeepAlive=yes ^
    -o ExitOnForwardFailure=yes ^
    -R veuxtv:80:localhost:8080 serveo.net
echo Connection Close. Reboot...
timeout /t 0
goto loop