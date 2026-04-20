@echo off
:loop
echo Запуск SSH-туннеля...
ssh -i ~/.ssh/lhr_key -R 80:localhost:8080 nokey@localhost.run
echo Туннель упал. Переподключение через 5 секунд...
timeout /t 5 >nul
goto loop