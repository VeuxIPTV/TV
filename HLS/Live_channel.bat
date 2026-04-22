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

:loop
echo [Tunnel] Connect to Tunnel...
ssh -i "%USERPROFILE%\.ssh\serveo_key" -o ServerAliveInterval=30 -o TCPKeepAlive=yes -R veuxtv:80:localhost:8080 serveo.net
echo [Tunnel] Connection Close. Reboot to 5 second...
timeout /t 5
goto loop