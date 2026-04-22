@echo off
title Tunnel Serveo (авто-перезапуск)

:loop
echo Connect to Tunnel...
ssh -i "%USERPROFILE%\.ssh\serveo_key" -o ServerAliveInterval=30 -o TCPKeepAlive=yes -R veuxtv:8080:localhost:8080 serveo.net
echo Connection Close. Reboot...
timeout /t 0
goto loop