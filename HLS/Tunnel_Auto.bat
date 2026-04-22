@echo off
title Tunnel Serveo (авто-перезапуск)

taskkill /f /im ssh.exe 2>nul
timeout /t 3

:loop
echo Connect to Tunnel...
ssh -i "%USERPROFILE%\.ssh\serveo_key" ^
    -o ServerAliveInterval=30 ^
    -o ServerAliveCountMax=3 ^
    -o TCPKeepAlive=yes ^
    -o ExitOnForwardFailure=yes ^
    -R veuxtv:8080:localhost:8080 serveo.net
echo Connection Close. Reboot...
timeout /t 0
goto loop