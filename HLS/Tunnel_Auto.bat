@echo off
title Tunnel Serveo (авто-перезапуск)

:loop
echo Connect to Tunnel...
ssh -i "$env:USERPROFILE\.ssh\serveo_key" -o ServerAliveInterval=30 -R veuxtv:80:localhost:8080 serveo.net
echo Connection Close. Reboot to 10 second...
timeout /t 10
goto loop