#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
生成静音文件的工具脚本
"""

import os
import wave
import struct

def generate_silence_wav(output_path, duration=0.1, sample_rate=44100, channels=1):
    """使用Python内置模块生成静音WAV文件"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 计算样本数
        num_samples = int(sample_rate * duration)
        
        # 生成静音数据（全零）
        audio_data = b'\x00\x00' * num_samples * channels
        
        # 写入WAV文件
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(channels)  # 声道数
            wav_file.setsampwidth(2)  # 16位
            wav_file.setframerate(sample_rate)  # 采样率
            wav_file.writeframes(audio_data)
        
        print(f"静音文件生成成功: {output_path}")
        print(f"时长: {duration}秒")
        print(f"采样率: {sample_rate}Hz")
        print(f"声道数: {channels}")
        print(f"文件大小: {os.path.getsize(output_path)} 字节")
        
        return True
        
    except Exception as e:
        print(f"生成静音文件失败: {e}")
        return False

def main():
    """主函数"""
    print("静音文件生成工具")
    print("=" * 30)
    
    # 确保static目录存在
    static_dir = "static"
    os.makedirs(static_dir, exist_ok=True)
    
    # 生成0.1秒的静音文件
    silence_file = os.path.join(static_dir, "silence_0.1s.wav")
    
    if os.path.exists(silence_file):
        print(f"静音文件已存在: {silence_file}")
        response = input("是否重新生成? (y/N): ")
        if response.lower() != 'y':
            print("跳过生成")
            return
    
    print("正在生成静音文件...")
    success = generate_silence_wav(silence_file, duration=0.1)
    
    if success:
        print("静音文件生成完成！")
        print(f"文件路径: {os.path.abspath(silence_file)}")
    else:
        print("静音文件生成失败！")

if __name__ == "__main__":
    main() 