@echo off
:loop
echo Запуск SSH-туннеля...
ssh -o ServerAliveInterval=60 -o ExitOnForwardFailure=yes -R 80:localhost:8080 serveo.net
echo Туннель упал. Переподключение через 5 секунд...
timeout /t 5 >nul
goto loop