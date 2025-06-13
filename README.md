# 文本转语音系统

这是一个基于Python Flask+剪映5.9的文本转语音Web应用程序，使用IndexTTS引擎实现语音合成功能。

在此感谢哔哩哔哩：

<div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin: 10px 0; background-color: #f8f9fa;">
  <a href="https://github.com/index-tts/index-tts" target="_blank" style="text-decoration: none; color: #0969da; font-weight: bold;">
    index-tts
  </a>
  <p style="margin: 8px 0 0; color: #666;">IndexTTS 是一种主要基于 XTTS 和 Tortoise 的 GPT 风格的文本转语音 （TTS） 模型。它能够使用拼音纠正汉字的发音，并通过标点符号控制任何位置的停顿。我们增强了系统的多个模块，包括扬声器条件特征表示的改进，以及 BigVGAN2 的集成以优化音频质量。</p>
</div>

- 1.参考音频在：model/checkpoints/voice
- 2.默认生成音频文件在：static/ouput
- 3.使用的剪映版本是5.9，大于5.9的无法使用




## 功能特性

- 选择不同的语音合成模型
- 选择参考音频作为语音风格参考
- 为参考音频添加备注信息
- 生成、预览和下载合成的语音文件
- 剪映的音频替换（1.本人钱包太干净。2.开了用一下就不用实在太浪费。3.剪映的音色选择实在不符合我的心意）
- 剪映的文字样式选择（可以去下载一些好看的ttf文件。好看的字体都收费😂😂😂）

## 系统依赖

这一步按照index-tts一样的安装过程即可

1.安装aconda,这一步看网上教程（就是傻瓜式安装，记得勾上环境变量那一项就行）[Download Now | Anaconda](https://www.anaconda.com/download/success)

```
conda create -n index-tts python=3.10
conda activate index-tts
#后面这些依赖都需要在index-tts环境中安装
conda install -c conda-forge ffmpeg
#安装torch torchaudio需要根据你的CUDA进行安装对应版本，不知道问AI（deepseek）
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
conda install -c conda-forge pynini==2.1.6
pip install WeTextProcessing --no-deps

```

然后我们需要安装index-tts依赖（这个是从index-tts直接下载下来的，使用终端进入该文件夹，且在index-tts的conda环境中运行命令）

<img src="./static/images/two.png" alt="" style="max-width:100%; height:auto;">

```
pip install -e .
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```



# 安装依赖提醒

### 问题1：

​	安装CUDA特别慢的问题，我们需要提前安装visual studio，否则会一直卡到这一步

​	[[Visual Studio 2022 IDE - 适用于软件开发人员的编程工具](https://visualstudio.microsoft.com/zh-hans/vs/)](https://visualstudio.microsoft.com/zh-hans/vs/)



### 问题2（这个不安装也是可以正常用的）：

```
>> DeepSpeed加载失败，回退到标准推理: No module named 'deepspeed'

```

出现上方情况，说明deepseed依赖没有装

```
pip install deepseed
```

<img src=".\static\images\one.png" alt="deepspeed安装失败" style="max-width:100%; height:auto;">

然后发现报错

解决方法：

```
# 禁用不兼容的DeepSpeed扩展
```

```
set DS_BUILD_AIO=0

set DS_BUILD_OPS=0
```

- 系统CUDA版本（12.9）与PyTorch编译时使用的CUDA版本（12.1）不一致（在终端输入`nvidia-smi`查看版本）

- DeepSpeed需要CUDA版本完全匹配才能编译扩展

  ```
  pip install deepspeed
  ```

  

## 如何运行

1. 确保系统中已安装Python和所需依赖

2. 确保模型文件已放置在 `model/checkpoints` 目录下

3. 确保参考音频文件已放置在 `model/checkpoints/voice` 目录下

4. 运行应用程序：

   ```
   python app.py
   ```

5. 在浏览器中访问: `http://127.0.0.1:5000`

6. 剪映如何替换音频(草稿随便使用一个声音来朗诵，这样生成的音频位置会记住，可以减少代码及混乱，替换后会自动计算音频时长)

   <img src=".\static\images\three.png" alt="" style="max-width:100%; height:auto;">

   效果(我还没有下载模型)：

   <img src=".\static\images\four.png" alt="" style="max-width:100%; height:auto;">

# 交流：

QQ交流群：700598581

哔哩哔哩：[浅若红尘的个人空间-浅若红尘个人主页-哔哩哔哩视频](https://space.bilibili.com/519965290?spm_id_from=333.1007.0.0)



# 赞赏：

* **底部温和呼吁 (最推荐)：**

  *   `如果这个项目帮助了你，一个 ⭐️ Star 是对我们最大的鼓励！`
  *   `觉得这个项目有用？点个 Star ⭐️ 让它被更多人发现吧！`
  *   `喜欢这个项目？欢迎 Star ⭐️、Fork 🍴 或分享给有需要的朋友！你的认可是我们持续改进的动力。`
  *   `项目的发展离不开社区的反馈和支持。如果你在使用中有任何建议，或者想表达支持，欢迎点个 Star ⭐️ 或 [提交 Issue/PR](链接)。`

  

<img src=".\static\images\nice.png" alt="赞赏" style="max-width:100%; height:auto;">



![Star History](https://api.star-history.com/svg?repos=shiyaaini/index-tts-jianying&type=Date)
