@echo off
title Инфоканал (Сервер + Туннель Serveo)
cd /d "C:\Репозиторий github\TV\HLS"

echo ========================================
echo   ЗАПУСК ИНФОКАНАЛА
echo ========================================
echo [1/2] Запуск HLS-сервера (live_stream.py)...
start /min py live.py
timeout /t 10

echo [2/2] Подключение туннеля...
:loop
ssh -i "$env:USERPROFILE\.ssh\serveo_key" -o ServerAliveInterval=30 -R veuxtv:80:localhost:8080 serveo.net
echo --------------------------------------------------------
echo Туннель разорван. Перезапуск через 10 секунд...
timeout /t 10
goto loop