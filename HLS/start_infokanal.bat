@echo off
title Инфоканал (автозапуск туннеля)
cd /d "C:\Репозиторий github\TV\HLS"

:: Проверяем, запущен ли сервер (live_stream.py). Если нет — запускаем в фоне.
tasklist /fi "imagename eq python.exe" | find "live_stream.py" >nul
if errorlevel 1 (
    echo [СЕРВЕР] Запуск live_stream.py...
    start /min py live_stream.py
    timeout /t 5
) else (
    echo [СЕРВЕР] Уже работает.
)

:: Бесконечный цикл для туннеля
:loop
echo [ТУННЕЛЬ] Подключение к serveo.net с доменом veuxiptv-tv...
ssh -i "%USERPROFILE%\.ssh\serveo_key" -o ServerAliveInterval=30 -o TCPKeepAlive=yes -o ExitOnForwardFailure=yes -R veuxiptv-tv:80:localhost:8080 serveo.net

echo [ТУННЕЛЬ] Соединение разорвано. Перезапуск через 10 секунд...
timeout /t 10
goto loop