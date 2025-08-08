# 剪映工程文件编辑器

> 基于PyQt5和IndexTTS的多功能剪映工程文件编辑器，集成文本转语音、多人语音合成、插帧算法等功能。

## ✨ 主要功能

- **📁 项目管理** - 剪映工程文件的创建、导入和管理
- **✏️ 文字编辑** - 可视化编辑剪映工程中的文本内容
- **🎤 文本转语音** - 基于IndexTTS的高质量语音合成
- **👥 多人语音合成** - 支持多角色语音配置和字幕导出
- **🎬 插帧算法补偿** - 视频帧率优化处理
- **🎵 视频提取音频** - 从视频文件中提取音频轨道

## 📦 下载链接（整合包）

- **百度网盘**: [点击下载](https://pan.baidu.com/s/11mEIKEfWxmEW0r7nxbag0g?pwd=6666) (提取码: 6666)
- **夸克网盘**: [点击下载](https://pan.quark.cn/s/09cfe9f495e8)

## 🚀 快速开始

1. **下载并解压**
   ```bash
   # 下载完成后解压到本地目录
   cd jianying_pyqt5
   ```

2. **运行程序**
   ```bash
   python main.py
   ```

## 📋 系统要求

- **操作系统**: Windows 10/11
- **Python版本**: 3.10+
- **显卡**: 支持CUDA的NVIDIA显卡（推荐）
- **内存**: 8GB以上

## 🛠️ 技术架构

- **界面框架**: PyQt5 + QFluentWidgets
- **语音合成**: IndexTTS
- **视频处理**: FFmpeg
- **深度学习**: PyTorch + CUDA

## ❓ 常见问题

### CUDA安装缓慢
**问题**: 安装CUDA特别慢  
**解决方案**: 提前安装Visual Studio  
**下载地址**: [Visual Studio官网](https://visualstudio.microsoft.com/zh-hans/vs/)

### DeepSpeed加载失败
**问题**: 
```
>> DeepSpeed加载失败，回退到标准推理: No module named 'deepspeed'
```

**解决方案**（可选，不安装也能正常使用）：
```bash
# 禁用不兼容的DeepSpeed扩展
set DS_BUILD_AIO=0
set DS_BUILD_OPS=0

# 安装deepspeed
pip install deepspeed
```

> 💡 **注意**: 系统CUDA版本与PyTorch编译时的CUDA版本需匹配，可通过`nvidia-smi`查看系统CUDA版本

## 💬 交流支持

- **QQ交流群**: 700598581
- **哔哩哔哩**: [浅若红尘的个人空间](https://space.bilibili.com/519965290)

## ❤️ 支持项目

如果这个项目帮助了您，欢迎：
- ⭐ 给项目点个Star
- 🍴 Fork项目并分享给有需要的朋友
- 📝 提交Issue或PR反馈问题和建议

<div align="center">
<img src="./static/nice.png" alt="赞赏码" style="max-width:50%; height:auto;">
</div>

<div align="center">

![Star History](https://api.star-history.com/svg?repos=shiyaaini/index-tts-jianying&type=Date)

</div>
