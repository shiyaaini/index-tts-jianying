@echo off
setlocal enabledelayedexpansion

:: 获取当前脚本所在路径
set "ROOT_DIR=%~dp0"

:: 检查路径结尾是否有反斜杠，确保路径格式正确
if "!ROOT_DIR:~-1!"=="\" set "ROOT_DIR=!ROOT_DIR:~0,-1!"

:: 执行Python程序
echo 正在启动程序...
echo 项目路径: !ROOT_DIR!
cd /d "!ROOT_DIR!"

:: 设置PYTHONPATH环境变量，添加当前目录到Python模块搜索路径
set "PYTHONPATH=!ROOT_DIR!;!PYTHONPATH!"

:: 运行Python程序
.\python10\python.exe main.py

:: 程序结束后暂停
echo.
echo 程序执行完毕
pause