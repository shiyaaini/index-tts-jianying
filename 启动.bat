@echo off
setlocal enabledelayedexpansion

:: 获取当前脚本所在路径
set "ROOT_DIR=%~dp0"

:: 检查路径结尾是否有反斜杠，确保路径格式正确
if "!ROOT_DIR:~-1!"=="\" set "ROOT_DIR=!ROOT_DIR:~0,-1!"

:: 添加ffmpeg到环境变量
set "PATH=%PATH%;!ROOT_DIR!\ffmpeg\bin"
echo FFmpeg环境变量已设置: !ROOT_DIR!\ffmpeg\bin

:: 执行Python程序
echo 正在启动程序...
echo 项目路径: !ROOT_DIR!
cd /d "!ROOT_DIR!"
.\python10\python.exe app.py

:: 程序结束后暂停
echo.
echo 程序执行完毕
pause