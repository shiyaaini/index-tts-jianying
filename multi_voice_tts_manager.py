import json
import os
import uuid
import time
import threading
import subprocess
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QCheckBox,
                             QInputDialog, QAbstractItemView, QComboBox, 
                             QSpinBox, QDoubleSpinBox, QLineEdit, QDialog, 
                             QListWidget, QListWidgetItem, QLabel, QScrollArea, 
                             QFrame, QFileDialog, QProgressBar, QTextEdit, 
                             QGroupBox, QFormLayout, QPushButton, QTreeWidget,
                             QTreeWidgetItem, QSplitter, QMessageBox, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QUrl, QTimer
from PyQt5.QtGui import QColor, QFont, QDragEnterEvent, QDropEvent
from qfluentwidgets import (CardWidget, StrongBodyLabel, BodyLabel,
                           PushButton, MessageBox, InfoBar, InfoBarPosition,
                           FluentIcon, ComboBox as FluentComboBox)

# 导入智能添加文本对话框
from text_editor import SmartTextAddDialog, MultiLineTextEditDialog

# 导入TTS相关组件
from tts_manager import (MultiLineTextEdit, ParameterSpinBox, ParameterIntSpinBox, 
                        ParameterCheckBox, AudioPreviewWidget, AudioTreeDialog, 
                        BatchParameterDialog)

try:
    from pygame_audio_player import get_audio_player
    PYGAME_PLAYER_AVAILABLE = True
except ImportError:
    PYGAME_PLAYER_AVAILABLE = False

class MultiVoiceTTSWorker(QThread):
    """多人语音合成TTS转换工作线程"""
    progress_updated = pyqtSignal(int, str)  # 进度, 状态信息
    conversion_finished = pyqtSignal(str, str, bool, float)  # text_id, output_path, success, duration
    error_occurred = pyqtSignal(str, str)  # text_id, error_message
    
    def __init__(self, text_items, project_name=""):
        super().__init__()
        self.text_items = text_items
        self.project_name = project_name
        self.is_cancelled = False
        
    def run(self):
        """执行TTS转换"""
        try:
            # 在开始转换前，强制释放pygame播放器以避免文件占用
            try:
                # 尝试导入pygame音频播放器
                try:
                    from pygame_audio_player import get_audio_player
                    player = get_audio_player()
                    player.force_release_player()
                    print("已强制释放pygame音频播放器以避免文件占用")
                except ImportError:
                    print("pygame音频播放器模块未找到")
            except Exception as e:
                print(f"释放音频播放器失败: {e}")
            
            # 导入TTS模块
            try:
                import sys
                import os
                # 添加index-tts-main目录到Python路径
                index_tts_path = os.path.join(os.getcwd(), "index-tts-main")
                if index_tts_path not in sys.path:
                    sys.path.insert(0, index_tts_path)
                
                from indextts.infer import IndexTTS
            except ImportError as e:
                self.progress_updated.emit(0, f"TTS模块导入失败: {str(e)}\n请确保已安装必要的依赖库，如torchaudio等")
                # 发出所有文本转换失败的信号
                for item in self.text_items:
                    self.error_occurred.emit(item['text_id'], f"TTS模块导入失败: {str(e)}")
                    self.conversion_finished.emit(item['text_id'], "", False, 0.0)
                return
            except Exception as e:
                self.progress_updated.emit(0, f"TTS模块初始化失败: {str(e)}")
                # 发出所有文本转换失败的信号
                for item in self.text_items:
                    self.error_occurred.emit(item['text_id'], f"TTS模块初始化失败: {str(e)}")
                    self.conversion_finished.emit(item['text_id'], "", False, 0.0)
                return
            
            # 初始化TTS模型
            self.progress_updated.emit(0, "正在初始化TTS模型...")
            try:
                tts = IndexTTS(
                    model_dir="checkpoints",
                    cfg_path="checkpoints/config.yaml"
                )
            except Exception as e:
                self.progress_updated.emit(0, f"TTS模型初始化失败: {str(e)}")
                # 发出所有文本转换失败的信号
                for item in self.text_items:
                    self.error_occurred.emit(item['text_id'], f"TTS模型初始化失败: {str(e)}")
                    self.conversion_finished.emit(item['text_id'], "", False)
                return
            
            total_items = len(self.text_items)
            
            # 创建项目输出目录
            if self.project_name:
                safe_project_name = self.generate_safe_project_name(self.project_name)
                project_output_dir = os.path.join("output", safe_project_name)
            else:
                project_output_dir = "output"
            
            os.makedirs(project_output_dir, exist_ok=True)
            
            for i, item in enumerate(self.text_items):
                if self.is_cancelled:
                    break
                    
                text_id = item['text_id']
                text_content = item['text_content']
                reference_voice = item['reference_voice']
                
                # 更新进度
                progress = int((i / total_items) * 100)
                self.progress_updated.emit(progress, f"正在转换: {text_content[:20]}...")
                
                try:
                    # 检查参考音频
                    if not reference_voice or not os.path.exists(reference_voice):
                        raise Exception("参考音频文件不存在")
                    
                    # 生成输出路径 - 保存到项目目录
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_text = self.generate_safe_filename(text_content)
                    audio_filename = f"{timestamp}_{safe_text}_{text_id[:8]}.wav"
                    output_path = os.path.join(project_output_dir, audio_filename)
                    
                    # 确保文件名唯一
                    counter = 0
                    while os.path.exists(output_path):
                        counter += 1
                        audio_filename = f"{timestamp}_{safe_text}_{text_id[:8]}_{counter:03d}.wav"
                        output_path = os.path.join(project_output_dir, audio_filename)
                    
                    # 获取TTS参数配置
                    tts_params = item.get('tts_params', {})
                    infer_mode = item.get('infer_mode', '普通推理')
                    
                    # 设置完整的TTS参数（使用表格中的用户配置）
                    kwargs = {
                        "do_sample": bool(tts_params.get('do_sample', True)),
                        "top_p": float(tts_params.get('top_p', 0.8)),
                        "top_k": int(tts_params.get('top_k', 30)) if int(tts_params.get('top_k', 30)) > 0 else None,
                        "temperature": float(tts_params.get('temperature', 1.0)),
                        "length_penalty": float(tts_params.get('length_penalty', 1.0)),
                        "num_beams": int(tts_params.get('num_beams', 3)),
                        "repetition_penalty": float(tts_params.get('repetition_penalty', 10.0)),
                        "max_mel_tokens": int(tts_params.get('max_mel_tokens', 2048)),
                    }
                    
                    # 获取分句参数
                    max_text_tokens = int(tts_params.get('max_text_tokens_per_sentence', 120))
                    sentences_bucket_size = int(tts_params.get('sentences_bucket_max_size', 4))
                    
                    # 执行TTS转换 - 使用用户配置的参数
                    if infer_mode == "普通推理":
                        tts.infer(
                            reference_voice, 
                            text_content, 
                            output_path, 
                            verbose=True,
                            max_text_tokens_per_sentence=max_text_tokens,
                            **kwargs
                        )
                    else:
                        # 批次推理
                        tts.infer_fast(
                            reference_voice, 
                            text_content, 
                            output_path, 
                            verbose=True,
                            max_text_tokens_per_sentence=max_text_tokens,
                            sentences_bucket_max_size=sentences_bucket_size,
                            **kwargs
                        )
                    
                    # 获取音频时长
                    audio_duration = self.get_audio_duration(output_path)
                    
                    # 转换成功
                    self.conversion_finished.emit(text_id, output_path, True, audio_duration)
                    
                except Exception as e:
                    # 转换失败
                    error_msg = f"转换失败: {str(e)}"
                    self.error_occurred.emit(text_id, error_msg)
                    self.conversion_finished.emit(text_id, "", False, 0.0)
            
            # 完成
            if not self.is_cancelled:
                self.progress_updated.emit(100, "转换完成!")
                
        except Exception as e:
            self.progress_updated.emit(0, f"初始化失败: {str(e)}")
    
    def get_audio_duration(self, audio_path):
        """获取音频时长（秒）"""
        try:
            # 尝试使用wave库获取时长
            if audio_path.lower().endswith('.wav'):
                import wave
                with wave.open(audio_path, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    return frames / float(sample_rate)
        except:
            pass
            
        try:
            # 尝试使用ffprobe获取时长
            ffprobe_path = self.get_ffprobe_path()
            if ffprobe_path:
                cmd = [
                    ffprobe_path, '-v', 'quiet', '-show_entries', 
                    'format=duration', '-of', 'csv=p=0', audio_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    return float(result.stdout.strip())
        except:
            pass
            
        # 默认估算：根据文件大小粗略估算
        try:
            file_size = os.path.getsize(audio_path)
            # 假设44.1kHz, 16bit, mono的WAV文件
            estimated_duration = file_size / (44100 * 2)
            return max(estimated_duration, 1.0)
        except:
            return 3.0  # 默认3秒
    
    def get_ffprobe_path(self):
        """获取ffprobe路径"""
        # 首先检查本地ffmpeg目录
        local_ffprobe = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffprobe.exe")
        if os.path.exists(local_ffprobe):
            return local_ffprobe
            
        # 检查系统PATH中的ffprobe
        try:
            result = subprocess.run(['ffprobe', '-version'], capture_output=True)
            if result.returncode == 0:
                return 'ffprobe'
        except:
            pass
            
        return None
            
    def generate_safe_filename(self, text, max_length=20):
        """生成安全的文件名"""
        import re
        # 移除所有不安全的字符
        safe_text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', text)
        # 替换换行符和制表符
        safe_text = safe_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # 合并多个空格为单个下划线
        safe_text = re.sub(r'\s+', '_', safe_text.strip())
        # 移除开头和结尾的点号（Windows不允许）
        safe_text = safe_text.strip('.')
        
        # 限制长度
        if len(safe_text) > max_length:
            safe_text = safe_text[:max_length].rstrip('_')
            
        # 如果处理后为空，使用默认名称
        if not safe_text:
            safe_text = f"text_{int(time.time())}"
            
        return safe_text
    
    def generate_safe_project_name(self, project_name):
        """生成安全的项目目录名"""
        import re
        # 移除所有不安全的字符
        safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', project_name)
        # 替换空格为下划线
        safe_name = re.sub(r'\s+', '_', safe_name.strip())
        # 移除开头和结尾的点号
        safe_name = safe_name.strip('.')
        
        # 如果处理后为空，使用默认名称
        if not safe_name:
            safe_name = "unnamed_project"
            
        return safe_name
        
    def cancel(self):
        """取消转换"""
        self.is_cancelled = True

class MultiVoiceProject:
    """多人语音合成项目类"""
    def __init__(self):
        self.project_name = ""
        self.created_time = datetime.now()
        self.modified_time = datetime.now()
        self.text_segments = []  # 文本段落列表
        self.voice_configs = {}  # 语音配置
        self.output_settings = {
            'format': 'wav',
            'sample_rate': 44100,
            'channels': 1,
            'gap_duration': 0.03,  # 段落间隔时间（秒）- 30ms，避免顿挫感
            'add_silence_gap': True  # 是否添加静音间隔
        }
        
    def to_dict(self):
        """转换为字典格式用于保存"""
        return {
            'project_name': self.project_name,
            'created_time': self.created_time.isoformat(),
            'modified_time': self.modified_time.isoformat(),
            'text_segments': self.text_segments,
            'voice_configs': self.voice_configs,
            'output_settings': self.output_settings
        }
        
    @classmethod
    def from_dict(cls, data):
        """从字典格式加载项目"""
        project = cls()
        project.project_name = data.get('project_name', '')
        project.created_time = datetime.fromisoformat(data.get('created_time', datetime.now().isoformat()))
        project.modified_time = datetime.fromisoformat(data.get('modified_time', datetime.now().isoformat()))
        project.text_segments = data.get('text_segments', [])
        project.voice_configs = data.get('voice_configs', {})
        project.output_settings = data.get('output_settings', {
            'format': 'wav',
            'sample_rate': 44100,
            'channels': 1,
            'gap_duration': 0.03,
            'add_silence_gap': True
        })
        return project

class AudioMergeWorker(QThread):
    """音频合成工作线程"""
    progress_updated = pyqtSignal(int, str)
    merge_finished = pyqtSignal(str, bool)  # output_path, success
    error_occurred = pyqtSignal(str)
    
    def __init__(self, audio_files, output_path, gap_duration=0.03, add_silence_gap=True):
        super().__init__()
        self.audio_files = audio_files
        self.output_path = output_path
        self.gap_duration = gap_duration
        self.add_silence_gap = add_silence_gap
        self.is_cancelled = False
        
    def run(self):
        """执行音频合成"""
        try:
            self.progress_updated.emit(0, "准备合成音频...")
            
            # 检查ffmpeg是否可用
            ffmpeg_path = self.get_ffmpeg_path()
            if not ffmpeg_path:
                raise Exception("未找到ffmpeg，请确保ffmpeg已安装或放置在ffmpeg/bin目录下")
            
            # 创建临时文件列表
            temp_dir = os.path.join(os.path.dirname(self.output_path), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 生成ffmpeg合并命令
            self.progress_updated.emit(20, "生成合并命令...")
            
            # 创建输入文件列表
            input_list_file = os.path.join(temp_dir, "input_list.txt")
            with open(input_list_file, 'w', encoding='utf-8') as f:
                for i, audio_file in enumerate(self.audio_files):
                    if self.is_cancelled:
                        return
                    
                    # 写入音频文件
                    f.write(f"file '{os.path.abspath(audio_file)}'\n")
                    
                    # 如果不是最后一个文件，添加静音间隔
                    if i < len(self.audio_files) - 1 and self.gap_duration > 0 and self.add_silence_gap:
                        # 生成静音文件 - 严格使用30ms间隔
                        silence_file = os.path.join(temp_dir, f"silence_{i}.wav")
                        silence_cmd = [
                            ffmpeg_path, '-f', 'lavfi', '-i', 
                            f'anullsrc=channel_layout=mono:sample_rate=44100',
                            '-t', '0.03', '-y', silence_file  # 强制使用30ms
                        ]
                        subprocess.run(silence_cmd, check=True, capture_output=True)
                        f.write(f"file '{os.path.abspath(silence_file)}'\n")
            
            self.progress_updated.emit(50, "正在合成音频...")
            
            # 执行ffmpeg合并命令
            merge_cmd = [
                ffmpeg_path, '-f', 'concat', '-safe', '0', 
                '-i', input_list_file, '-c', 'copy', '-y', self.output_path
            ]
            
            result = subprocess.run(merge_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"ffmpeg合并失败: {result.stderr}")
            
            self.progress_updated.emit(90, "清理临时文件...")
            
            # 清理临时文件
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass
            
            self.progress_updated.emit(100, "合成完成!")
            self.merge_finished.emit(self.output_path, True)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            self.merge_finished.emit("", False)
            
    def get_ffmpeg_path(self):
        """获取ffmpeg路径"""
        # 首先检查本地ffmpeg目录
        local_ffmpeg = os.path.join(os.getcwd(),"ffmpeg", "bin", "ffmpeg.exe")
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
        
    def cancel(self):
        """取消合成"""
        self.is_cancelled = True

class SubtitleExporter:
    """字幕导出器"""
    
    @staticmethod
    def export_srt(text_segments, audio_durations, output_path, gap_duration=0.03):
        """导出SRT字幕"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                current_time = 0
                
                for i, (segment, duration) in enumerate(zip(text_segments, audio_durations)):
                    start_time = current_time
                    end_time = current_time + duration
                    
                    # 格式化时间
                    start_str = SubtitleExporter.format_srt_time(start_time)
                    end_str = SubtitleExporter.format_srt_time(end_time)
                    
                    # 写入字幕条目
                    f.write(f"{i + 1}\n")
                    f.write(f"{start_str} --> {end_str}\n")
                    f.write(f"{segment['text']}\n\n")
                    
                    current_time = end_time + gap_duration  # 使用项目设置的间隔时间
                    
            return True
        except Exception as e:
            print(f"导出SRT失败: {e}")
            return False
    
    @staticmethod
    def export_srt_for_merged_audio(text_segments, audio_files, output_path, gap_duration=0.03):
        """为合成音频导出SRT字幕"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                current_time = 0
                
                for i, (segment, audio_file) in enumerate(zip(text_segments, audio_files)):
                    # 获取实际音频时长
                    if os.path.exists(audio_file):
                        # 使用ffprobe获取准确时长
                        duration = SubtitleExporter.get_audio_duration_accurate(audio_file)
                    else:
                        # 使用估算时长
                        duration = segment.get('actual_duration', len(segment['text']) * 300 / 1000.0)
                    
                    start_time = current_time
                    end_time = current_time + duration
                    
                    # 格式化时间
                    start_str = SubtitleExporter.format_srt_time(start_time)
                    end_str = SubtitleExporter.format_srt_time(end_time)
                    
                    # 写入字幕条目
                    f.write(f"{i + 1}\n")
                    f.write(f"{start_str} --> {end_str}\n")
                    f.write(f"{segment['text']}\n\n")
                    
                    # 更新时间轴，考虑间隔
                    current_time = end_time + gap_duration
                    
            return True
        except Exception as e:
            print(f"导出SRT失败: {e}")
            return False
    
    @staticmethod
    def export_ass(text_segments, audio_durations, output_path, gap_duration=0.03):
        """导出ASS字幕"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # ASS文件头
                f.write("[Script Info]\n")
                f.write("Title: Multi-Voice TTS Subtitle\n")
                f.write("ScriptType: v4.00+\n\n")
                
                f.write("[V4+ Styles]\n")
                f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                f.write("Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n\n")
                
                f.write("[Events]\n")
                f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                
                current_time = 0
                
                for segment, duration in zip(text_segments, audio_durations):
                    start_time = current_time
                    end_time = current_time + duration
                    
                    # 格式化时间
                    start_str = SubtitleExporter.format_ass_time(start_time)
                    end_str = SubtitleExporter.format_ass_time(end_time)
                    
                    # 写入字幕条目
                    f.write(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{segment['text']}\n")
                    
                    current_time = end_time + gap_duration  # 使用项目设置的间隔时间
                    
            return True
        except Exception as e:
            print(f"导出ASS失败: {e}")
            return False
    
    @staticmethod
    def export_ass_for_merged_audio(text_segments, audio_files, output_path, gap_duration=0.03):
        """为合成音频导出ASS字幕"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # ASS文件头
                f.write("[Script Info]\n")
                f.write("Title: Multi-Voice TTS Subtitle\n")
                f.write("ScriptType: v4.00+\n\n")
                
                f.write("[V4+ Styles]\n")
                f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                f.write("Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n\n")
                
                f.write("[Events]\n")
                f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                
                current_time = 0
                
                for segment, audio_file in zip(text_segments, audio_files):
                    # 获取实际音频时长
                    if os.path.exists(audio_file):
                        duration = SubtitleExporter.get_audio_duration_accurate(audio_file)
                    else:
                        duration = segment.get('actual_duration', len(segment['text']) * 300 / 1000.0)
                    
                    start_time = current_time
                    end_time = current_time + duration
                    
                    # 格式化时间
                    start_str = SubtitleExporter.format_ass_time(start_time)
                    end_str = SubtitleExporter.format_ass_time(end_time)
                    
                    # 写入字幕条目
                    f.write(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{segment['text']}\n")
                    
                    current_time = end_time + gap_duration
                    
            return True
        except Exception as e:
            print(f"导出ASS失败: {e}")
            return False
    
    @staticmethod
    def export_lrc(text_segments, audio_durations, output_path, gap_duration=0.03):
        """导出LRC字幕"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # LRC文件头
                f.write("[ti:Multi-Voice TTS]\n")
                f.write("[ar:TTS Generator]\n")
                f.write("[al:Generated]\n")
                f.write("[by:Multi-Voice TTS Manager]\n\n")
                
                current_time = 0
                
                for segment, duration in zip(text_segments, audio_durations):
                    # 格式化时间
                    time_str = SubtitleExporter.format_lrc_time(current_time)
                    
                    # 写入字幕条目
                    f.write(f"[{time_str}]{segment['text']}\n")
                    
                    current_time += duration + gap_duration  # 使用项目设置的间隔时间
                    
            return True
        except Exception as e:
            print(f"导出LRC失败: {e}")
            return False
    
    @staticmethod
    def export_lrc_for_merged_audio(text_segments, audio_files, output_path, gap_duration=0.03):
        """为合成音频导出LRC字幕"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # LRC文件头
                f.write("[ti:Multi-Voice TTS]\n")
                f.write("[ar:TTS Generator]\n")
                f.write("[al:Generated]\n")
                f.write("[by:Multi-Voice TTS Manager]\n\n")
                
                current_time = 0
                
                for segment, audio_file in zip(text_segments, audio_files):
                    # 获取实际音频时长
                    if os.path.exists(audio_file):
                        duration = SubtitleExporter.get_audio_duration_accurate(audio_file)
                    else:
                        duration = segment.get('actual_duration', len(segment['text']) * 300 / 1000.0)
                    
                    # 格式化时间
                    time_str = SubtitleExporter.format_lrc_time(current_time)
                    
                    # 写入字幕条目
                    f.write(f"[{time_str}]{segment['text']}\n")
                    
                    current_time += duration + gap_duration
                    
            return True
        except Exception as e:
            print(f"导出LRC失败: {e}")
            return False
    
    @staticmethod
    def get_audio_duration_accurate(audio_path):
        """获取音频准确时长（秒）"""
        try:
            # 尝试使用wave库获取时长
            if audio_path.lower().endswith('.wav'):
                import wave
                with wave.open(audio_path, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    return frames / float(sample_rate)
        except:
            pass
            
        try:
            # 尝试使用ffprobe获取时长
            import subprocess
            import os
            
            # 首先检查本地ffprobe
            local_ffprobe = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffprobe.exe")
            if os.path.exists(local_ffprobe):
                ffprobe_path = local_ffprobe
            else:
                # 检查系统PATH中的ffprobe
                try:
                    result = subprocess.run(['ffprobe', '-version'], capture_output=True)
                    if result.returncode == 0:
                        ffprobe_path = 'ffprobe'
                    else:
                        return None
                except:
                    return None
            
            cmd = [
                ffprobe_path, '-v', 'quiet', '-show_entries', 
                'format=duration', '-of', 'csv=p=0', audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except:
            pass
            
        # 默认估算：根据文件大小粗略估算
        try:
            file_size = os.path.getsize(audio_path)
            # 假设44.1kHz, 16bit, mono的WAV文件
            estimated_duration = file_size / (44100 * 2)
            return max(estimated_duration, 1.0)
        except:
            return 3.0  # 默认3秒
    
    @staticmethod
    def format_srt_time(seconds):
        """格式化SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def format_ass_time(seconds):
        """格式化ASS时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:01d}:{minutes:02d}:{secs:05.2f}"
    
    @staticmethod
    def format_lrc_time(seconds):
        """格式化LRC时间格式"""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes:02d}:{secs:05.2f}"

class MultiVoiceTTSManager(QWidget):
    """多人语音合成管理器"""
    
    def __init__(self):
        super().__init__()
        self.current_project = MultiVoiceProject()
        self.text_configs = {}  # 存储每个文本的配置
        self.tts_worker = None
        self.merge_worker = None
        self.generation_history = []  # 生成历史记录
        
        # 初始化音频播放器
        if PYGAME_PLAYER_AVAILABLE:
            self.audio_player = get_audio_player()
        else:
            self.audio_player = None
            
        self.init_ui()
        self.setup_styles()
        self.load_generation_history()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 标题
        layout.addWidget(StrongBodyLabel("多人语音合成"))
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 项目编辑标签页
        self.create_project_tab()
        
        # 生成历史标签页
        self.create_history_tab()
        
        layout.addWidget(self.tab_widget)
        
    def create_project_tab(self):
        """创建项目编辑标签页"""
        project_widget = QWidget()
        layout = QVBoxLayout(project_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 项目操作按钮区域
        project_btn_layout = QHBoxLayout()
        
        self.new_project_btn = PushButton(FluentIcon.ADD, "新建项目")
        self.new_project_btn.clicked.connect(self.new_project)
        
        self.save_project_btn = PushButton(FluentIcon.SAVE, "保存项目")
        self.save_project_btn.clicked.connect(self.save_project)
        
        self.load_project_btn = PushButton(FluentIcon.FOLDER, "加载项目")
        self.load_project_btn.clicked.connect(self.load_project)
        
        self.settings_btn = PushButton(FluentIcon.SETTING, "合成设置")
        self.settings_btn.clicked.connect(self.open_synthesis_settings)
        
        project_btn_layout.addWidget(self.new_project_btn)
        project_btn_layout.addWidget(self.save_project_btn)
        project_btn_layout.addWidget(self.load_project_btn)
        project_btn_layout.addWidget(self.settings_btn)
        project_btn_layout.addStretch()
        
        layout.addLayout(project_btn_layout)
        
        # 项目信息
        info_layout = QHBoxLayout()
        self.project_name_label = QLabel("项目名称: 未命名项目")
        self.project_name_label.setStyleSheet("font-weight: bold; color: #1976d2;")
        info_layout.addWidget(self.project_name_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # 文本操作按钮区域
        text_btn_layout = QHBoxLayout()
        
        self.smart_add_btn = PushButton(FluentIcon.ADD_TO, "智能添加文本")
        self.smart_add_btn.clicked.connect(self.smart_add_text)
        
        self.add_text_btn = PushButton(FluentIcon.ADD, "添加单个文本")
        self.add_text_btn.clicked.connect(self.add_single_text)
        
        self.delete_text_btn = PushButton(FluentIcon.DELETE, "删除选中")
        self.delete_text_btn.clicked.connect(self.delete_selected_texts)
        
        self.select_all_btn = PushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all_texts)
        
        self.select_none_btn = PushButton("取消全选")
        self.select_none_btn.clicked.connect(self.select_none_texts)
        
        self.batch_settings_btn = PushButton(FluentIcon.SETTING, "批量设置")
        self.batch_settings_btn.clicked.connect(self.open_batch_settings)
        
        # 添加合并功能按钮
        self.merge_up_btn = PushButton("↑ 向上合并")
        self.merge_up_btn.clicked.connect(self.merge_text_up)
        self.merge_up_btn.setToolTip("将选中的文本向上合并到上一行")
        
        self.merge_down_btn = PushButton("↓ 向下合并")
        self.merge_down_btn.clicked.connect(self.merge_text_down)
        self.merge_down_btn.setToolTip("将选中的文本向下合并到下一行")
        
        self.merge_selected_btn = PushButton("合并选中")
        self.merge_selected_btn.clicked.connect(self.merge_selected_texts)
        self.merge_selected_btn.setToolTip("将多个选中的文本合并为一个")
        
        text_btn_layout.addWidget(self.smart_add_btn)
        text_btn_layout.addWidget(self.add_text_btn)
        text_btn_layout.addWidget(self.delete_text_btn)
        text_btn_layout.addWidget(self.select_all_btn)
        text_btn_layout.addWidget(self.select_none_btn)
        text_btn_layout.addWidget(self.batch_settings_btn)
        text_btn_layout.addWidget(self.merge_up_btn)
        text_btn_layout.addWidget(self.merge_down_btn)
        text_btn_layout.addWidget(self.merge_selected_btn)
        text_btn_layout.addStretch()
        
        layout.addLayout(text_btn_layout)
        
        # 转换和合成按钮区域
        convert_btn_layout = QHBoxLayout()
        
        self.convert_selected_btn = PushButton(FluentIcon.PLAY, "转换选中文本")
        self.convert_selected_btn.clicked.connect(self.convert_selected_texts)
        
        self.merge_audio_btn = PushButton(FluentIcon.MEDIA, "合成音频")
        self.merge_audio_btn.clicked.connect(self.merge_audio)
        
        self.stop_btn = PushButton(FluentIcon.PAUSE, "停止")
        self.stop_btn.clicked.connect(self.stop_operations)
        self.stop_btn.setEnabled(False)
        
        convert_btn_layout.addWidget(self.convert_selected_btn)
        convert_btn_layout.addWidget(self.merge_audio_btn)
        convert_btn_layout.addWidget(self.stop_btn)
        convert_btn_layout.addStretch()
        
        layout.addLayout(convert_btn_layout)
        
        # 字幕导出按钮区域
        subtitle_btn_layout = QHBoxLayout()
        
        
        # 合成音频字幕导出按钮
        merged_subtitle_label = QLabel("合成音频字幕:")
        merged_subtitle_label.setStyleSheet("font-weight: bold; color: #1976d2;")
        subtitle_btn_layout.addWidget(merged_subtitle_label)
        
        self.export_merged_srt_btn = PushButton("导出SRT")
        self.export_merged_srt_btn.clicked.connect(lambda: self.export_subtitle('srt', True))
        self.export_merged_srt_btn.setToolTip("为合成音频导出SRT字幕，时间轴与音频完全同步（30ms间隔，避免顿挫感）")
        
        self.export_merged_ass_btn = PushButton("导出ASS")
        self.export_merged_ass_btn.clicked.connect(lambda: self.export_subtitle('ass', True))
        self.export_merged_ass_btn.setToolTip("为合成音频导出ASS字幕，时间轴与音频完全同步（30ms间隔，避免顿挫感）")
        
        self.export_merged_lrc_btn = PushButton("导出LRC")
        self.export_merged_lrc_btn.clicked.connect(lambda: self.export_subtitle('lrc', True))
        self.export_merged_lrc_btn.setToolTip("为合成音频导出LRC字幕，时间轴与音频完全同步（30ms间隔，避免顿挫感）")
        
        subtitle_btn_layout.addWidget(self.export_merged_srt_btn)
        subtitle_btn_layout.addWidget(self.export_merged_ass_btn)
        subtitle_btn_layout.addWidget(self.export_merged_lrc_btn)
        
        # 添加验证时间轴按钮
        self.validate_timing_btn = PushButton("验证时间轴")
        self.validate_timing_btn.clicked.connect(self.validate_current_timing)
        self.validate_timing_btn.setToolTip("验证当前项目的字幕时间轴准确性")
        subtitle_btn_layout.addWidget(self.validate_timing_btn)
        
        layout.addLayout(subtitle_btn_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666666; font-size: 14px;")
        layout.addWidget(self.status_label)
        
        # 文本列表表格
        self.create_text_table()
        layout.addWidget(self.text_table)
        
        self.tab_widget.addTab(project_widget, "项目编辑")
        
    def create_history_tab(self):
        """创建生成历史标签页"""
        history_widget = QWidget()
        layout = QVBoxLayout(history_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 历史记录操作按钮
        history_btn_layout = QHBoxLayout()
        
        self.refresh_history_btn = PushButton(FluentIcon.SYNC, "刷新历史")
        self.refresh_history_btn.clicked.connect(self.load_generation_history)
        
        self.clear_history_btn = PushButton(FluentIcon.DELETE, "清空历史")
        self.clear_history_btn.clicked.connect(self.clear_generation_history)
        
        self.open_output_dir_btn = PushButton(FluentIcon.FOLDER, "打开输出目录")
        self.open_output_dir_btn.clicked.connect(self.open_output_directory)
        
        history_btn_layout.addWidget(self.refresh_history_btn)
        history_btn_layout.addWidget(self.clear_history_btn)
        history_btn_layout.addWidget(self.open_output_dir_btn)
        history_btn_layout.addStretch()
        
        layout.addLayout(history_btn_layout)
        
        # 历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "生成时间", "项目名称", "文本数量", "音频文件", "字幕文件", "操作"
        ])
        
        # 设置表格属性
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        
        # 设置列宽
        self.history_table.setColumnWidth(0, 150)  # 生成时间
        self.history_table.setColumnWidth(1, 200)  # 项目名称
        self.history_table.setColumnWidth(2, 80)   # 文本数量
        self.history_table.setColumnWidth(3, 200)  # 音频文件
        self.history_table.setColumnWidth(4, 200)  # 字幕文件
        
        layout.addWidget(self.history_table)
        
        self.tab_widget.addTab(history_widget, "生成历史")      
  
    def create_text_table(self):
        """创建文本列表表格"""
        self.text_table = QTableWidget()
        self.text_table.setColumnCount(12)
        self.text_table.setHorizontalHeaderLabels([
            "选择", "文本内容", "参考音频", "推理模式", "Temperature", "Top P", "Top K", 
            "Num Beams", "Rep Penalty", "转换状态", "音频文件", "操作"
        ])
        
        # 设置表格属性
        self.text_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.text_table.setAlternatingRowColors(True)
        
        # 设置表头可手动调整大小
        header = self.text_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        
        # 设置默认列宽
        self.text_table.setColumnWidth(0, 50)   # 选择列
        self.text_table.setColumnWidth(1, 300)  # 文本内容列
        self.text_table.setColumnWidth(2, 150)  # 参考音频列
        self.text_table.setColumnWidth(3, 100)  # 推理模式列
        self.text_table.setColumnWidth(4, 90)   # Temperature列
        self.text_table.setColumnWidth(5, 80)   # Top P列
        self.text_table.setColumnWidth(6, 70)   # Top K列
        self.text_table.setColumnWidth(7, 90)   # Num Beams列
        self.text_table.setColumnWidth(8, 100)  # Rep Penalty列
        self.text_table.setColumnWidth(9, 100)  # 转换状态列
        self.text_table.setColumnWidth(10, 150) # 音频文件列
        
        # 设置行高
        self.text_table.verticalHeader().setDefaultSectionSize(80)
        self.text_table.verticalHeader().setMinimumSectionSize(60)
        self.text_table.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # 启用文本换行
        self.text_table.setWordWrap(True)
        
        # 连接单元格点击事件
        self.text_table.cellClicked.connect(self.on_cell_clicked)
        
    def setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            MultiVoiceTTSManager {
                background-color: #ffffff;
                color: #333333;
            }
            QTableWidget {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                gridline-color: #e0e0e0;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #f0f0f0;
                color: #333333;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #333333;
                padding: 6px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
                font-size: 12px;
            }
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #f5f5f5;
                color: #333333;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #1976d2;
                border-bottom: 2px solid #1976d2;
            }
            QTabBar::tab:hover {
                background-color: #e8f4fd;
            }
        """)
        
    def new_project(self):
        """新建项目"""
        project_name, ok = QInputDialog.getText(self, "新建项目", "请输入项目名称:")
        if ok and project_name.strip():
            self.current_project = MultiVoiceProject()
            self.current_project.project_name = project_name.strip()
            self.text_configs = {}
            
            # 自动保存到project目录
            self.auto_save_project()
            
            self.update_project_info()
            self.refresh_text_table()
            
            InfoBar.success(
                title="项目已创建",
                content=f"新项目 '{project_name}' 已创建并保存到project目录",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
    def save_project(self):
        """保存项目"""
        if not self.current_project.project_name:
            MessageBox("提示", "请先创建或命名项目", self).exec()
            return
            
        # 直接保存到project目录，覆盖现有文件
        self.auto_save_project()
        
    def auto_save_project(self):
        """自动保存项目到project目录"""
        if not self.current_project.project_name:
            return
            
        try:
            # 确保project目录存在
            os.makedirs("project", exist_ok=True)
            
            # 生成安全的文件名
            safe_project_name = self.generate_safe_project_name(self.current_project.project_name)
            file_path = os.path.join("project", f"{safe_project_name}.mvtts")
            
            # 更新修改时间
            self.current_project.modified_time = datetime.now()
            
            # 保存项目数据
            project_data = self.current_project.to_dict()
            project_data['text_configs'] = self.text_configs
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
                
            InfoBar.success(
                title="保存成功",
                content=f"项目已保存到: project/{safe_project_name}.mvtts",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            MessageBox("错误", f"保存项目失败: {str(e)}", self).exec()
    
    def generate_safe_project_name(self, project_name):
        """生成安全的项目目录名"""
        import re
        # 移除所有不安全的字符
        safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', project_name)
        # 替换空格为下划线
        safe_name = re.sub(r'\s+', '_', safe_name.strip())
        # 移除开头和结尾的点号
        safe_name = safe_name.strip('.')
        
        # 如果处理后为空，使用默认名称
        if not safe_name:
            safe_name = "unnamed_project"
            
        return safe_name
    
    def validate_audio_paths(self):
        """验证并更新音频路径状态"""
        for segment in self.current_project.text_segments:
            audio_path = segment.get('audio_path', '')
            if audio_path and not os.path.exists(audio_path):
                # 如果保存的路径不存在，清除路径信息
                segment.pop('audio_path', None)
                segment.pop('actual_duration', None)
                
    def load_project(self):
        """加载项目"""
        # 优先从project目录加载
        project_dir = "project"
        if os.path.exists(project_dir):
            initial_dir = project_dir
        else:
            initial_dir = ""
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "加载项目",
            initial_dir,
            "多人语音合成项目 (*.mvtts);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                    
                self.current_project = MultiVoiceProject.from_dict(project_data)
                self.text_configs = project_data.get('text_configs', {})
                
                # 验证音频路径
                self.validate_audio_paths()
                
                self.update_project_info()
                self.refresh_text_table()
                
                InfoBar.success(
                    title="加载成功",
                    content=f"项目 '{self.current_project.project_name}' 已加载",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                MessageBox("错误", f"加载项目失败: {str(e)}", self).exec()
                
    def update_project_info(self):
        """更新项目信息显示"""
        if self.current_project.project_name:
            self.project_name_label.setText(f"项目名称: {self.current_project.project_name}")
        else:
            self.project_name_label.setText("项目名称: 未命名项目")
            
    def smart_add_text(self):
        """智能添加文本"""
        dialog = SmartTextAddDialog(self)
        if dialog.exec() == QDialog.Accepted:
            segments_with_duration = dialog.get_text_segments()
            
            for segment_data in segments_with_duration:
                text_id = str(uuid.uuid4())
                segment = {
                    'id': text_id,
                    'text': segment_data['text'],
                    'duration': segment_data['duration']
                }
                
                self.current_project.text_segments.append(segment)
                
                # 初始化配置
                self.text_configs[text_id] = {
                    'reference_voice': '',
                    'infer_mode': '普通推理',
                    'tts_params': {
                        'do_sample': True,
                        'temperature': 1.0,
                        'top_p': 0.8,
                        'top_k': 30,
                        'num_beams': 3,
                        'repetition_penalty': 10.0,
                    }
                }
                
            self.refresh_text_table()
            
            # 自动保存项目
            if self.current_project.project_name:
                self.auto_save_project()
            
            InfoBar.success(
                title="文本已添加",
                content=f"已添加 {len(segments_with_duration)} 个文本段落",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
    def add_single_text(self):
        """添加单个文本"""
        dialog = MultiLineTextEditDialog("", self)
        if dialog.exec() == QDialog.Accepted:
            text_content = dialog.get_text()
            if text_content.strip():
                text_id = str(uuid.uuid4())
                segment = {
                    'id': text_id,
                    'text': text_content.strip(),
                    'duration': len(text_content) * 300  # 默认每字300ms
                }
                
                self.current_project.text_segments.append(segment)
                
                # 初始化配置
                self.text_configs[text_id] = {
                    'reference_voice': '',
                    'infer_mode': '普通推理',
                    'tts_params': {
                        'do_sample': True,
                        'temperature': 1.0,
                        'top_p': 0.8,
                        'top_k': 30,
                        'num_beams': 3,
                        'repetition_penalty': 10.0,
                    }
                }
                
                self.refresh_text_table()
                
                # 自动保存项目
                if self.current_project.project_name:
                    self.auto_save_project()
                
                InfoBar.success(
                    title="文本已添加",
                    content="新文本段落已添加",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=1500,
                    parent=self
                )
                
    def delete_selected_texts(self):
        """删除选中的文本"""
        selected_rows = []
        for row in range(self.text_table.rowCount()):
            checkbox = self.text_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_rows.append(row)
                
        if not selected_rows:
            MessageBox("提示", "请先选择要删除的文本", self).exec()
            return
            
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除选中的 {len(selected_rows)} 个文本段落吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 从后往前删除，避免索引变化
            for row in reversed(selected_rows):
                if row < len(self.current_project.text_segments):
                    segment = self.current_project.text_segments[row]
                    text_id = segment['id']
                    
                    # 删除配置
                    if text_id in self.text_configs:
                        del self.text_configs[text_id]
                    
                    # 删除段落
                    del self.current_project.text_segments[row]
                    
            self.refresh_text_table()
            
            # 自动保存项目
            if self.current_project.project_name:
                self.auto_save_project()
            
            InfoBar.success(
                title="删除成功",
                content=f"已删除 {len(selected_rows)} 个文本段落",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
    def select_all_texts(self):
        """全选所有文本"""
        for row in range(self.text_table.rowCount()):
            checkbox = self.text_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
                
    def select_none_texts(self):
        """取消全选"""
        for row in range(self.text_table.rowCount()):
            checkbox = self.text_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
                
    def open_batch_settings(self):
        """打开批量设置对话框"""
        dialog = BatchParameterDialog(self)
        if dialog.exec() == QDialog.Accepted:
            settings = dialog.get_batch_settings()
            
            # 保存当前选中状态
            selected_text_ids = []
            for row in range(self.text_table.rowCount()):
                checkbox = self.text_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    if row < len(self.current_project.text_segments):
                        segment = self.current_project.text_segments[row]
                        selected_text_ids.append(segment['id'])
            
            # 应用批量设置到选中的文本
            applied_count = 0
            for row in range(self.text_table.rowCount()):
                checkbox = self.text_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    if row < len(self.current_project.text_segments):
                        segment = self.current_project.text_segments[row]
                        text_id = segment['id']
                        
                        if text_id in self.text_configs:
                            config = self.text_configs[text_id]
                            
                            # 应用设置
                            if 'reference_voice' in settings:
                                config['reference_voice'] = settings['reference_voice']
                            if 'infer_mode' in settings:
                                config['infer_mode'] = settings['infer_mode']
                            if 'tts_params' in settings:
                                config['tts_params'].update(settings['tts_params'])
                                
                            applied_count += 1
                            
            if applied_count > 0:
                # 刷新表格并恢复选中状态
                self.refresh_text_table_with_selection(selected_text_ids)
                InfoBar.success(
                    title="批量设置完成",
                    content=f"已应用设置到 {applied_count} 个文本",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            else:
                MessageBox("提示", "请先选择要设置的文本", self).exec()
                
    def refresh_text_table(self):
        """刷新文本表格"""
        self.text_table.setRowCount(len(self.current_project.text_segments))
        
        for row, segment in enumerate(self.current_project.text_segments):
            text_id = segment['id']
            text_content = segment['text']
            
            # 确保配置存在
            if text_id not in self.text_configs:
                self.text_configs[text_id] = {
                    'reference_voice': '',
                    'infer_mode': '普通推理',
                    'tts_params': {
                        'do_sample': True,
                        'temperature': 1.0,
                        'top_p': 0.8,
                        'top_k': 30,
                        'num_beams': 3,
                        'repetition_penalty': 10.0,
                    }
                }
                
            config = self.text_configs[text_id]
            params = config['tts_params']
            
            # 选择框
            checkbox = QCheckBox()
            self.text_table.setCellWidget(row, 0, checkbox)
            
            # 文本内容
            text_item = QTableWidgetItem(text_content)
            text_item.setData(Qt.UserRole, text_id)
            self.text_table.setItem(row, 1, text_item)
            
            # 参考音频预览组件
            audio_preview = AudioPreviewWidget()
            audio_preview.set_audio_path(config['reference_voice'])
            self.text_table.setCellWidget(row, 2, audio_preview)
            
            # 推理模式
            mode_item = QTableWidgetItem(config['infer_mode'])
            self.text_table.setItem(row, 3, mode_item)
            
            # TTS参数
            temp_spin = ParameterSpinBox(0.1, 2.0, params['temperature'], 0.1, 2)
            temp_spin.valueChanged.connect(lambda v, tid=text_id: self.update_parameter(tid, 'temperature', v))
            self.text_table.setCellWidget(row, 4, temp_spin)
            
            top_p_spin = ParameterSpinBox(0.0, 1.0, params['top_p'], 0.01, 3)
            top_p_spin.valueChanged.connect(lambda v, tid=text_id: self.update_parameter(tid, 'top_p', v))
            self.text_table.setCellWidget(row, 5, top_p_spin)
            
            top_k_spin = ParameterIntSpinBox(0, 100, params['top_k'])
            top_k_spin.valueChanged.connect(lambda v, tid=text_id: self.update_parameter(tid, 'top_k', v))
            self.text_table.setCellWidget(row, 6, top_k_spin)
            
            beams_spin = ParameterIntSpinBox(1, 10, params['num_beams'])
            beams_spin.valueChanged.connect(lambda v, tid=text_id: self.update_parameter(tid, 'num_beams', v))
            self.text_table.setCellWidget(row, 7, beams_spin)
            
            rep_penalty_spin = ParameterSpinBox(0.1, 20.0, params['repetition_penalty'], 0.1, 1)
            rep_penalty_spin.valueChanged.connect(lambda v, tid=text_id: self.update_parameter(tid, 'repetition_penalty', v))
            self.text_table.setCellWidget(row, 8, rep_penalty_spin)
            
            # 转换状态和音频文件
            audio_path = segment.get('audio_path', '')
            if audio_path and os.path.exists(audio_path):
                # 已有音频文件
                status_item = QTableWidgetItem("已转换")
                status_item.setForeground(QColor(76, 175, 80))  # 绿色
                audio_file_item = QTableWidgetItem(audio_path)
            else:
                # 未转换或文件不存在
                status_item = QTableWidgetItem("未转换")
                status_item.setForeground(QColor(128, 128, 128))  # 灰色
                audio_file_item = QTableWidgetItem("")
                
            self.text_table.setItem(row, 9, status_item)
            self.text_table.setItem(row, 10, audio_file_item)
            
            # 操作按钮
            self.create_operation_buttons(row, text_id)
            
        # 调整行高
        self.text_table.resizeRowsToContents()
        
    def refresh_text_table_with_selection(self, selected_text_ids):
        """刷新文本表格并恢复选中状态"""
        self.refresh_text_table()
        
        # 恢复选中状态
        for row in range(self.text_table.rowCount()):
            if row < len(self.current_project.text_segments):
                segment = self.current_project.text_segments[row]
                text_id = segment['id']
                
                if text_id in selected_text_ids:
                    checkbox = self.text_table.cellWidget(row, 0)
                    if checkbox:
                        checkbox.setChecked(True)
        
    def create_operation_buttons(self, row, text_id):
        """创建操作按钮"""
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(2, 2, 2, 2)
        button_layout.setSpacing(2)
        
        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.setFixedSize(40, 25)
        edit_btn.clicked.connect(lambda: self.edit_text(row))
        
        # 播放按钮
        play_btn = QPushButton("▶")
        play_btn.setFixedSize(25, 25)
        play_btn.clicked.connect(lambda: self.play_audio(row))
        
        # 向上合并按钮
        merge_up_btn = QPushButton("↑")
        merge_up_btn.setFixedSize(25, 25)
        merge_up_btn.setToolTip("向上合并")
        merge_up_btn.clicked.connect(lambda: self.merge_single_text_up(row))
        
        # 向下合并按钮
        merge_down_btn = QPushButton("↓")
        merge_down_btn.setFixedSize(25, 25)
        merge_down_btn.setToolTip("向下合并")
        merge_down_btn.clicked.connect(lambda: self.merge_single_text_down(row))
        
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(play_btn)
        button_layout.addWidget(merge_up_btn)
        button_layout.addWidget(merge_down_btn)
        
        self.text_table.setCellWidget(row, 11, button_widget)
        
    def update_parameter(self, text_id, param_name, value):
        """更新参数值"""
        if text_id in self.text_configs:
            self.text_configs[text_id]['tts_params'][param_name] = value
            
    def on_cell_clicked(self, row, col):
        """处理单元格点击事件"""
        if col == 2:  # 参考音频列
            self.select_reference_audio(row)
        elif col == 3:  # 推理模式列
            self.select_infer_mode(row)
            
    def select_reference_audio(self, row):
        """选择参考音频"""
        dialog = AudioTreeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            audio_path = dialog.get_selected_audio_path()
            if audio_path and row < len(self.current_project.text_segments):
                segment = self.current_project.text_segments[row]
                text_id = segment['id']
                
                self.text_configs[text_id]['reference_voice'] = audio_path
                
                # 更新表格显示
                audio_preview = self.text_table.cellWidget(row, 2)
                if audio_preview:
                    audio_preview.set_audio_path(audio_path)
                    
    def select_infer_mode(self, row):
        """选择推理模式"""
        if row >= len(self.current_project.text_segments):
            return
            
        segment = self.current_project.text_segments[row]
        text_id = segment['id']
        current_mode = self.text_configs[text_id]['infer_mode']
        
        modes = ["普通推理", "批次推理"]
        mode, ok = QInputDialog.getItem(
            self, "选择推理模式", "推理模式:", modes, 
            modes.index(current_mode), False
        )
        
        if ok:
            self.text_configs[text_id]['infer_mode'] = mode
            mode_item = self.text_table.item(row, 3)
            mode_item.setText(mode)
            
    def edit_text(self, row):
        """编辑文本"""
        if row >= len(self.current_project.text_segments):
            return
            
        segment = self.current_project.text_segments[row]
        original_text = segment['text']
        
        dialog = MultiLineTextEditDialog(original_text, self)
        if dialog.exec() == QDialog.Accepted:
            new_text = dialog.get_text()
            if new_text.strip():
                segment['text'] = new_text.strip()
                segment['duration'] = len(new_text) * 300  # 重新计算时长
                
                # 更新表格显示
                text_item = self.text_table.item(row, 1)
                text_item.setText(new_text.strip())
                
                InfoBar.success(
                    title="文本已更新",
                    content="文本内容已保存",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=1500,
                    parent=self
                )
                
    def play_audio(self, row):
        """播放音频"""
        audio_file_item = self.text_table.item(row, 10)
        if audio_file_item and audio_file_item.text():
            audio_path = audio_file_item.text()
            if os.path.exists(audio_path) and self.audio_player:
                self.audio_player.play_audio(audio_path)
            else:
                MessageBox("提示", "音频文件不存在或播放器不可用", self).exec()
        else:
            MessageBox("提示", "该文本尚未转换为音频", self).exec()
            
    def convert_selected_texts(self):
        """转换选中的文本"""
        selected_items = self.get_selected_text_items()
        if not selected_items:
            MessageBox("提示", "请先选择要转换的文本", self).exec()
            return
            
        # 检查配置
        missing_audio = []
        for item in selected_items:
            if not item['reference_voice'] or not os.path.exists(item['reference_voice']):
                missing_audio.append(item['text_content'][:20] + "...")
                
        if missing_audio:
            MessageBox("错误", f"以下文本缺少参考音频:\n" + "\n".join(missing_audio), self).exec()
            return
            
        # 更新UI状态
        self.convert_selected_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 更新选中文本的状态
        for item in selected_items:
            row = item['row']
            status_item = self.text_table.item(row, 9)
            status_item.setText("等待转换")
            status_item.setForeground(QColor(255, 165, 0))  # 橙色
            
        self.status_label.setText(f"开始转换 {len(selected_items)} 个文本...")
        
        # 启动工作线程
        self.tts_worker = MultiVoiceTTSWorker(selected_items, self.current_project.project_name)
        self.tts_worker.progress_updated.connect(self.on_progress_updated)
        self.tts_worker.conversion_finished.connect(self.on_conversion_finished)
        self.tts_worker.error_occurred.connect(self.on_error_occurred)
        self.tts_worker.finished.connect(self.on_worker_finished)
        self.tts_worker.start()
        
    def get_selected_text_items(self):
        """获取选中的文本项"""
        selected_items = []
        for row in range(self.text_table.rowCount()):
            checkbox = self.text_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked() and row < len(self.current_project.text_segments):
                segment = self.current_project.text_segments[row]
                text_id = segment['id']
                config = self.text_configs.get(text_id, {})
                
                selected_items.append({
                    'text_id': text_id,
                    'text_content': segment['text'],
                    'reference_voice': config.get('reference_voice', ''),
                    'infer_mode': config.get('infer_mode', '普通推理'),
                    'tts_params': config.get('tts_params', {}),
                    'row': row
                })
        return selected_items
        
    def merge_audio(self):
        """合成音频"""
        # 检查是否有已转换的音频，优先使用保存的音频路径
        audio_files = []
        for segment in self.current_project.text_segments:
            audio_path = segment.get('audio_path', '')
            if audio_path and os.path.exists(audio_path):
                audio_files.append(audio_path)
            else:
                # 如果保存的路径不存在，尝试从表格获取
                for row in range(self.text_table.rowCount()):
                    if row < len(self.current_project.text_segments):
                        if self.current_project.text_segments[row]['id'] == segment['id']:
                            audio_file_item = self.text_table.item(row, 10)
                            if audio_file_item and audio_file_item.text() and os.path.exists(audio_file_item.text()):
                                audio_files.append(audio_file_item.text())
                            break
                
        if not audio_files:
            MessageBox("提示", "没有可合成的音频文件，请先转换文本", self).exec()
            return
            
        # 选择输出路径
        if self.current_project.project_name:
            safe_project_name = self.generate_safe_project_name(self.current_project.project_name)
            project_output_dir = os.path.join("output", safe_project_name)
        else:
            project_output_dir = "output"
        
        os.makedirs(project_output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = self.current_project.project_name or "未命名项目"
        safe_project_name = self.generate_safe_project_name(project_name)
        default_filename = f"{safe_project_name}_合成音频_{timestamp}.wav"
        
        output_path, _ = QFileDialog.getSaveFileName(
            self, "保存合成音频",
            os.path.join(project_output_dir, default_filename),
            "音频文件 (*.wav *.mp3);;所有文件 (*)"
        )
        
        if output_path:
            # 更新UI状态
            self.merge_audio_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            self.status_label.setText("正在合成音频...")
            
            # 启动合成线程
            gap_duration = self.current_project.output_settings.get('gap_duration', 0.03)
            add_silence_gap = self.current_project.output_settings.get('add_silence_gap', True)
            self.merge_worker = AudioMergeWorker(audio_files, output_path, gap_duration, add_silence_gap)
            self.merge_worker.progress_updated.connect(self.on_progress_updated)
            self.merge_worker.merge_finished.connect(self.on_merge_finished)
            self.merge_worker.error_occurred.connect(self.on_merge_error)
            self.merge_worker.start()
            
    def export_subtitle(self, format_type, for_merged_audio=False):
        """导出字幕"""
        if not self.current_project.text_segments:
            MessageBox("提示", "没有文本内容可导出", self).exec()
            return
            
        # 选择保存路径
        if self.current_project.project_name:
            safe_project_name = self.generate_safe_project_name(self.current_project.project_name)
            project_output_dir = os.path.join("output", safe_project_name)
        else:
            project_output_dir = "output"
        
        os.makedirs(project_output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = self.current_project.project_name or "未命名项目"
        safe_project_name = self.generate_safe_project_name(project_name)
        
        if for_merged_audio:
            default_filename = f"{safe_project_name}_合成音频字幕_{timestamp}.{format_type}"
        else:
            default_filename = f"{safe_project_name}_字幕_{timestamp}.{format_type}"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"导出{format_type.upper()}字幕",
            os.path.join(project_output_dir, default_filename),
            f"{format_type.upper()}字幕文件 (*.{format_type});;所有文件 (*)"
        )
        
        if file_path:
            try:
                # 获取项目设置中的间隔时间
                gap_duration = self.current_project.output_settings.get('gap_duration', 0.03)
                
                if for_merged_audio:
                    # 为合成音频导出字幕
                    audio_files = self.get_merged_audio_files()
                    if not audio_files:
                        MessageBox("错误", "没有找到可用的音频文件", self).exec()
                        return
                    
                    # 验证时间轴
                    timing_data = self.validate_subtitle_timing(audio_files, gap_duration)
                    if timing_data:
                        # 询问是否显示时间轴信息
                        reply = QMessageBox.question(
                            self, "时间轴验证", 
                            f"检测到 {len(audio_files)} 个音频文件，总时长约 {timing_data['total_duration']:.2f} 秒。\n是否查看详细的时间轴信息？",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if reply == QMessageBox.Yes:
                            self.show_subtitle_timing_info(timing_data)
                    
                    if format_type == 'srt':
                        success = SubtitleExporter.export_srt_for_merged_audio(
                            self.current_project.text_segments, audio_files, file_path, gap_duration
                        )
                    elif format_type == 'ass':
                        success = SubtitleExporter.export_ass_for_merged_audio(
                            self.current_project.text_segments, audio_files, file_path, gap_duration
                        )
                    elif format_type == 'lrc':
                        success = SubtitleExporter.export_lrc_for_merged_audio(
                            self.current_project.text_segments, audio_files, file_path, gap_duration
                        )
                    else:
                        success = False
                else:
                    # 使用原有的导出逻辑
                    # 计算音频时长
                    audio_durations = []
                    for segment in self.current_project.text_segments:
                        # 优先使用已保存的实际音频时长
                        if 'actual_duration' in segment and segment['actual_duration'] > 0:
                            duration = segment['actual_duration']
                        elif 'audio_path' in segment and segment['audio_path'] and os.path.exists(segment['audio_path']):
                            # 从保存的音频路径获取时长
                            duration = self.get_audio_duration(segment['audio_path'])
                            # 更新段落的实际时长
                            segment['actual_duration'] = duration
                        else:
                            # 使用估算时长
                            duration = segment.get('duration', len(segment['text']) * 300) / 1000.0
                        
                        audio_durations.append(duration)
                    
                    if format_type == 'srt':
                        success = SubtitleExporter.export_srt(self.current_project.text_segments, audio_durations, file_path, gap_duration)
                    elif format_type == 'ass':
                        success = SubtitleExporter.export_ass(self.current_project.text_segments, audio_durations, file_path, gap_duration)
                    elif format_type == 'lrc':
                        success = SubtitleExporter.export_lrc(self.current_project.text_segments, audio_durations, file_path, gap_duration)
                    else:
                        success = False
                    
                if success:
                    InfoBar.success(
                        title="导出成功",
                        content=f"{format_type.upper()}字幕已导出到: {os.path.basename(file_path)}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                else:
                    MessageBox("错误", f"导出{format_type.upper()}字幕失败", self).exec()
                    
            except Exception as e:
                MessageBox("错误", f"导出字幕失败: {str(e)}", self).exec()
    
    def get_merged_audio_files(self):
        """获取合成音频的文件列表（按项目中的顺序）"""
        audio_files = []
        for segment in self.current_project.text_segments:
            audio_path = segment.get('audio_path', '')
            if audio_path and os.path.exists(audio_path):
                audio_files.append(audio_path)
            else:
                # 如果保存的路径不存在，尝试从表格获取
                for row in range(self.text_table.rowCount()):
                    if row < len(self.current_project.text_segments):
                        if self.current_project.text_segments[row]['id'] == segment['id']:
                            audio_file_item = self.text_table.item(row, 10)
                            if audio_file_item and audio_file_item.text() and os.path.exists(audio_file_item.text()):
                                audio_files.append(audio_file_item.text())
                            break
        return audio_files
    
    def get_audio_duration(self, audio_path):
        """获取音频时长（秒）"""
        try:
            # 尝试使用wave库获取时长
            if audio_path.lower().endswith('.wav'):
                import wave
                with wave.open(audio_path, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    return frames / float(sample_rate)
        except:
            pass
            
        try:
            # 尝试使用ffprobe获取时长
            ffprobe_path = self.get_ffprobe_path()
            if ffprobe_path:
                cmd = [
                    ffprobe_path, '-v', 'quiet', '-show_entries', 
                    'format=duration', '-of', 'csv=p=0', audio_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    return float(result.stdout.strip())
        except:
            pass
            
        # 默认估算：根据文件大小粗略估算
        try:
            file_size = os.path.getsize(audio_path)
            # 假设44.1kHz, 16bit, mono的WAV文件
            estimated_duration = file_size / (44100 * 2)
            return max(estimated_duration, 1.0)
        except:
            return 3.0  # 默认3秒
    
    def get_ffprobe_path(self):
        """获取ffprobe路径"""
        # 首先检查本地ffmpeg目录
        local_ffprobe = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffprobe.exe")
        if os.path.exists(local_ffprobe):
            return local_ffprobe
            
        # 检查系统PATH中的ffprobe
        try:
            result = subprocess.run(['ffprobe', '-version'], capture_output=True)
            if result.returncode == 0:
                return 'ffprobe'
        except:
            pass
            
        return None
    
    def stop_operations(self):
        """停止所有操作"""
        if self.tts_worker and self.tts_worker.isRunning():
            self.tts_worker.cancel()
        if self.merge_worker and self.merge_worker.isRunning():
            self.merge_worker.cancel()
            
        self.status_label.setText("正在停止操作...")
        
    @pyqtSlot(int, str)
    def on_progress_updated(self, progress, status):
        """进度更新"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
        
    @pyqtSlot(str, str, bool, float)
    def on_conversion_finished(self, text_id, output_path, success, duration):
        """转换完成"""
        # 查找对应的行
        for row in range(len(self.current_project.text_segments)):
            segment = self.current_project.text_segments[row]
            if segment['id'] == text_id:
                if row < self.text_table.rowCount():
                    status_item = self.text_table.item(row, 9)
                    audio_file_item = self.text_table.item(row, 10)
                    
                    if success:
                        status_item.setText("转换成功")
                        status_item.setForeground(QColor(76, 175, 80))  # 绿色
                        audio_file_item.setText(output_path)
                        # 更新段落的实际音频时长和路径
                        segment['actual_duration'] = duration
                        segment['audio_path'] = os.path.abspath(output_path)  # 保存绝对路径
                        # 自动保存项目
                        if self.current_project.project_name:
                            self.auto_save_project()
                    else:
                        status_item.setText("转换失败")
                        status_item.setForeground(QColor(244, 67, 54))  # 红色
                break
                
    @pyqtSlot(str, str)
    def on_error_occurred(self, text_id, error_message):
        """转换错误"""
        print(f"转换错误 [{text_id}]: {error_message}")
        
    @pyqtSlot()
    def on_worker_finished(self):
        """工作线程完成"""
        self.convert_selected_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("转换完成")
        
        InfoBar.success(
            title="转换完成",
            content="文本转语音任务已完成",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        
    @pyqtSlot(str, bool)
    def on_merge_finished(self, output_path, success):
        """合成完成"""
        self.merge_audio_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("合成完成")
            
            # 添加到生成历史
            self.add_to_generation_history(output_path)
            
            InfoBar.success(
                title="合成完成",
                content=f"音频已保存到: {os.path.basename(output_path)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            self.status_label.setText("合成失败")
    
    def auto_generate_subtitles_for_merged_audio(self, audio_path):
        """为合成音频自动生成字幕文件"""
        subtitle_files = []
        
        try:
            # 获取项目设置中的间隔时间
            gap_duration = self.current_project.output_settings.get('gap_duration', 0.03)
            
            # 获取音频文件列表
            audio_files = self.get_merged_audio_files()
            if not audio_files:
                return subtitle_files
            
            # 生成字幕文件路径
            audio_dir = os.path.dirname(audio_path)
            audio_name = os.path.splitext(os.path.basename(audio_path))[0]
            
            # 生成SRT字幕
            srt_path = os.path.join(audio_dir, f"{audio_name}.srt")
            if SubtitleExporter.export_srt_for_merged_audio(
                self.current_project.text_segments, audio_files, srt_path, gap_duration
            ):
                subtitle_files.append(srt_path)
            
            # 生成ASS字幕
            ass_path = os.path.join(audio_dir, f"{audio_name}.ass")
            if SubtitleExporter.export_ass_for_merged_audio(
                self.current_project.text_segments, audio_files, ass_path, gap_duration
            ):
                subtitle_files.append(ass_path)
            
            # 生成LRC字幕
            lrc_path = os.path.join(audio_dir, f"{audio_name}.lrc")
            if SubtitleExporter.export_lrc_for_merged_audio(
                self.current_project.text_segments, audio_files, lrc_path, gap_duration
            ):
                subtitle_files.append(lrc_path)
                
        except Exception as e:
            print(f"自动生成字幕失败: {e}")
            
        return subtitle_files
    
    @pyqtSlot(str)
    def on_merge_error(self, error_message):
        """合成错误"""
        self.merge_audio_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("合成失败")
        
        MessageBox("错误", f"音频合成失败: {error_message}", self).exec()
        
    def add_to_generation_history(self, audio_path, subtitle_files=None):
        """添加到生成历史"""
        if subtitle_files is None:
            subtitle_files = []
            
        history_item = {
            'timestamp': datetime.now().isoformat(),
            'project_name': self.current_project.project_name,
            'text_count': len(self.current_project.text_segments),
            'audio_path': audio_path,
            'subtitle_files': subtitle_files
        }
        
        self.generation_history.append(history_item)
        self.save_generation_history()
        self.load_generation_history()  # 刷新历史表格
        
    def load_generation_history(self):
        """加载生成历史"""
        history_file = "output/generation_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.generation_history = json.load(f)
            except:
                self.generation_history = []
        else:
            self.generation_history = []
            
        # 更新历史表格
        self.update_history_table()
        
    def save_generation_history(self):
        """保存生成历史"""
        os.makedirs("output", exist_ok=True)
        history_file = "output/generation_history.json"
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.generation_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存生成历史失败: {e}")
            
    def update_history_table(self):
        """更新历史表格"""
        self.history_table.setRowCount(len(self.generation_history))
        
        for row, item in enumerate(reversed(self.generation_history)):  # 最新的在前面
            # 生成时间
            timestamp = datetime.fromisoformat(item['timestamp'])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            time_item = QTableWidgetItem(time_str)
            self.history_table.setItem(row, 0, time_item)
            
            # 项目名称
            project_item = QTableWidgetItem(item['project_name'])
            self.history_table.setItem(row, 1, project_item)
            
            # 文本数量
            count_item = QTableWidgetItem(str(item['text_count']))
            self.history_table.setItem(row, 2, count_item)
            
            # 音频文件
            audio_path = item['audio_path']
            audio_name = os.path.basename(audio_path) if audio_path else ""
            audio_item = QTableWidgetItem(audio_name)
            audio_item.setToolTip(audio_path)
            self.history_table.setItem(row, 3, audio_item)
            
            # 字幕文件
            subtitle_files = item.get('subtitle_files', [])
            subtitle_text = ", ".join([os.path.basename(f) for f in subtitle_files])
            subtitle_item = QTableWidgetItem(subtitle_text)
            self.history_table.setItem(row, 4, subtitle_item)
            
            # 操作按钮
            self.create_history_operation_buttons(row, item)
            
    def create_history_operation_buttons(self, row, item):
        """创建历史记录操作按钮"""
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(2, 2, 2, 2)
        button_layout.setSpacing(2)
        
        # 播放按钮
        play_btn = QPushButton("▶")
        play_btn.setFixedSize(25, 25)
        play_btn.clicked.connect(lambda: self.play_history_audio(item['audio_path']))
        
        # 删除按钮
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(25, 25)
        delete_btn.clicked.connect(lambda: self.delete_history_item(row))
        
        button_layout.addWidget(play_btn)
        button_layout.addWidget(delete_btn)
        
        self.history_table.setCellWidget(row, 5, button_widget)
        
    def play_history_audio(self, audio_path):
        """播放历史音频"""
        if os.path.exists(audio_path) and self.audio_player:
            self.audio_player.play_audio(audio_path)
        else:
            MessageBox("提示", "音频文件不存在或播放器不可用", self).exec()
            
    def delete_history_item(self, row):
        """删除历史记录项"""
        reply = QMessageBox.question(
            self, "确认删除", 
            "确定要删除这条历史记录吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 计算实际索引（因为表格是倒序显示的）
            actual_index = len(self.generation_history) - 1 - row
            if 0 <= actual_index < len(self.generation_history):
                del self.generation_history[actual_index]
                self.save_generation_history()
                self.update_history_table()
                
    def clear_generation_history(self):
        """清空生成历史"""
        reply = QMessageBox.question(
            self, "确认清空", 
            "确定要清空所有生成历史吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.generation_history = []
            self.save_generation_history()
            self.update_history_table()
            
            InfoBar.success(
                title="历史已清空",
                content="生成历史记录已清空",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
    def open_output_directory(self):
        """打开输出目录"""
        output_dir = os.path.abspath("output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        try:
            import subprocess
            import platform
            system = platform.system()
            if system == "Windows":
                os.startfile(output_dir)
            elif system == "Darwin":
                subprocess.run(["open", output_dir])
            else:
                subprocess.run(["xdg-open", output_dir])
        except Exception as e:
            MessageBox("错误", f"无法打开目录: {str(e)}", self).exec()
    
    def validate_subtitle_timing(self, audio_files, gap_duration=0.03):
        """验证字幕时间轴准确性"""
        try:
            total_duration = 0
            timing_info = []
            
            for i, audio_file in enumerate(audio_files):
                if os.path.exists(audio_file):
                    duration = SubtitleExporter.get_audio_duration_accurate(audio_file)
                    start_time = total_duration
                    end_time = total_duration + duration
                    
                    timing_info.append({
                        'index': i + 1,
                        'audio_file': os.path.basename(audio_file),
                        'duration': duration,
                        'start_time': start_time,
                        'end_time': end_time
                    })
                    
                    total_duration = end_time + gap_duration
                else:
                    timing_info.append({
                        'index': i + 1,
                        'audio_file': '文件不存在',
                        'duration': 0,
                        'start_time': total_duration,
                        'end_time': total_duration
                    })
                    total_duration += gap_duration
            
            return {
                'total_duration': total_duration,
                'timing_info': timing_info,
                'gap_duration': gap_duration
            }
        except Exception as e:
            print(f"验证字幕时间轴失败: {e}")
            return None
    
    def show_subtitle_timing_info(self, timing_data):
        """显示字幕时间轴信息"""
        if not timing_data:
            return
            
        # 使用新的对话框显示时间轴信息
        dialog = TimingInfoDialog(timing_data, self)
        dialog.exec()
    
    def validate_current_timing(self):
        """验证当前项目的时间轴准确性"""
        audio_files = self.get_merged_audio_files()
        if not audio_files:
            MessageBox("提示", "没有找到可用的音频文件", self).exec()
            return
            
        gap_duration = self.current_project.output_settings.get('gap_duration', 0.03)
        timing_data = self.validate_subtitle_timing(audio_files, gap_duration)
        
        if timing_data:
            self.show_subtitle_timing_info(timing_data)
        else:
            MessageBox("错误", "时间轴验证失败", self).exec()
    
    def open_synthesis_settings(self):
        """打开合成设置对话框"""
        dialog = SynthesisSettingsDialog(self.current_project.output_settings, self)
        if dialog.exec() == QDialog.Accepted:
            # 更新项目设置
            self.current_project.output_settings.update(dialog.get_settings())
            
            # 自动保存项目
            if self.current_project.project_name:
                self.auto_save_project()
            
            InfoBar.success(
                title="设置已保存",
                content="合成设置已更新",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
    
    def merge_text_up(self):
        """向上合并文本"""
        selected_rows = self.get_selected_rows()
        if len(selected_rows) != 1:
            MessageBox("提示", "请选择一行文本进行向上合并", self).exec()
            return
            
        current_row = selected_rows[0]
        if current_row == 0:
            MessageBox("提示", "第一行无法向上合并", self).exec()
            return
            
        # 获取当前行和上一行的文本
        current_segment = self.current_project.text_segments[current_row]
        prev_segment = self.current_project.text_segments[current_row - 1]
        
        # 合并文本
        merged_text = prev_segment['text'] + "\n" + current_segment['text']
        
        # 更新上一行的文本
        prev_segment['text'] = merged_text
        prev_segment['duration'] = len(merged_text) * 300  # 重新计算时长
        
        # 删除当前行
        del self.current_project.text_segments[current_row]
        
        # 清理配置
        if current_segment['id'] in self.text_configs:
            del self.text_configs[current_segment['id']]
        
        # 刷新表格
        self.refresh_text_table()
        
        # 自动保存项目
        if self.current_project.project_name:
            self.auto_save_project()
        
        InfoBar.success(
            title="合并成功",
            content="文本已向上合并",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def merge_text_down(self):
        """向下合并文本"""
        selected_rows = self.get_selected_rows()
        if len(selected_rows) != 1:
            MessageBox("提示", "请选择一行文本进行向下合并", self).exec()
            return
            
        current_row = selected_rows[0]
        if current_row >= len(self.current_project.text_segments) - 1:
            MessageBox("提示", "最后一行无法向下合并", self).exec()
            return
            
        # 获取当前行和下一行的文本
        current_segment = self.current_project.text_segments[current_row]
        next_segment = self.current_project.text_segments[current_row + 1]
        
        # 合并文本
        merged_text = current_segment['text'] + "\n" + next_segment['text']
        
        # 更新当前行的文本
        current_segment['text'] = merged_text
        current_segment['duration'] = len(merged_text) * 300  # 重新计算时长
        
        # 删除下一行
        del self.current_project.text_segments[current_row + 1]
        
        # 清理配置
        if next_segment['id'] in self.text_configs:
            del self.text_configs[next_segment['id']]
        
        # 刷新表格
        self.refresh_text_table()
        
        # 自动保存项目
        if self.current_project.project_name:
            self.auto_save_project()
        
        InfoBar.success(
            title="合并成功",
            content="文本已向下合并",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def merge_selected_texts(self):
        """合并选中的多个文本"""
        selected_rows = self.get_selected_rows()
        if len(selected_rows) < 2:
            MessageBox("提示", "请至少选择两行文本进行合并", self).exec()
            return
            
        # 按行号排序
        selected_rows.sort()
        
        # 获取第一个选中的文本作为基础
        base_row = selected_rows[0]
        base_segment = self.current_project.text_segments[base_row]
        merged_text = base_segment['text']
        
        # 收集要删除的行和配置
        rows_to_delete = []
        configs_to_delete = []
        
        # 合并其他选中的文本
        for row in selected_rows[1:]:
            segment = self.current_project.text_segments[row]
            merged_text += "\n" + segment['text']
            rows_to_delete.append(row)
            configs_to_delete.append(segment['id'])
        
        # 更新基础文本
        base_segment['text'] = merged_text
        base_segment['duration'] = len(merged_text) * 300  # 重新计算时长
        
        # 从后往前删除其他行（避免索引变化）
        for row in reversed(rows_to_delete):
            del self.current_project.text_segments[row]
        
        # 清理配置
        for text_id in configs_to_delete:
            if text_id in self.text_configs:
                del self.text_configs[text_id]
        
        # 刷新表格
        self.refresh_text_table()
        
        # 自动保存项目
        if self.current_project.project_name:
            self.auto_save_project()
        
        InfoBar.success(
            title="合并成功",
            content=f"已合并 {len(selected_rows)} 个文本段落",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def get_selected_rows(self):
        """获取选中的行号列表"""
        selected_rows = []
        for row in range(self.text_table.rowCount()):
            checkbox = self.text_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_rows.append(row)
        return selected_rows
    
    def merge_single_text_up(self, row):
        """表格中单个文本向上合并"""
        if row == 0:
            MessageBox("提示", "第一行无法向上合并", self).exec()
            return
            
        # 获取当前行和上一行的文本
        current_segment = self.current_project.text_segments[row]
        prev_segment = self.current_project.text_segments[row - 1]
        
        # 合并文本
        merged_text = prev_segment['text'] + "\n" + current_segment['text']
        
        # 更新上一行的文本
        prev_segment['text'] = merged_text
        prev_segment['duration'] = len(merged_text) * 300  # 重新计算时长
        
        # 删除当前行
        del self.current_project.text_segments[row]
        
        # 清理配置
        if current_segment['id'] in self.text_configs:
            del self.text_configs[current_segment['id']]
        
        # 刷新表格
        self.refresh_text_table()
        
        # 自动保存项目
        if self.current_project.project_name:
            self.auto_save_project()
        
        InfoBar.success(
            title="合并成功",
            content="文本已向上合并",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def merge_single_text_down(self, row):
        """表格中单个文本向下合并"""
        if row >= len(self.current_project.text_segments) - 1:
            MessageBox("提示", "最后一行无法向下合并", self).exec()
            return
            
        # 获取当前行和下一行的文本
        current_segment = self.current_project.text_segments[row]
        next_segment = self.current_project.text_segments[row + 1]
        
        # 合并文本
        merged_text = current_segment['text'] + "\n" + next_segment['text']
        
        # 更新当前行的文本
        current_segment['text'] = merged_text
        current_segment['duration'] = len(merged_text) * 300  # 重新计算时长
        
        # 删除下一行
        del self.current_project.text_segments[row + 1]
        
        # 清理配置
        if next_segment['id'] in self.text_configs:
            del self.text_configs[next_segment['id']]
        
        # 刷新表格
        self.refresh_text_table()
        
        # 自动保存项目
        if self.current_project.project_name:
            self.auto_save_project()
        
        InfoBar.success(
            title="合并成功",
            content="文本已向下合并",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

class SynthesisSettingsDialog(QDialog):
    """合成设置对话框"""
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("合成设置")
        self.setModal(True)
        self.resize(400, 300)
        
        self.current_settings = current_settings.copy()
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("音频合成设置")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976d2; margin: 10px;")
        layout.addWidget(title_label)
        
        # 设置表单
        form_layout = QFormLayout()
        
        # 静音间隔设置
        self.add_silence_checkbox = QCheckBox("添加静音间隔")
        self.add_silence_checkbox.setChecked(current_settings.get('add_silence_gap', True))
        self.add_silence_checkbox.setToolTip("在音频段落之间添加静音间隔，避免顿挫感")
        form_layout.addRow("静音间隔:", self.add_silence_checkbox)
        
        # 间隔时长设置
        self.gap_duration_spin = QDoubleSpinBox()
        self.gap_duration_spin.setRange(0.0, 1.0)
        self.gap_duration_spin.setSingleStep(0.01)
        self.gap_duration_spin.setValue(current_settings.get('gap_duration', 0.03))
        self.gap_duration_spin.setSuffix(" 秒")
        self.gap_duration_spin.setToolTip("静音间隔的时长，建议30ms（0.03秒）")
        form_layout.addRow("间隔时长:", self.gap_duration_spin)
        
        # 连接信号
        self.add_silence_checkbox.toggled.connect(self.on_silence_toggled)
        
        layout.addLayout(form_layout)
        
        # 说明文本
        info_label = QLabel("说明：\n• 30ms的静音间隔可以有效避免顿挫感\n• 如果不需要间隔，请取消勾选'添加静音间隔'\n• 间隔时长建议不超过100ms")
        info_label.setStyleSheet("color: #666666; font-size: 12px; padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        layout.addWidget(info_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = PushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        ok_btn = PushButton("确定")
        ok_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QCheckBox {
                font-size: 12px;
            }
            QDoubleSpinBox {
                font-size: 12px;
                padding: 4px;
            }
        """)
    
    def on_silence_toggled(self, checked):
        """静音间隔开关状态改变"""
        self.gap_duration_spin.setEnabled(checked)
    
    def get_settings(self):
        """获取设置"""
        return {
            'add_silence_gap': self.add_silence_checkbox.isChecked(),
            'gap_duration': self.gap_duration_spin.value()
        }

class TimingInfoDialog(QDialog):
    """时间轴信息对话框"""
    def __init__(self, timing_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("字幕时间轴信息")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("字幕时间轴详细信息")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976d2; margin: 10px;")
        layout.addWidget(title_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 总体信息
        summary_text = f"总时长: {timing_data['total_duration']:.2f}秒\n"
        summary_text += f"间隔时间: {timing_data['gap_duration']}秒\n"
        summary_text += f"音频文件数量: {len(timing_data['timing_info'])}\n\n"
        
        summary_label = QLabel(summary_text)
        summary_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        content_layout.addWidget(summary_label)
        
        # 详细信息
        for info in timing_data['timing_info']:
            info_text = f"第{info['index']}段: {info['audio_file']}\n"
            info_text += f"  时长: {info['duration']:.2f}秒\n"
            info_text += f"  开始: {info['start_time']:.2f}秒\n"
            info_text += f"  结束: {info['end_time']:.2f}秒\n"
            
            info_label = QLabel(info_text)
            info_label.setStyleSheet("font-size: 12px; color: #666666; padding: 8px; margin: 2px; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 3px;")
            content_layout.addWidget(info_label)
        
        # 添加弹性空间
        content_layout.addStretch()
        
        # 设置滚动区域的内容
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 关闭按钮
        close_btn = PushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QScrollArea {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                background-color: #ffffff;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
        """)