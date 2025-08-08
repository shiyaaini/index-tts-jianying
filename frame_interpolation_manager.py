import os
import sys
import subprocess
import threading
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFileDialog, QProgressBar, QTextEdit,
                           QGroupBox, QFormLayout, QSpinBox, QComboBox,
                           QMessageBox, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont
from qfluentwidgets import (PushButton, LineEdit, SpinBox, ComboBox, 
                           ProgressBar, TextEdit, InfoBar, InfoBarPosition)

class FrameInterpolationWorker(QThread):
    """视频插帧处理工作线程"""
    progress_updated = pyqtSignal(str)  # 进度信息
    finished = pyqtSignal(bool, str)    # 完成信号(成功/失败, 消息)
    
    def __init__(self, input_path, output_path, target_fps=60, crf=18):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.target_fps = target_fps
        self.crf = crf
        self.is_cancelled = False
        
    def run(self):
        try:
            # 检查ffmpeg是否可用
            ffmpeg_path = self.find_ffmpeg()
            if not ffmpeg_path:
                self.finished.emit(False, "未找到FFmpeg，请确保FFmpeg已安装并在PATH中")
                return
                
            # 构建ffmpeg命令
            cmd = [
                ffmpeg_path,
                '-i', self.input_path,
                '-vf', f"minterpolate='fps={self.target_fps}:mi_mode=mci:mc_mode=aobmc:vsbmc=1'",
                '-c:v', 'libx264',
                '-crf', str(self.crf),
                '-y',  # 覆盖输出文件
                self.output_path
            ]
            
            self.progress_updated.emit(f"开始处理: {os.path.basename(self.input_path)}")
            self.progress_updated.emit(f"命令: {' '.join(cmd)}")
            
            # 执行ffmpeg命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8',
                errors='ignore',  # 忽略编码错误
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # 读取输出
            while True:
                if self.is_cancelled:
                    process.terminate()
                    self.finished.emit(False, "处理已取消")
                    return
                    
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.progress_updated.emit(output.strip())
            
            # 检查处理结果
            return_code = process.poll()
            if return_code == 0:
                self.finished.emit(True, f"处理完成: {os.path.basename(self.output_path)}")
            else:
                stderr = process.stderr.read()
                self.finished.emit(False, f"处理失败: {stderr}")
                
        except Exception as e:
            self.finished.emit(False, f"处理出错: {str(e)}")
    
    def find_ffmpeg(self):
        """查找ffmpeg可执行文件"""
        # 首先检查本地ffmpeg目录
        local_ffmpeg = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")
        if os.path.exists(local_ffmpeg):
            return local_ffmpeg
            
        # 检查系统PATH
        try:
            result = subprocess.run(['where', 'ffmpeg'] if sys.platform == 'win32' else ['which', 'ffmpeg'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
            
        return None
    
    def cancel(self):
        """取消处理"""
        self.is_cancelled = True

class FrameInterpolationManager(QWidget):
    """插帧算法补偿管理器"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.setup_drag_drop()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title = QLabel("插帧算法补偿")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 说明文字
        desc = QLabel("将120fps视频通过AI插帧压缩到60fps，保留更多运动信息，防止平台压缩降质")
        desc.setStyleSheet("color: #666; font-size: 14px; margin-bottom: 20px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # 输入文件选择
        input_group = QGroupBox("输入视频")
        input_layout = QVBoxLayout(input_group)
        
        file_layout = QHBoxLayout()
        self.input_path_edit = LineEdit()
        self.input_path_edit.setPlaceholderText("选择输入视频文件或拖拽到此处...")
        self.input_path_edit.setReadOnly(True)
        
        self.browse_btn = PushButton("浏览")
        self.browse_btn.clicked.connect(self.browse_input_file)
        
        file_layout.addWidget(self.input_path_edit)
        file_layout.addWidget(self.browse_btn)
        input_layout.addLayout(file_layout)
        
        layout.addWidget(input_group)
        
        # 输出设置
        output_group = QGroupBox("输出设置")
        output_layout = QFormLayout(output_group)
        
        # 目标帧率
        self.fps_spinbox = SpinBox()
        self.fps_spinbox.setRange(24, 120)
        self.fps_spinbox.setValue(60)
        self.fps_spinbox.setSuffix(" fps")
        output_layout.addRow("目标帧率:", self.fps_spinbox)
        
        # 视频质量
        self.crf_spinbox = SpinBox()
        self.crf_spinbox.setRange(0, 51)
        self.crf_spinbox.setValue(18)
        self.crf_spinbox.setToolTip("CRF值越小质量越高，文件越大 (推荐: 18-23)")
        output_layout.addRow("视频质量 (CRF):", self.crf_spinbox)
        
        # 输出路径
        output_path_layout = QHBoxLayout()
        self.output_path_edit = LineEdit()
        downloads_path = str(Path.home() / "Downloads")
        self.output_path_edit.setText(downloads_path)
        
        self.browse_output_btn = PushButton("浏览")
        self.browse_output_btn.clicked.connect(self.browse_output_folder)
        
        output_path_layout.addWidget(self.output_path_edit)
        output_path_layout.addWidget(self.browse_output_btn)
        output_layout.addRow("输出文件夹:", output_path_layout)
        
        layout.addWidget(output_group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        self.start_btn = PushButton("开始处理")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setEnabled(False)
        
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setEnabled(False)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 日志输出
        log_group = QGroupBox("处理日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = TextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        
    def setup_drag_drop(self):
        """设置拖拽功能"""
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if self.is_video_file(file_path):
                    event.acceptProposedAction()
                    return
        event.ignore()
        
    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if self.is_video_file(file_path):
                self.input_path_edit.setText(file_path)
                self.update_ui_state()
                self.log_text.append(f"已选择输入文件: {os.path.basename(file_path)}")
                
    def is_video_file(self, file_path):
        """检查是否为视频文件"""
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        return Path(file_path).suffix.lower() in video_extensions
        
    def browse_input_file(self):
        """浏览输入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择输入视频文件",
            "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v);;所有文件 (*)"
        )
        if file_path:
            self.input_path_edit.setText(file_path)
            self.update_ui_state()
            self.log_text.append(f"已选择输入文件: {os.path.basename(file_path)}")
            
    def browse_output_folder(self):
        """浏览输出文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择输出文件夹",
            self.output_path_edit.text()
        )
        if folder_path:
            self.output_path_edit.setText(folder_path)
            
    def update_ui_state(self):
        """更新UI状态"""
        has_input = bool(self.input_path_edit.text().strip())
        self.start_btn.setEnabled(has_input and not self.is_processing())
        
    def is_processing(self):
        """检查是否正在处理"""
        return self.worker and self.worker.isRunning()
        
    def start_processing(self):
        """开始处理"""
        input_path = self.input_path_edit.text().strip()
        if not input_path or not os.path.exists(input_path):
            QMessageBox.warning(self, "错误", "请选择有效的输入视频文件")
            return
            
        output_folder = self.output_path_edit.text().strip()
        if not output_folder or not os.path.exists(output_folder):
            QMessageBox.warning(self, "错误", "请选择有效的输出文件夹")
            return
            
        # 生成输出文件名
        input_name = Path(input_path).stem
        output_name = f"{input_name}_ai_{self.fps_spinbox.value()}fps.mp4"
        output_path = os.path.join(output_folder, output_name)
        
        # 创建工作线程
        self.worker = FrameInterpolationWorker(
            input_path, 
            output_path, 
            self.fps_spinbox.value(),
            self.crf_spinbox.value()
        )
        
        # 连接信号
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.finished.connect(self.on_processing_finished)
        
        # 更新UI
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        # 清空日志
        self.log_text.clear()
        self.log_text.append("开始处理...")
        
        # 启动线程
        self.worker.start()
        
    def cancel_processing(self):
        """取消处理"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.log_text.append("正在取消处理...")
            
    def on_progress_updated(self, message):
        """进度更新"""
        self.log_text.append(message)
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)
        
    def on_processing_finished(self, success, message):
        """处理完成"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        self.log_text.append(message)
        
        if success:
            InfoBar.success(
                title="处理完成",
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            InfoBar.error(
                title="处理失败",
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        
        self.worker = None