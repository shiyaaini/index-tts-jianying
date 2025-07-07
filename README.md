# 文本转语音系统 🎙️

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/shiyaaini/index-tts-jianying?style=flat-square&color=yellow)
![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web框架-green?style=flat-square&logo=flask)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

**基于Python Flask+剪映5.9的文本转语音Web应用程序，使用IndexTTS引擎实现语音合成功能**

</div>

## 📑 目录

- [项目简介](#project-intro)
- [项目结构](#project-structure)
- [功能特性](#features)
- [系统依赖](#system-requirements)
- [常见问题](#faq)
- [运行方法](#how-to-run)
- [剪映替换教程](#jianying-tutorial)
- [去除伴奏](#remove-bgm)
- [交流方式](#communication)
- [赞赏支持](#support)

## 📋 项目简介 {#project-intro}

在此感谢哔哩哔哩：

<div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin: 10px 0; background-color: #f8f9fa;">
  <a href="https://github.com/index-tts/index-tts" target="_blank" style="text-decoration: none; color: #0969da; font-weight: bold;">
    index-tts
  </a>
  <p style="margin: 8px 0 0; color: #666;">IndexTTS 是一种主要基于 XTTS 和 Tortoise 的 GPT 风格的文本转语音 （TTS） 模型。它能够使用拼音纠正汉字的发音，并通过标点符号控制任何位置的停顿。我们增强了系统的多个模块，包括扬声器条件特征表示的改进，以及 BigVGAN2 的集成以优化音频质量。</p>
</div>
通过网盘分享的文件（项目+模型）：github
链接: https://pan.baidu.com/s/1DJFfS14bGSC0ZAq9E-rBMg?pwd=6666 提取码: 6666 
整合包（没有电脑知识的朋友准备的）：
通过网盘分享的文件：整合包
链接: https://pan.baidu.com/s/11mEIKEfWxmEW0r7nxbag0g?pwd=6666 提取码: 6666 
--来自百度网盘超级会员v3的分享

## 📂 项目结构 {#project-structure}

```
index_tts_web/
├── app.py                    # 主应用程序入口
├── config.json               # 配置文件
├── deepseek.py               # DeepSeek相关功能
├── requirements.txt          # 项目依赖
├── README.md                 # 项目说明文档
│
├── font/                     # 字体文件
│   ├── 华为新魏.ttf
│   ├── 华文行楷.ttf
│   └── 楷体.ttf
│
├── model/                    # 模型文件
│   └── checkpoints/          # 检查点文件
│       ├── voice/            # 参考音频
│       │   ├── data.json
│       │   ├── 可莉.wav
│       │   └── 声优.wav
│       ├── bigvgan_discriminator.pth
│       ├── bigvgan_generator.pth
│       ├── config.yaml
│       └── ...
│
├── records/                  # 记录文件
│   └── generation_history.json
│
├── static/                   # 静态资源
│   ├── css/                  # 样式文件
│   ├── images/               # 图片资源
│   ├── js/                   # JavaScript文件
│   └── output/               # 生成的音频输出
│
└── templates/                # HTML模板
    └── index.html
```

## 📁 文件路径说明

| 路径 | 描述 |
|------|------|
| `model/checkpoints/voice` | 参考音频存放位置 |
| `static/output` | 生成的音频文件默认存放位置 |

> **注意**：本项目使用剪映版本为5.9，大于5.9的版本无法兼容使用通过网盘分享的文件：剪映5.9
> 链接: https://pan.baidu.com/s/1q6s2QVcP6F4MKm_qehJmXw?pwd=6666 提取码: 6666 
> --来自百度网盘超级会员v3的分享

## ✨ 功能特性 {#features}

- ✅ 选择不同的语音合成模型
- ✅ 选择参考音频作为语音风格参考
- ✅ 为参考音频添加备注信息
- ✅ 生成、预览和下载合成的语音文件
- ✅ 剪映的音频替换（解决以下问题）：
  - 💰 本人钱包太干净
  - 🔄 开了用一下就不用实在太浪费
  - 🎭 剪映的音色选择不符合个人需求
- ✅ 剪映的文字样式选择（可以下载好看的ttf文件。好看的字体都收费😂）

## 🔧 系统依赖 {#system-requirements}

### 基础环境安装

> 按照index-tts相同的安装过程执行

1. 安装Anaconda（傻瓜式安装，记得勾选环境变量选项）
   - 下载地址：[Anaconda官网](https://www.anaconda.com/download/success)
   - 安装时遇到邮件登录问题，可在链接后加上`/success`继续下载

2. 安装CUDA（有显卡的用户需要安装）
   - 下载地址：[CUDA Toolkit Archive](https://developer.nvidia.com/cuda-toolkit-archive)
   - 选择与您硬件兼容的版本
   - 🚨 **重要**：安装CUDA前先安装Visual Studio，否则会一直卡住
     <img src="./static/images/six.png" alt="VS的安装" style="max-width:100%; height:auto;">

3. 创建并激活conda环境

```bash
# 创建Python 3.10环境
conda create -n index-tts python=3.10
# 激活环境
conda activate index-tts
```

4. 安装依赖项

```bash
# 安装ffmpeg
conda install -c conda-forge ffmpeg

# 安装PyTorch和TorchAudio（根据CUDA版本选择对应命令）
# 可使用nvidia-smi查看CUDA版本
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安装其他依赖
conda install -c conda-forge pynini==2.1.6
pip install WeTextProcessing --no-deps
pip install flask
pip install openai
```

5. 安装index-tts依赖（在项目根目录下执行）

<img src="./static/images/two.png" alt="安装依赖" style="max-width:100%; height:auto;">

报下面错误

```
(index-tts) F:\BaiduNetdiskDownload\index_tts_web>python app.py
Traceback (most recent call last):
  File "F:\BaiduNetdiskDownload\index_tts_web\app.py", line 11, in <module>
    from indextts.infer import IndexTTS
ModuleNotFoundError: No module named 'indextts'
```

请到[index-tts/index-tts: An Industrial-Level Controllable and Efficient Zero-Shot Text-To-Speech System (github.com)](https://github.com/index-tts/index-tts)把项目拉取下来，解压完成后终端运行

```
pip install -e .
```



## ❓ 常见问题 {#faq}

### 1️⃣ CUDA安装缓慢

问题：安装CUDA特别慢  
解决方案：提前安装Visual Studio  
下载地址：[Visual Studio官网](https://visualstudio.microsoft.com/zh-hans/vs/)

### 2️⃣ DeepSpeed加载失败

问题：
```
>> DeepSpeed加载失败，回退到标准推理: No module named 'deepspeed'
```

解决方案（可选，不安装也能正常使用）：

```bash
# 禁用不兼容的DeepSpeed扩展
set DS_BUILD_AIO=0
set DS_BUILD_OPS=0

# 安装deepspeed
pip install deepspeed
```

<img src="./static/images/one.png" alt="deepspeed安装失败" style="max-width:100%; height:auto;">

> 注意：系统CUDA版本与PyTorch编译时的CUDA版本需匹配，可通过`nvidia-smi`查看系统CUDA版本

## 🚀 运行方法 {#how-to-run}

1. 确保已安装所有依赖
2. 检查模型文件是否已放置在 `model/checkpoints` 目录
3. 确认参考音频文件已放置在 `model/checkpoints/voice` 目录
4. 运行应用程序：

```bash
python app.py
```

5. 在浏览器中访问: `http://127.0.0.1:5000`

### 快速启动脚本

为了便于快速启动应用，您可以创建以下bat脚本（`start_tts.bat`）：

```bat
@echo off
echo 正在启动文本转语音系统...
echo.

REM 激活conda环境
call conda activate index-tts

REM 启动应用
python app.py

REM 如果应用意外关闭，暂停显示
pause
```

将此脚本保存在项目根目录下，双击即可快速启动应用。

## 🎬 剪映替换教程 {#jianying-tutorial}

步骤：草稿中先使用任意内置声音朗诵（这样生成的音频位置会固定，便于替换）

<div align="center">
<img src="./static/images/three.png" alt="剪映替换步骤" style="max-width:80%; height:auto;">
</div>



## 🎵 去除伴奏 {#remove-bgm}

推荐使用UVR5软件：[The Ultimate Vocal Remover Application](https://ultimatevocalremover.com/)

> **注意**：UVR5的模型在国外服务器，国内用户可能需要使用VPN下载

国内用户可以使用以下方式获取模型：
- 云兔VPN（价格较便宜且稳定）：[注册链接](https://vip.yuntu.blog/#/register?code=2rb4ZHij)
- 模型百度网盘链接：[下载链接](https://pan.baidu.com/s/1gdEvwbbreDKH8VEHO1SDVA?pwd=6666) 提取码: 6666

安装方法：右击UVR5图标 → 打开文件所在位置 → 将下载的model文件夹粘贴到此处

相关教程：
- [UVR5使用教程(CSDN)](https://blog.csdn.net/2301_79607161/article/details/135057915)
- [UVR5使用教程和最新连招(B站)](https://www.bilibili.com/opus/860174897353064448)

## 💬 交流方式 {#communication}

- QQ交流群：700598581
- 哔哩哔哩：[浅若红尘的个人空间](https://space.bilibili.com/519965290)
- 公众号：浅若红尘

## ❤️ 赞赏支持 {#support}

如果这个项目帮助了你，欢迎：
- ⭐ 给项目点个Star
- 🍴 Fork项目并分享给有需要的朋友
- 提交Issue或PR反馈问题和建议

<div align="center">
<img src="./static/images/nice.png" alt="赞赏码" style="max-width:50%; height:auto;">
</div>

<div align="center">

![Star History](https://api.star-history.com/svg?repos=shiyaaini/index-tts-jianying&type=Date)

</div>
