@echo off
echo 正在启动文本转语音系统...
echo.

REM 激活conda环境
call conda activate index-tts

REM 启动应用
python app.py

REM 如果应用意外关闭，暂停显示
pause 