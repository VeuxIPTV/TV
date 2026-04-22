@echo off
title Tunnel Serveo

taskkill /f /im ssh.exe 2>nul
timeout /t 1@echo off
title Serveo Tunnel with Monitoring & Auto-Cleanup
cd /d "C:\Репозиторий github\TV\HLS"

:: ========== НАСТРОЙКИ ==========
set DOMAIN=veuxtv
set SSH_KEY=%USERPROFILE%\.ssh\serveo_key
set LOCAL_PORT=8080
set REMOTE_PORT=80
set SERVE_HOST=serveo.net
:: ==============================

echo ================================================
echo   Serveo Tunnel Monitor v1.0
echo   DOMAIN: %DOMAIN%.%SERVE_HOST%
echo ================================================

:pre_loop
echo [%date% %time%] Cleaning up old SSH processes...
taskkill /f /im ssh.exe >nul 2>&1
timeout /t 2 >nul

echo Checking the local server http://localhost:%LOCAL_PORT%...
curl -s -o nul -w "%%{http_code}" http://localhost:%LOCAL_PORT% > status.tmp
set /p HTTP_STATUS=<status.tmp
del status.tmp
if "%HTTP_STATUS%"=="200" (
    echo [OK] The local server is responding.
) else (
    echo [WARN] The local server did not respond to 200! Probably a live_stream.py is not running.
)

echo Ping check before %SERVE_HOST%...
ping -n 2 %SERVE_HOST% | findstr /i "time=" > ping.tmp
if %errorlevel% equ 0 (
    for /f "tokens=7 delims== " %%a in (ping.tmp) do set PING_TIME=%%a
    echo [OK] Ping before %SERVE_HOST%: %PING_TIME%
) else (
    echo [WARN] Ping before %SERVE_HOST% failed. Check the network/VPN.
)
del ping.tmp 2>nul

echo ================================================
echo Launching the tunnel...
echo ================================================

:loop

echo [%date% %time%] Establishing a connection with %SERVE_HOST%...
ssh -i "%SSH_KEY%" ^
    -o ServerAliveInterval=30 ^
    -o ServerAliveCountMax=3 ^
    -o TCPKeepAlive=yes ^
    -o ExitOnForwardFailure=yes ^
    -R %DOMAIN%:%REMOTE_PORT%:localhost:%LOCAL_PORT% %SERVE_HOST%

echo [%date% %time%] The tunnel is torn up. Waiting time is 5 seconds...

taskkill /f /im ssh.exe >nul 2>&1

echo Checking the connection speed...
ping -n 3 8.8.8.8 | findstr /i "time=" > speed.tmp
if %errorlevel% equ 0 (
    for /f "tokens=7 delims== " %%a in (speed.tmp) do set PING_TIME=%%a
    echo Current ping: %PING_TIME%
) else (
    echo Couldn't check the speed. Maybe there is no internet connection.
)
del speed.tmp 2>nul

timeout /t 3
goto pre_loop

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