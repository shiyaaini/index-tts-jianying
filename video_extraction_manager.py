import os
import sys
import subprocess
import threading
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFileDialog, QProgressBar, QTextEdit,
                           QComboBox, QSpinBox, QCheckBox, QGroupBox, QFormLayout,
                           QMessageBox, QListWidget, QListWidgetItem, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont
from qfluentwidgets import (PushButton, LineEdit, ComboBox, SpinBox, 
                           MessageBox, ProgressBar, TextEdit, CheckBox)

class VideoExtractionThread(QThread):
    """视频提取音频的工作线程"""
    progress_updated = pyqtSignal(str)
    extraction_finished = pyqtSignal(bool, str)
    
    def __init__(self, input_file, output_file, audio_format, quality, start_time=None, duration=None):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.audio_format = audio_format
        self.quality = quality
        self.start_time = start_time
        self.duration = duration
        
    def run(self):
        try:
            # 构建ffmpeg命令
            ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")
            if not os.path.exists(ffmpeg_path):
                ffmpeg_path = "ffmpeg"  # 使用系统PATH中的ffmpeg
            
            cmd = [ffmpeg_path, "-i", self.input_file]
            
            # 添加时间参数
            if self.start_time:
                cmd.extend(["-ss", str(self.start_time)])
            if self.duration:
                cmd.extend(["-t", str(self.duration)])
            
            # 添加音频参数
            if self.audio_format == "mp3":
                cmd.extend(["-acodec", "libmp3lame", "-b:a", f"{self.quality}k"])
            elif self.audio_format == "wav":
                cmd.extend(["-acodec", "pcm_s16le"])
            elif self.audio_format == "aac":
                cmd.extend(["-acodec", "aac", "-b:a", f"{self.quality}k"])
            elif self.audio_format == "flac":
                cmd.extend(["-acodec", "flac"])
            
            cmd.extend(["-y", self.output_file])  # -y 覆盖输出文件
            
            self.progress_updated.emit(f"开始提取音频: {os.path.basename(self.input_file)}")
            self.progress_updated.emit(f"命令: {' '.join(cmd)}")
            
            # 执行ffmpeg命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',  # 替换无法解码的字符
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            # 读取输出
            while True:
                try:
                    output = process.stderr.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        self.progress_updated.emit(output.strip())
                except UnicodeDecodeError as e:
                    # 如果仍然有编码错误，跳过这行输出
                    self.progress_updated.emit(f"⚠️ 编码错误，跳过输出行: {str(e)}")
                    continue
            
            return_code = process.poll()
            
            if return_code == 0:
                self.progress_updated.emit(f"✅ 音频提取完成: {os.path.basename(self.output_file)}")
                self.extraction_finished.emit(True, self.output_file)
            else:
                error_msg = f"❌ 提取失败，返回码: {return_code}"
                self.progress_updated.emit(error_msg)
                self.extraction_finished.emit(False, error_msg)
                
        except Exception as e:
            error_msg = f"❌ 提取过程中出现错误: {str(e)}"
            self.progress_updated.emit(error_msg)
            self.extraction_finished.emit(False, error_msg)

class VideoExtractionManager(QWidget):
    """视频提取音频管理器"""
    
    def __init__(self):
        super().__init__()
        self.extraction_thread = None
        self.init_ui()
        self.setAcceptDrops(True)  # 启用拖拽功能
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("视频提取音频")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #333333; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 左侧控制面板
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)
        
        # 右侧日志面板
        log_panel = self.create_log_panel()
        splitter.addWidget(log_panel)
        
        # 设置分割器比例
        splitter.setSizes([400, 500])
        
    def create_control_panel(self):
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 文件选择组
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)
        
        # 输入文件选择
        input_layout = QHBoxLayout()
        self.input_file_edit = LineEdit()
        self.input_file_edit.setPlaceholderText("选择视频文件或拖拽到此处...")
        self.input_file_edit.setReadOnly(True)
        input_layout.addWidget(QLabel("输入视频:"))
        input_layout.addWidget(self.input_file_edit)
        
        self.browse_btn = PushButton("浏览")
        self.browse_btn.clicked.connect(self.browse_input_file)
        input_layout.addWidget(self.browse_btn)
        file_layout.addLayout(input_layout)
        
        # 输出目录选择
        output_layout = QHBoxLayout()
        self.output_dir_edit = LineEdit()
        downloads_path = str(Path.home() / "Downloads")
        self.output_dir_edit.setText(downloads_path)
        output_layout.addWidget(QLabel("输出目录:"))
        output_layout.addWidget(self.output_dir_edit)
        
        self.browse_output_btn = PushButton("浏览")
        self.browse_output_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(self.browse_output_btn)
        file_layout.addLayout(output_layout)
        
        layout.addWidget(file_group)
        
        # 音频设置组
        audio_group = QGroupBox("音频设置")
        audio_layout = QFormLayout(audio_group)
        
        # 音频格式
        self.format_combo = ComboBox()
        self.format_combo.addItems(["mp3", "wav", "aac", "flac"])
        self.format_combo.setCurrentText("mp3")
        audio_layout.addRow("音频格式:", self.format_combo)
        
        # 音频质量（仅对有损格式有效）
        self.quality_spin = SpinBox()
        self.quality_spin.setRange(64, 320)
        self.quality_spin.setValue(192)
        self.quality_spin.setSuffix(" kbps")
        audio_layout.addRow("音频质量:", self.quality_spin)
        
        layout.addWidget(audio_group)
        
        # 时间设置组
        time_group = QGroupBox("时间设置（可选）")
        time_layout = QFormLayout(time_group)
        
        # 开始时间
        self.start_time_edit = LineEdit()
        self.start_time_edit.setPlaceholderText("例如: 00:01:30 或 90")
        time_layout.addRow("开始时间:", self.start_time_edit)
        
        # 持续时间
        self.duration_edit = LineEdit()
        self.duration_edit.setPlaceholderText("例如: 00:02:00 或 120")
        time_layout.addRow("持续时间:", self.duration_edit)
        
        layout.addWidget(time_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.extract_btn = PushButton("开始提取")
        self.extract_btn.clicked.connect(self.start_extraction)
        self.extract_btn.setStyleSheet("""
            PushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            PushButton:hover {
                background-color: #45a049;
            }
            PushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        self.stop_btn = PushButton("停止")
        self.stop_btn.clicked.connect(self.stop_extraction)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            PushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            PushButton:hover {
                background-color: #da190b;
            }
            PushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        button_layout.addWidget(self.extract_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addStretch()
        return panel
        
    def create_log_panel(self):
        """创建日志面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 日志标题
        log_label = QLabel("提取日志")
        log_font = QFont()
        log_font.setBold(True)
        log_label.setFont(log_font)
        layout.addWidget(log_label)
        
        # 日志文本框
        self.log_text = TextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                border: 1px solid #333333;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.log_text)
        
        # 清除日志按钮
        clear_btn = PushButton("清除日志")
        clear_btn.clicked.connect(self.clear_log)
        layout.addWidget(clear_btn)
        
        return panel
        
    def browse_input_file(self):
        """浏览输入文件"""
        downloads_path = str(Path.home() / "Downloads")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            downloads_path,
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.m4v *.3gp *.webm);;所有文件 (*.*)"
        )
        if file_path:
            self.input_file_edit.setText(file_path)
            
    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self.output_dir_edit.text()
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            
    def start_extraction(self):
        """开始提取音频"""
        input_file = self.input_file_edit.text().strip()
        output_dir = self.output_dir_edit.text().strip()
        
        if not input_file:
            QMessageBox.warning(self, "警告", "请选择输入视频文件！")
            return
            
        if not os.path.exists(input_file):
            QMessageBox.warning(self, "警告", "输入文件不存在！")
            return
            
        if not output_dir:
            QMessageBox.warning(self, "警告", "请选择输出目录！")
            return
            
        # 生成输出文件名
        input_name = os.path.splitext(os.path.basename(input_file))[0]
        audio_format = self.format_combo.currentText()
        output_file = os.path.join(output_dir, f"{input_name}.{audio_format}")
        
        # 获取时间参数
        start_time = self.start_time_edit.text().strip() or None
        duration = self.duration_edit.text().strip() or None
        
        # 创建并启动提取线程
        self.extraction_thread = VideoExtractionThread(
            input_file, output_file, audio_format, 
            self.quality_spin.value(), start_time, duration
        )
        self.extraction_thread.progress_updated.connect(self.update_log)
        self.extraction_thread.extraction_finished.connect(self.on_extraction_finished)
        
        # 更新UI状态
        self.extract_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        self.extraction_thread.start()
        self.update_log("🚀 开始音频提取任务...")
        
    def stop_extraction(self):
        """停止提取"""
        if self.extraction_thread and self.extraction_thread.isRunning():
            self.extraction_thread.terminate()
            self.extraction_thread.wait()
            self.update_log("⏹️ 用户停止了提取任务")
            
        self.extract_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
    def update_log(self, message):
        """更新日志"""
        self.log_text.append(message)
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)
        
    def on_extraction_finished(self, success, result):
        """提取完成回调"""
        self.extract_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if success:
            QMessageBox.information(self, "成功", f"音频提取完成！\n输出文件: {result}")
        else:
            QMessageBox.critical(self, "错误", f"音频提取失败！\n错误信息: {result}")
            
    def clear_log(self):
        """清除日志"""
        self.log_text.clear()
        
    # 拖拽功能实现
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files:
            # 只处理第一个文件
            file_path = files[0]
            if os.path.isfile(file_path):
                # 检查是否为视频文件
                video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.3gp', '.webm']
                if any(file_path.lower().endswith(ext) for ext in video_extensions):
                    self.input_file_edit.setText(file_path)
                    self.update_log(f"📁 通过拖拽添加文件: {os.path.basename(file_path)}")
                else:
                    QMessageBox.warning(self, "警告", "请拖拽视频文件！")
            else:
                QMessageBox.warning(self, "警告", "请拖拽文件而不是文件夹！")