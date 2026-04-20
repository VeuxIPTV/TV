@echo off
start /min ssh -o ServerAliveInterval=60 -R 80:localhost:8080 serveo.net