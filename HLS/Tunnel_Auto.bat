@echo off
title Tunnel Serveo

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