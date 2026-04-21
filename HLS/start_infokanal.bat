@echo off
title Serveo Tunnel Auto-Restart
cd /d "C:\Репозиторий github\TV\HLS"

:loop
echo [ТУННЕЛЬ] Connect to Tunnel...
ssh -i "%USERPROFILE%\.ssh\serveo_key" -o ServerAliveInterval=30 -o TCPKeepAlive=yes -o ExitOnForwardFailure=yes -R veuxtv:80:localhost:8080 serveo.net

echo [ТУННЕЛЬ] Connection Close. Reboot to 10 second...
timeout /t 10
goto loop