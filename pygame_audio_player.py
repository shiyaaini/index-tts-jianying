#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于 pygame 的音频播放器
支持单个音频播放和批量顺序播放
"""

import os
import time
import threading
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox

try:
    import pygame
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("警告: pygame 未安装，音频播放功能将受限。请运行: pip install pygame")

class PygameAudioPlayer(QObject):
    """基于 pygame 的音频播放器"""
    
    # 信号定义
    playback_started = pyqtSignal(str)  # 播放开始信号，传递文件路径
    playback_finished = pyqtSignal(str)  # 播放完成信号，传递文件路径
    playback_error = pyqtSignal(str, str)  # 播放错误信号，传递文件路径和错误信息
    batch_playback_finished = pyqtSignal()  # 批量播放完成信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_playing = False
        self.current_file = None
        self.batch_playlist = []
        self.current_batch_index = 0
        self.is_batch_playing = False
        self.playback_thread = None
        
        # 创建定时器用于检查播放状态
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_playback_status)
        
    def is_pygame_available(self):
        """检查 pygame 是否可用"""
        return PYGAME_AVAILABLE
        
    def play_audio(self, audio_path):
        """播放单个音频文件"""
        if not PYGAME_AVAILABLE:
            self.playback_error.emit(audio_path, "pygame 未安装，无法播放音频")
            return False
            
        if not os.path.exists(audio_path):
            self.playback_error.emit(audio_path, "音频文件不存在")
            return False
            
        try:
            # 停止当前播放
            self.stop_audio()
            
            # 直接播放原文件，不再创建临时文件
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            self.is_playing = True
            self.current_file = audio_path
            
            # 开始检查播放状态
            self.check_timer.start(100)  # 每100ms检查一次
            
            self.playback_started.emit(audio_path)
            return True
            
        except Exception as e:
            error_msg = f"播放音频失败: {str(e)}"
            self.playback_error.emit(audio_path, error_msg)
            return False
            
    def stop_audio(self):
        """停止音频播放"""
        if PYGAME_AVAILABLE and self.is_playing:
            try:
                pygame.mixer.music.stop()
                self.check_timer.stop()
                
                if self.current_file:
                    self.playback_finished.emit(self.current_file)
                    
                self.is_playing = False
                current_file = self.current_file
                self.current_file = None
                
                # 播放静音文件来释放播放器
                self.play_silence_to_release()
                    
            except Exception as e:
                print(f"停止音频播放失败: {e}")
                
    def force_release_player(self):
        """强制释放播放器（用于TTS转换前）"""
        try:
            if PYGAME_AVAILABLE:
                # 停止当前播放
                pygame.mixer.music.stop()
                self.check_timer.stop()
                
                # 播放静音文件来释放播放器
                self.play_silence_to_release()
                
                # 重置状态
                self.is_playing = False
                self.current_file = None
                
                print("已强制释放pygame播放器")
                return True
        except Exception as e:
            print(f"强制释放播放器失败: {e}")
            return False
                
    def pause_audio(self):
        """暂停音频播放"""
        if PYGAME_AVAILABLE and self.is_playing:
            try:
                pygame.mixer.music.pause()
            except Exception as e:
                print(f"暂停音频播放失败: {e}")
                
    def resume_audio(self):
        """恢复音频播放"""
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.unpause()
            except Exception as e:
                print(f"恢复音频播放失败: {e}")
                
    def check_playback_status(self):
        """检查播放状态"""
        if not PYGAME_AVAILABLE:
            return
            
        try:
            # 检查音频是否还在播放
            if not pygame.mixer.music.get_busy():
                # 音频播放完成
                self.check_timer.stop()
                
                if self.current_file:
                    finished_file = self.current_file
                    self.current_file = None
                    self.is_playing = False
                    self.playback_finished.emit(finished_file)
                    
                    # 如果是批量播放，继续播放下一个
                    if self.is_batch_playing:
                        self.play_next_in_batch()
                        
        except Exception as e:
            print(f"检查播放状态失败: {e}")
            
    def play_audio_list(self, audio_paths, delay_between_files=1.0):
        """批量播放音频文件列表"""
        if not PYGAME_AVAILABLE:
            self.playback_error.emit("", "pygame 未安装，无法播放音频")
            return False
            
        if not audio_paths:
            return False
            
        # 过滤存在的音频文件
        valid_paths = [path for path in audio_paths if os.path.exists(path)]
        
        if not valid_paths:
            self.playback_error.emit("", "没有找到有效的音频文件")
            return False
            
        # 设置批量播放参数
        self.batch_playlist = valid_paths
        self.current_batch_index = 0
        self.is_batch_playing = True
        self.delay_between_files = delay_between_files
        
        # 开始播放第一个文件
        self.play_next_in_batch()
        return True
        
    def play_next_in_batch(self):
        """播放批量列表中的下一个音频"""
        if not self.is_batch_playing or self.current_batch_index >= len(self.batch_playlist):
            # 批量播放完成
            self.is_batch_playing = False
            self.batch_playlist = []
            self.current_batch_index = 0
            self.batch_playback_finished.emit()
            return
            
        # 获取下一个要播放的文件
        next_file = self.batch_playlist[self.current_batch_index]
        self.current_batch_index += 1
        
        # 如果需要延迟，则使用定时器
        if hasattr(self, 'delay_between_files') and self.delay_between_files > 0 and self.current_batch_index > 1:
            QTimer.singleShot(int(self.delay_between_files * 1000), lambda: self.play_audio(next_file))
        else:
            self.play_audio(next_file)
            
    def stop_batch_playback(self):
        """停止批量播放"""
        self.is_batch_playing = False
        self.batch_playlist = []
        self.current_batch_index = 0
        self.stop_audio()
        
    def get_playback_info(self):
        """获取当前播放信息"""
        return {
            'is_playing': self.is_playing,
            'current_file': self.current_file,
            'is_batch_playing': self.is_batch_playing,
            'batch_progress': f"{self.current_batch_index}/{len(self.batch_playlist)}" if self.is_batch_playing else None
        }
        
    def get_supported_formats(self):
        """获取支持的音频格式"""
        return ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac']
        
    def is_supported_format(self, file_path):
        """检查文件格式是否支持"""
        if not file_path:
            return False
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.get_supported_formats()

    def play_silence_to_release(self):
        """播放静音文件来释放播放器"""
        try:
            # 确保static目录存在
            static_dir = "static"
            os.makedirs(static_dir, exist_ok=True)
            
            # 静音文件路径
            silence_file = os.path.join(static_dir, "silence_0.1s.wav")
            
            # 如果静音文件不存在，使用ffmpeg生成
            if not os.path.exists(silence_file):
                self.generate_silence_file(silence_file)
            
            if os.path.exists(silence_file):
                # 播放静音文件
                pygame.mixer.music.load(silence_file)
                pygame.mixer.music.play()
                
                # 等待播放完成
                import time
                time.sleep(0.15)  # 稍微多等一点确保播放完成
                
                # 停止播放
                pygame.mixer.music.stop()
                
                print("已播放静音文件释放播放器")
                return True
            else:
                print("静音文件生成失败")
                return False
                
        except Exception as e:
            print(f"播放静音文件失败: {e}")
            return False
    
    def generate_silence_file(self, output_path):
        """使用ffmpeg生成静音文件，如果ffmpeg不可用则使用Python内置模块"""
        try:
            import subprocess
            
            # 查找ffmpeg路径
            ffmpeg_path = self.get_ffmpeg_path()
            if ffmpeg_path:
                # 使用ffmpeg生成
                cmd = [
                    ffmpeg_path, '-f', 'lavfi', '-i', 
                    'anullsrc=channel_layout=mono:sample_rate=44100',
                    '-t', '0.1', '-y', output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"静音文件已生成: {output_path}")
                    return True
                else:
                    print(f"ffmpeg生成静音文件失败: {result.stderr}")
            else:
                print("未找到ffmpeg，尝试使用Python内置模块生成")
            
            # 备用方案：使用Python内置模块生成
            return self.generate_silence_with_python(output_path)
                
        except Exception as e:
            print(f"生成静音文件时出错: {e}")
            # 备用方案：使用Python内置模块生成
            return self.generate_silence_with_python(output_path)
    
    def generate_silence_with_python(self, output_path):
        """使用Python内置模块生成静音文件"""
        try:
            import wave
            
            # 确保目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 参数设置
            duration = 0.1  # 0.1秒
            sample_rate = 44100
            channels = 1
            
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
            
            print(f"静音文件已生成（Python内置模块）: {output_path}")
            return True
            
        except Exception as e:
            print(f"Python内置模块生成静音文件失败: {e}")
            return False
    
    def get_ffmpeg_path(self):
        """获取ffmpeg路径"""
        # 首先检查本地ffmpeg目录
        local_ffmpeg = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")
        if os.path.exists(local_ffmpeg):
            return local_ffmpeg
            
        # 检查系统PATH中的ffmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
            if result.returncode == 0:
                return 'ffmpeg'
        except:
            pass
            
        return None

# 全局音频播放器实例
_global_audio_player = None

def get_audio_player():
    """获取全局音频播放器实例"""
    global _global_audio_player
    if _global_audio_player is None:
        _global_audio_player = PygameAudioPlayer()
    return _global_audio_player

def play_audio_file(audio_path):
    """播放单个音频文件的便捷函数"""
    player = get_audio_player()
    return player.play_audio(audio_path)

def play_audio_files(audio_paths, delay=1.0):
    """播放多个音频文件的便捷函数"""
    player = get_audio_player()
    return player.play_audio_list(audio_paths, delay)

def stop_audio():
    """停止音频播放的便捷函数"""
    player = get_audio_player()
    player.stop_audio()

if __name__ == "__main__":
    # 测试代码
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QCoreApplication
    
    app = QCoreApplication(sys.argv)
    
    player = PygameAudioPlayer()
    
    # 连接信号
    player.playback_started.connect(lambda path: print(f"开始播放: {os.path.basename(path)}"))
    player.playback_finished.connect(lambda path: print(f"播放完成: {os.path.basename(path)}"))
    player.playback_error.connect(lambda path, error: print(f"播放错误 {os.path.basename(path)}: {error}"))
    player.batch_playback_finished.connect(lambda: print("批量播放完成"))
    
    # 测试播放（需要有实际的音频文件）
    test_files = ["test1.wav", "test2.wav"]  # 替换为实际存在的音频文件
    existing_files = [f for f in test_files if os.path.exists(f)]
    
    if existing_files:
        print(f"测试播放 {len(existing_files)} 个音频文件...")
        player.play_audio_list(existing_files, delay=0.5)
    else:
        print("没有找到测试音频文件")
        
    # 运行5秒后退出
    QTimer.singleShot(5000, app.quit)
    sys.exit(app.exec_())