@echo off
title Инфоканал (автозапуск туннеля)
cd /d "C:\Репозиторий github\TV\HLS"

:: Проверяем, запущен ли сервер (live.py). Если нет — запускаем в фоне.
tasklist /fi "imagename eq python.exe" | find "live_stream.py" >nul
if errorlevel 1 (
    echo [СЕРВЕР] Запуск live_stream.py...
    start /min py live.py
    timeout /t 5
) else (
    echo [СЕРВЕР] Уже работает.
)

:loop
echo [Tunnel] Connect to Tunnel...
ssh -i "$env:USERPROFILE\.ssh\serveo_key" -o ServerAliveInterval=30 -R veuxtv:80:localhost:8080 serveo.net

echo [Tunnel] Connection close. Reboot to 10 second...
timeout /t 10
goto loop