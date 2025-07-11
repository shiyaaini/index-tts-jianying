@echo off
title 文本转语音系统启动器
echo 正在启动文本转语音系统...
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查是否安装了conda
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未检测到conda环境，请先安装Anaconda或Miniconda。
    echo 请访问: https://www.anaconda.com/download
    pause
    exit /b 1
)

REM 初始化conda
call conda.bat activate base || (
    echo 错误: conda初始化失败
    pause
    exit /b 1
)

REM 激活项目环境
call conda.bat activate index-tts || (
    echo 错误: 未找到index-tts环境，请先创建环境
    echo 创建方法: conda create -n index-tts python=3.10
    pause
    exit /b 1
)

REM 检查是否有app.py文件
if not exist app.py (
    echo 错误: 未找到app.py文件，请确认当前目录是否为项目根目录
    echo 当前目录: %cd%
    pause
    exit /b 1
)

echo 环境检查通过，正在启动应用...
echo.

REM 启动应用
python app.py

REM 如果应用意外关闭，显示退出码
if %errorlevel% neq 0 (
    echo.
    echo 应用异常退出，错误代码: %errorlevel%
    echo 如遇问题，请加入QQ群: 700598581寻求帮助
)

echo.
echo 按任意键退出...
pause >nul