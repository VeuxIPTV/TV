@echo off
start /min ssh -i ~/.ssh/lhr_key -R 80:localhost:8080 nokey@localhost.run