import json
import os
import uuid
import time
import threading
from datetime import datetime
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("警告: pygame 未安装，音频播放功能将受限。请运行: pip install pygame")
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QCheckBox,
                             QInputDialog, QAbstractItemView, QComboBox, 
                             QSpinBox, QDoubleSpinBox, QLineEdit, QDialog, 
                             QListWidget, QListWidgetItem, QLabel, QScrollArea, 
                             QFrame, QFileDialog, QProgressBar, QTextEdit, 
                             QGroupBox, QFormLayout, QPushButton, QTreeWidget,
                             QTreeWidgetItem, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QUrl
from PyQt5.QtGui import QColor, QFont, QDragEnterEvent, QDropEvent
try:
    from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
    MULTIMEDIA_AVAILABLE = True
except ImportError:
    MULTIMEDIA_AVAILABLE = False
from qfluentwidgets import (CardWidget, StrongBodyLabel, BodyLabel,
                           PushButton, MessageBox, InfoBar, InfoBarPosition,
                           FluentIcon, ComboBox as FluentComboBox)

# 导入 pygame 音频播放器
try:
    from pygame_audio_player import PygameAudioPlayer, get_audio_player
    PYGAME_PLAYER_AVAILABLE = True
except ImportError:
    PYGAME_PLAYER_AVAILABLE = False
    print("警告: pygame_audio_player 模块未找到，将使用系统默认播放器")

class MultiLineTextEdit(QTextEdit):
    """多行文本编辑器，用于表格中的文本编辑"""

    def __init__(self, text="", text_id="", tts_manager=None, parent=None):
        super().__init__(parent)
        self.text_id = text_id
        self.tts_manager = tts_manager
        self._updating = False

        self.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 10px;
                font-size: 16px;
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
                background-color: #ffffff;
                color: #333333;
            }
            QTextEdit:focus {
                border-color: #2196f3;
                background-color: #f8f9fa;
            }
        """)
        self.setPlainText(text)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.textChanged.connect(self.on_text_changed)

        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self.adjust_height)

    def on_text_changed(self):
        """文本改变时发出信号并调整高度"""
        self.adjust_height()
        if not self._updating and self.tts_manager:
            if hasattr(self.tts_manager, 'on_text_content_changed'):
                self.tts_manager.on_text_content_changed(self.text_id, self.toPlainText())

    def adjust_height(self):
        """根据内容自动调整高度"""
        doc_height = self.document().size().height()
        margins = self.contentsMargins()
        ideal_height = doc_height + margins.top() + margins.bottom() + 5 # Add a small buffer

        min_height = 80
        new_height = max(ideal_height, min_height)

        if self.height() != int(new_height):
            self.setFixedHeight(int(new_height))
            if self.tts_manager and hasattr(self.tts_manager, 'text_table'):
                table = self.tts_manager.text_table
                # Find the row for this widget and resize it
                for row in range(table.rowCount()):
                    if table.cellWidget(row, 1) is self:
                        # Set row height to be the editor's height + padding
                        table.setRowHeight(row, int(new_height) + 20)
                        break

    def setPlainText(self, text):
        """重写setPlainText方法，避免在设置初始文本时触发不必要的信号"""
        self._updating = True
        super().setPlainText(text)
        self._updating = False
        self.adjust_height()

    def get_available_width(self):
        """获取可用宽度"""
        if self.tts_manager and hasattr(self.tts_manager, 'text_table'):
            table = self.tts_manager.text_table
            return table.columnWidth(1) - 20  # 减去边距
        return 300  # 默认宽度
        
    def get_text(self):
        """获取文本内容"""
        return self.toPlainText()
        
    def set_text(self, text):
        """设置文本内容"""
        self.setPlainText(text)
        
    def resizeEvent(self, event):
        """重写resize事件，确保内容适应新大小"""
        super().resizeEvent(event)
        # 当组件被外部调整大小时，重新计算文档布局
        if hasattr(self, 'document'):
            self.document().setTextWidth(self.viewport().width())
            
    def showEvent(self, event):
        """重写show事件，确保显示时大小正确"""
        super().showEvent(event)
        # 延迟调整大小，确保组件完全显示
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(50, self.adjust_height)

class ParameterSpinBox(QDoubleSpinBox):
    """自定义参数输入框"""
    def __init__(self, min_val, max_val, default_val, step=0.1, decimals=2):
        super().__init__()
        self.setRange(min_val, max_val)
        self.setValue(default_val)
        self.setSingleStep(step)
        self.setDecimals(decimals)
        self.setFixedSize(70, 30)  # 设置固定大小，防止被行高拉伸
        self.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 2px;
                font-size: 12px;
                max-height: 30px;
                min-height: 30px;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #1976d2;
            }
        """)

class ParameterIntSpinBox(QSpinBox):
    """自定义整数参数输入框"""
    def __init__(self, min_val, max_val, default_val):
        super().__init__()
        self.setRange(min_val, max_val)
        self.setValue(default_val)
        self.setFixedSize(60, 30)  # 设置固定大小，防止被行高拉伸
        self.setStyleSheet("""
            QSpinBox {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 2px;
                font-size: 12px;
                max-height: 30px;
                min-height: 30px;
            }
            QSpinBox:focus {
                border: 2px solid #1976d2;
            }
        """)

class ParameterCheckBox(QCheckBox):
    """自定义参数复选框"""
    def __init__(self, default_val=True):
        super().__init__()
        self.setChecked(default_val)
        self.setFixedSize(60, 30)  # 设置固定大小，防止被行高拉伸
        self.setStyleSheet("""
            QCheckBox {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 2px;
                font-size: 12px;
                max-height: 30px;
                min-height: 30px;
            }
            QCheckBox:focus {
                border: 2px solid #1976d2;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #d0d0d0;
                background-color: #ffffff;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #1976d2;
                background-color: #1976d2;
                border-radius: 2px;
            }
        """)

class AudioPreviewWidget(QWidget):
    """音频预览组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_audio_path = None
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(25, 25)
        self.play_btn.clicked.connect(self.toggle_play)
        
        self.audio_label = QLabel("未选择")
        self.audio_label.setStyleSheet("color: #666666; font-size: 11px;")
        
        layout.addWidget(self.play_btn)
        layout.addWidget(self.audio_label)
        
    def set_audio_path(self, audio_path):
        """设置音频路径"""
        self.current_audio_path = audio_path
        if audio_path and os.path.exists(audio_path):
            self.audio_label.setText(os.path.basename(audio_path)[:15] + "...")
        else:
            self.audio_label.setText("未选择")
            
    def toggle_play(self):
        """使用 pygame 播放器切换播放状态"""
        if self.current_audio_path and os.path.exists(self.current_audio_path):
            try:
                # 尝试使用 pygame 播放器
                if PYGAME_PLAYER_AVAILABLE:
                    from pygame_audio_player import get_audio_player
                    player = get_audio_player()
                    success = player.play_audio(self.current_audio_path)
                    if not success:
                        # 如果 pygame 播放失败，回退到系统默认播放器
                        self._play_with_system_player()
                else:
                    # 使用系统默认播放器
                    self._play_with_system_player()
            except Exception as e:
                print(f"无法播放音频: {e}")
                
    def _play_with_system_player(self):
        """使用系统默认播放器播放音频"""
        try:
            import subprocess
            import platform
            system = platform.system()
            if system == "Windows":
                os.startfile(self.current_audio_path)
            elif system == "Darwin":
                subprocess.run(["open", self.current_audio_path])
            else:
                subprocess.run(["xdg-open", self.current_audio_path])
        except Exception as e:
            print(f"系统播放器播放失败: {e}")

class AudioTreeDialog(QDialog):
    """音频文件树选择对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_audio_path = None
        self.init_ui()
        self.setup_styles()
        self.load_audio_tree()
        
    def init_ui(self):
        self.setWindowTitle("选择参考音频")
        self.setFixedSize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题和搜索
        header_layout = QHBoxLayout()
        
        title_label = QLabel("选择参考音频文件")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2;")
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索音频文件...")
        self.search_edit.textChanged.connect(self.filter_audio_tree)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(QLabel("搜索:"))
        header_layout.addWidget(self.search_edit)
        
        layout.addLayout(header_layout)
        
        # 主要内容区域
        content_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧音频树
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        tree_label = QLabel("音频文件列表:")
        tree_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        left_layout.addWidget(tree_label)
        
        self.audio_tree = QTreeWidget()
        self.audio_tree.setHeaderLabels(["文件名", "大小", "路径"])
        self.audio_tree.itemClicked.connect(self.on_audio_selected)
        self.audio_tree.itemDoubleClicked.connect(self.on_audio_double_clicked)
        left_layout.addWidget(self.audio_tree)
        
        # 右侧预览区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        preview_label = QLabel("音频预览:")
        preview_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        right_layout.addWidget(preview_label)
        
        # 音频信息
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(150)
        self.info_text.setReadOnly(True)
        right_layout.addWidget(self.info_text)
        
        # 音频预览控件
        self.audio_preview = AudioPreviewWidget()
        right_layout.addWidget(self.audio_preview)
        
        # 浏览其他位置按钮
        browse_btn = PushButton("浏览其他位置...")
        browse_btn.clicked.connect(self.browse_other_location)
        right_layout.addWidget(browse_btn)
        
        right_layout.addStretch()
        
        content_splitter.addWidget(left_widget)
        content_splitter.addWidget(right_widget)
        content_splitter.setSizes([500, 300])
        
        layout.addWidget(content_splitter)
        
        # 拖拽提示
        drag_label = QLabel("💡 提示: 您也可以直接将音频文件拖拽到此窗口")
        drag_label.setStyleSheet("color: #666666; font-size: 12px; padding: 10px; background-color: #f0f0f0; border-radius: 4px;")
        layout.addWidget(drag_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = PushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setEnabled(False)
        self.ok_button.setFixedSize(80, 35)
        
        self.cancel_button = PushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setFixedSize(80, 35)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # 启用拖拽
        self.setAcceptDrops(True)
        
    def setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QTreeWidget {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-size: 14px;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTreeWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QTreeWidget::item:hover {
                background-color: #f5f5f5;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }
            QTextEdit {
                background-color: #f8f9fa;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
        """)
        
    def load_audio_tree(self):
        """加载音频文件树"""
        self.audio_tree.clear()
        
        files_dir = "files"
        if not os.path.exists(files_dir):
            return
            
        # 扫描音频文件
        audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg'}
        
        for root, dirs, files in os.walk(files_dir):
            # 创建目录节点
            if root == files_dir:
                parent_item = self.audio_tree.invisibleRootItem()
            else:
                rel_path = os.path.relpath(root, files_dir)
                parent_item = self.find_or_create_folder_item(rel_path)
            
            # 添加音频文件
            for file in files:
                if any(file.lower().endswith(ext) for ext in audio_extensions):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    size_str = self.format_file_size(file_size)
                    
                    item = QTreeWidgetItem(parent_item)
                    item.setText(0, file)
                    item.setText(1, size_str)
                    item.setData(0, Qt.UserRole, file_path)
                    
        # 展开所有节点
        self.audio_tree.expandAll()
        
    def find_or_create_folder_item(self, rel_path):
        """查找或创建文件夹节点"""
        parts = rel_path.split(os.sep)
        current_item = self.audio_tree.invisibleRootItem()
        
        for part in parts:
            # 查找是否已存在
            found = False
            for i in range(current_item.childCount()):
                child = current_item.child(i)
                if child.text(0) == f"📁 {part}":
                    current_item = child
                    found = True
                    break
            
            if not found:
                # 创建新的文件夹节点
                folder_item = QTreeWidgetItem(current_item)
                folder_item.setText(0, f"📁 {part}")
                folder_item.setText(1, "")
                current_item = folder_item
                
        return current_item
        
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        
    def filter_audio_tree(self, text):
        """过滤音频树"""
        def hide_item(item, hide):
            item.setHidden(hide)
            for i in range(item.childCount()):
                hide_item(item.child(i), hide)
        
        if not text:
            # 显示所有项目
            for i in range(self.audio_tree.topLevelItemCount()):
                hide_item(self.audio_tree.topLevelItem(i), False)
        else:
            # 过滤项目
            text = text.lower()
            for i in range(self.audio_tree.topLevelItemCount()):
                item = self.audio_tree.topLevelItem(i)
                self.filter_item(item, text)
                
    def filter_item(self, item, text):
        """递归过滤项目"""
        # 检查当前项目是否匹配
        matches = text in item.text(0).lower() or text in item.text(2).lower()
        
        # 检查子项目
        has_visible_child = False
        for i in range(item.childCount()):
            child = item.child(i)
            child_visible = self.filter_item(child, text)
            if child_visible:
                has_visible_child = True
        
        # 如果当前项目匹配或有可见子项目，则显示
        visible = matches or has_visible_child
        item.setHidden(not visible)
        return visible
        
    def on_audio_selected(self, item, column):
        """音频选择事件"""
        audio_path = item.data(0, Qt.UserRole)
        if audio_path and os.path.exists(audio_path):
            self.selected_audio_path = audio_path
            self.ok_button.setEnabled(True)
            
            # 更新预览
            self.audio_preview.set_audio_path(audio_path)
            
            # 更新信息
            file_info = self.get_audio_info(audio_path)
            self.info_text.setText(file_info)
        else:
            self.selected_audio_path = None
            self.ok_button.setEnabled(False)
            self.info_text.clear()
            
    def on_audio_double_clicked(self, item, column):
        """双击选择音频"""
        if self.selected_audio_path:
            self.accept()
            
    def get_audio_info(self, audio_path):
        """获取音频文件信息"""
        try:
            file_size = os.path.getsize(audio_path)
            size_str = self.format_file_size(file_size)
            
            # 获取文件修改时间
            mtime = os.path.getmtime(audio_path)
            mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            info = f"""文件路径: {audio_path}
文件大小: {size_str}
修改时间: {mtime_str}
文件格式: {os.path.splitext(audio_path)[1].upper()}

💡 点击播放按钮可以预览音频"""
            
            return info
        except Exception as e:
            return f"无法获取文件信息: {str(e)}"
            
    def browse_other_location(self):
        """浏览其他位置的音频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择参考音频文件",
            "",
            "音频文件 (*.mp3 *.wav *.flac *.m4a *.aac *.ogg);;所有文件 (*)"
        )
        
        if file_path:
            self.selected_audio_path = file_path
            self.ok_button.setEnabled(True)
            
            # 更新预览
            self.audio_preview.set_audio_path(file_path)
            
            # 更新信息
            file_info = self.get_audio_info(file_path)
            self.info_text.setText(file_info)
            
            InfoBar.success(
                title="音频文件已选择",
                content=f"已选择: {os.path.basename(file_path)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        """拖拽放置事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path and os.path.exists(file_path):
                # 检查是否为音频文件
                audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg'}
                if any(file_path.lower().endswith(ext) for ext in audio_extensions):
                    self.selected_audio_path = file_path
                    self.ok_button.setEnabled(True)
                    
                    # 更新预览
                    self.audio_preview.set_audio_path(file_path)
                    
                    # 更新信息
                    file_info = self.get_audio_info(file_path)
                    self.info_text.setText(file_info)
                    
                    InfoBar.success(
                        title="音频文件已添加",
                        content=f"已选择: {os.path.basename(file_path)}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                else:
                    MessageBox("错误", "请拖拽音频文件 (mp3, wav, flac, m4a, aac, ogg)", self).exec()
            
    def get_selected_audio_path(self):
        """获取选中的音频路径"""
        return self.selected_audio_path

class TTSWorker(QThread):
    """TTS转换工作线程"""
    progress_updated = pyqtSignal(int, str)  # 进度, 状态信息
    conversion_finished = pyqtSignal(str, str, bool)  # text_id, output_path, success
    error_occurred = pyqtSignal(str, str)  # text_id, error_message
    
    def __init__(self, text_items, draft_file_path=None, draft_data=None):
        super().__init__()
        self.text_items = text_items
        self.draft_file_path = draft_file_path
        self.draft_data = draft_data
        self.is_cancelled = False
        
    def run(self):
        """执行TTS转换"""
        try:
            # 在开始转换前，强制释放pygame播放器以避免文件占用
            try:
                if PYGAME_PLAYER_AVAILABLE:
                    from pygame_audio_player import get_audio_player
                    player = get_audio_player()
                    player.force_release_player()
                    print("已强制释放pygame音频播放器以避免文件占用")
            except Exception as e:
                print(f"释放音频播放器失败: {e}")
            
            # 导入TTS模块
            try:
                from indextts.infer import IndexTTS
            except ImportError as e:
                self.progress_updated.emit(0, f"TTS模块导入失败: {str(e)}")
                return
            
            # 初始化TTS模型
            self.progress_updated.emit(0, "正在初始化TTS模型...")
            tts = IndexTTS(
                model_dir="checkpoints",
                cfg_path="checkpoints/config.yaml"
            )
            
            total_items = len(self.text_items)
            
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
                    
                    # 生成输出路径 - 放到draft文件同目录的textReading文件夹
                    if self.draft_file_path:
                        draft_dir = os.path.dirname(self.draft_file_path)
                    else:
                        draft_dir = os.path.dirname(os.path.abspath("draft_content.json"))
                    
                    textreading_dir = os.path.join(draft_dir, "textReading")
                    os.makedirs(textreading_dir, exist_ok=True)
                    
                    # 检查是否已存在该文本的音频文件
                    existing_filename = self.get_existing_audio_filename(text_id)
                    
                    if existing_filename:
                        # 使用现有文件名进行替换
                        output_path = os.path.join(textreading_dir, existing_filename)
                        self.progress_updated.emit(progress, f"替换现有音频: {existing_filename}")
                        
                        # 如果文件正在被占用，等待一下再尝试
                        if os.path.exists(output_path):
                            try:
                                # 尝试删除现有文件
                                os.remove(output_path)
                            except PermissionError:
                                # 如果文件被占用，等待一下再重试
                                import time
                                time.sleep(1)
                                try:
                                    os.remove(output_path)
                                except PermissionError:
                                    # 如果还是被占用，使用新的文件名
                                    audio_uuid = str(uuid.uuid4())
                                    output_path = os.path.join(textreading_dir, f"{audio_uuid}_000.wav")
                                    counter = 0
                                    while os.path.exists(output_path):
                                        counter += 1
                                        output_path = os.path.join(textreading_dir, f"{audio_uuid}_{counter:03d}.wav")
                    else:
                        # 生成新的音频文件名
                        audio_uuid = str(uuid.uuid4())
                        output_path = os.path.join(textreading_dir, f"{audio_uuid}_000.wav")
                        
                        # 确保文件名唯一
                        counter = 0
                        while os.path.exists(output_path):
                            counter += 1
                            output_path = os.path.join(textreading_dir, f"{audio_uuid}_{counter:03d}.wav")
                    
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
                            sentences_bucket_size=sentences_bucket_size,
                            **kwargs
                        )
                    
                    # 转换成功
                    self.conversion_finished.emit(text_id, output_path, True)
                    
                except Exception as e:
                    # 转换失败
                    error_msg = f"转换失败: {str(e)}"
                    self.error_occurred.emit(text_id, error_msg)
                    self.conversion_finished.emit(text_id, "", False)
            
            # 完成
            if not self.is_cancelled:
                self.progress_updated.emit(100, "转换完成!")
                
        except Exception as e:
            self.progress_updated.emit(0, f"初始化失败: {str(e)}")
            
    def get_existing_audio_filename(self, text_id):
        """获取现有音频文件名"""
        if not self.draft_data:
            return None
            
        try:
            # 查找该文本ID对应的音频
            audios = self.draft_data.get("materials", {}).get("audios", [])
            for audio in audios:
                if audio.get("text_id") == text_id:
                    audio_path = audio.get("path", "")
                    if audio_path:
                        # 提取文件名
                        # 处理占位符路径格式：##_draftpath_placeholder_UUID##/textReading/filename.wav
                        if "textReading/" in audio_path:
                            filename = audio_path.split("textReading/")[-1]
                            return filename
                        else:
                            # 处理普通路径
                            return os.path.basename(audio_path)
            return None
        except Exception as e:
            print(f"获取现有音频文件名失败: {e}")
            return None
    
    def generate_safe_filename(self, text, max_length=50):
        """生成安全的文件名"""
        import re
        safe_text = re.sub(r'[<>:"/\\|?*]', '', text)
        safe_text = safe_text.replace('\n', ' ').replace('\r', ' ')
        safe_text = re.sub(r'\s+', '_', safe_text.strip())
        
        if len(safe_text) > max_length:
            safe_text = safe_text[:max_length]
            
        if not safe_text:
            safe_text = f"audio_{int(time.time())}"
            
        return safe_text
        
    def cancel(self):
        """取消转换"""
        self.is_cancelled = True

class BatchParameterDialog(QDialog):
    """批量参数设置对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_audio_path = None
        self.init_ui()
        self.setup_styles()
        
    def init_ui(self):
        self.setWindowTitle("批量参数设置")
        self.setFixedSize(600, 700)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("批量设置TTS参数")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)
        
        # 参考音频设置
        audio_group = QGroupBox("参考音频设置")
        audio_layout = QVBoxLayout(audio_group)
        
        self.audio_checkbox = QCheckBox("批量设置参考音频")
        self.audio_checkbox.toggled.connect(self.on_audio_checkbox_toggled)
        audio_layout.addWidget(self.audio_checkbox)
        
        audio_select_layout = QHBoxLayout()
        self.audio_preview = AudioPreviewWidget()
        self.audio_preview.setEnabled(False)
        
        self.select_audio_btn = PushButton("选择音频")
        self.select_audio_btn.clicked.connect(self.select_reference_audio)
        self.select_audio_btn.setEnabled(False)
        
        audio_select_layout.addWidget(self.audio_preview)
        audio_select_layout.addWidget(self.select_audio_btn)
        audio_select_layout.addStretch()
        
        audio_layout.addLayout(audio_select_layout)
        scroll_layout.addWidget(audio_group)
        
        # 推理模式设置
        mode_group = QGroupBox("推理模式设置")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_checkbox = QCheckBox("批量设置推理模式")
        self.mode_checkbox.toggled.connect(self.on_mode_checkbox_toggled)
        mode_layout.addWidget(self.mode_checkbox)
        
        self.mode_combo = FluentComboBox()
        self.mode_combo.addItems(["普通推理", "批次推理"])
        self.mode_combo.setEnabled(False)
        mode_layout.addWidget(self.mode_combo)
        
        scroll_layout.addWidget(mode_group)
        
        # TTS参数设置
        params_group = QGroupBox("TTS参数设置")
        params_layout = QFormLayout(params_group)
        
        # Do Sample
        self.do_sample_checkbox = QCheckBox("批量设置Do Sample")
        self.do_sample_value = ParameterCheckBox(True)
        self.do_sample_value.setEnabled(False)
        self.do_sample_checkbox.toggled.connect(lambda checked: self.do_sample_value.setEnabled(checked))
        do_sample_layout = QHBoxLayout()
        do_sample_layout.addWidget(self.do_sample_checkbox)
        do_sample_layout.addWidget(self.do_sample_value)
        do_sample_layout.addStretch()
        params_layout.addRow(do_sample_layout)
        
        # Temperature
        self.temperature_checkbox = QCheckBox("批量设置Temperature")
        self.temperature_value = ParameterSpinBox(0.1, 2.0, 1.0, 0.1, 2)
        self.temperature_value.setEnabled(False)
        self.temperature_checkbox.toggled.connect(lambda checked: self.temperature_value.setEnabled(checked))
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temperature_checkbox)
        temp_layout.addWidget(self.temperature_value)
        temp_layout.addStretch()
        params_layout.addRow(temp_layout)
        
        # Top P
        self.top_p_checkbox = QCheckBox("批量设置Top P")
        self.top_p_value = ParameterSpinBox(0.0, 1.0, 0.8, 0.01, 3)
        self.top_p_value.setEnabled(False)
        self.top_p_checkbox.toggled.connect(lambda checked: self.top_p_value.setEnabled(checked))
        top_p_layout = QHBoxLayout()
        top_p_layout.addWidget(self.top_p_checkbox)
        top_p_layout.addWidget(self.top_p_value)
        top_p_layout.addStretch()
        params_layout.addRow(top_p_layout)
        
        # Top K
        self.top_k_checkbox = QCheckBox("批量设置Top K")
        self.top_k_value = ParameterIntSpinBox(0, 100, 30)
        self.top_k_value.setEnabled(False)
        self.top_k_checkbox.toggled.connect(lambda checked: self.top_k_value.setEnabled(checked))
        top_k_layout = QHBoxLayout()
        top_k_layout.addWidget(self.top_k_checkbox)
        top_k_layout.addWidget(self.top_k_value)
        top_k_layout.addStretch()
        params_layout.addRow(top_k_layout)
        
        # Num Beams
        self.num_beams_checkbox = QCheckBox("批量设置Num Beams")
        self.num_beams_value = ParameterIntSpinBox(1, 10, 3)
        self.num_beams_value.setEnabled(False)
        self.num_beams_checkbox.toggled.connect(lambda checked: self.num_beams_value.setEnabled(checked))
        beams_layout = QHBoxLayout()
        beams_layout.addWidget(self.num_beams_checkbox)
        beams_layout.addWidget(self.num_beams_value)
        beams_layout.addStretch()
        params_layout.addRow(beams_layout)
        
        # Repetition Penalty
        self.rep_penalty_checkbox = QCheckBox("批量设置Repetition Penalty")
        self.rep_penalty_value = ParameterSpinBox(0.1, 20.0, 10.0, 0.1, 1)
        self.rep_penalty_value.setEnabled(False)
        self.rep_penalty_checkbox.toggled.connect(lambda checked: self.rep_penalty_value.setEnabled(checked))
        rep_penalty_layout = QHBoxLayout()
        rep_penalty_layout.addWidget(self.rep_penalty_checkbox)
        rep_penalty_layout.addWidget(self.rep_penalty_value)
        rep_penalty_layout.addStretch()
        params_layout.addRow(rep_penalty_layout)
        
        # Length Penalty
        self.length_penalty_checkbox = QCheckBox("批量设置Length Penalty")
        self.length_penalty_value = ParameterSpinBox(-2.0, 2.0, 1, 0.1, 1)
        self.length_penalty_value.setEnabled(False)
        self.length_penalty_checkbox.toggled.connect(lambda checked: self.length_penalty_value.setEnabled(checked))
        length_penalty_layout = QHBoxLayout()
        length_penalty_layout.addWidget(self.length_penalty_checkbox)
        length_penalty_layout.addWidget(self.length_penalty_value)
        length_penalty_layout.addStretch()
        params_layout.addRow(length_penalty_layout)
        
        # Max Mel Tokens
        self.max_mel_checkbox = QCheckBox("批量设置Max Mel Tokens")
        self.max_mel_value = ParameterIntSpinBox(50, 1000, 900)
        self.max_mel_value.setEnabled(False)
        self.max_mel_checkbox.toggled.connect(lambda checked: self.max_mel_value.setEnabled(checked))
        max_mel_layout = QHBoxLayout()
        max_mel_layout.addWidget(self.max_mel_checkbox)
        max_mel_layout.addWidget(self.max_mel_value)
        max_mel_layout.addStretch()
        params_layout.addRow(max_mel_layout)
        
        # Max Text Tokens
        self.max_text_checkbox = QCheckBox("批量设置Max Text Tokens")
        self.max_text_value = ParameterIntSpinBox(20, 300, 120)
        self.max_text_value.setEnabled(False)
        self.max_text_checkbox.toggled.connect(lambda checked: self.max_text_value.setEnabled(checked))
        max_text_layout = QHBoxLayout()
        max_text_layout.addWidget(self.max_text_checkbox)
        max_text_layout.addWidget(self.max_text_value)
        max_text_layout.addStretch()
        params_layout.addRow(max_text_layout)
        
        # Bucket Size
        self.bucket_size_checkbox = QCheckBox("批量设置Bucket Size")
        self.bucket_size_value = ParameterIntSpinBox(1, 16, 4)
        self.bucket_size_value.setEnabled(False)
        self.bucket_size_checkbox.toggled.connect(lambda checked: self.bucket_size_value.setEnabled(checked))
        bucket_size_layout = QHBoxLayout()
        bucket_size_layout.addWidget(self.bucket_size_checkbox)
        bucket_size_layout.addWidget(self.bucket_size_value)
        bucket_size_layout.addStretch()
        params_layout.addRow(bucket_size_layout)
        
        scroll_layout.addWidget(params_group)
        
        # 设置滚动区域
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(scroll_area)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = PushButton("应用设置")
        self.apply_btn.clicked.connect(self.accept)
        self.apply_btn.setFixedSize(100, 35)
        
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setFixedSize(80, 35)
        
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
    def setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            BatchParameterDialog {
                background-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0d0d0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #1976d2;
            }
            QCheckBox {
                font-size: 13px;
                color: #333333;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #d0d0d0;
                background-color: #ffffff;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #1976d2;
                background-color: #1976d2;
                border-radius: 2px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
    def on_audio_checkbox_toggled(self, checked):
        """音频复选框切换事件"""
        self.audio_preview.setEnabled(checked)
        self.select_audio_btn.setEnabled(checked)
        
    def on_mode_checkbox_toggled(self, checked):
        """模式复选框切换事件"""
        self.mode_combo.setEnabled(checked)
        
    def select_reference_audio(self):
        """选择参考音频"""
        dialog = AudioTreeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            audio_path = dialog.get_selected_audio_path()
            if audio_path:
                self.selected_audio_path = audio_path
                self.audio_preview.set_audio_path(audio_path)
                
    def get_batch_settings(self):
        """获取批量设置参数"""
        settings = {}
        
        # 参考音频
        if self.audio_checkbox.isChecked() and self.selected_audio_path:
            settings['reference_voice'] = self.selected_audio_path
            
        # 推理模式
        if self.mode_checkbox.isChecked():
            settings['infer_mode'] = self.mode_combo.currentText()
            
        # TTS参数
        tts_params = {}
        
        if self.do_sample_checkbox.isChecked():
            tts_params['do_sample'] = self.do_sample_value.isChecked()
            
        if self.temperature_checkbox.isChecked():
            tts_params['temperature'] = self.temperature_value.value()
            
        if self.top_p_checkbox.isChecked():
            tts_params['top_p'] = self.top_p_value.value()
            
        if self.top_k_checkbox.isChecked():
            tts_params['top_k'] = self.top_k_value.value()
            
        if self.num_beams_checkbox.isChecked():
            tts_params['num_beams'] = self.num_beams_value.value()
            
        if self.rep_penalty_checkbox.isChecked():
            tts_params['repetition_penalty'] = self.rep_penalty_value.value()
            
        if self.length_penalty_checkbox.isChecked():
            tts_params['length_penalty'] = self.length_penalty_value.value()
            
        if self.max_mel_checkbox.isChecked():
            tts_params['max_mel_tokens'] = self.max_mel_value.value()
            
        if self.max_text_checkbox.isChecked():
            tts_params['max_text_tokens_per_sentence'] = self.max_text_value.value()
            
        if self.bucket_size_checkbox.isChecked():
            tts_params['sentences_bucket_max_size'] = self.bucket_size_value.value()
            
        if tts_params:
            settings['tts_params'] = tts_params
            
        return settings

class TTSManager(QWidget):
    """文本转语音管理器 - 支持表格内高级参数配置"""
    def __init__(self):
        super().__init__()
        self.draft_data = None
        self.draft_file_path = None
        self.tts_worker = None
        self.text_configs = {}  # 存储每个文本的配置
        
        # 初始化音频播放器
        if PYGAME_PLAYER_AVAILABLE:
            self.audio_player = get_audio_player()
            # 连接音频播放器信号
            self.audio_player.playback_started.connect(self.on_audio_playback_started)
            self.audio_player.playback_finished.connect(self.on_audio_playback_finished)
            self.audio_player.playback_error.connect(self.on_audio_playback_error)
            self.audio_player.batch_playback_finished.connect(self.on_batch_playback_finished)
        else:
            self.audio_player = None
            
        self.init_ui()
        self.setup_styles()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 标题
        layout.addWidget(StrongBodyLabel("文本转语音 - 高级参数表格配置"))
        
        # 操作按钮区域
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = PushButton(FluentIcon.SYNC, "刷新文本")
        self.refresh_btn.clicked.connect(self.refresh_text_list)
        
        self.select_all_btn = PushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all_texts)
        
        self.select_none_btn = PushButton("取消全选")
        self.select_none_btn.clicked.connect(self.select_none_texts)
        
        self.convert_btn = PushButton(FluentIcon.PLAY, "开始转换")
        self.convert_btn.clicked.connect(self.start_conversion)
        
        self.stop_btn = PushButton(FluentIcon.PAUSE, "停止转换")
        self.stop_btn.clicked.connect(self.stop_conversion)
        self.stop_btn.setEnabled(False)
        
        self.batch_settings_btn = PushButton(FluentIcon.SETTING, "批量设置参数")
        self.batch_settings_btn.clicked.connect(self.open_batch_settings)
        
        self.save_btn = PushButton(FluentIcon.SAVE, "保存工程")
        self.save_btn.clicked.connect(self.save_draft_file)
        
        self.auto_resize_btn = PushButton(FluentIcon.ZOOM_IN, "自动调整行高")
        self.auto_resize_btn.clicked.connect(self.auto_resize_all_rows)
        self.auto_resize_btn.setToolTip("根据文本内容自动调整所有行的高度")
        
        self.play_all_btn = PushButton(FluentIcon.PLAY, "播放所有音频")
        self.play_all_btn.clicked.connect(self.play_all_audio)
        self.play_all_btn.setToolTip("播放所有已转换的音频文件")
        
        self.stop_playback_btn = PushButton(FluentIcon.PAUSE, "停止播放")
        self.stop_playback_btn.clicked.connect(self.stop_audio_playback)
        self.stop_playback_btn.setToolTip("停止当前音频播放")
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.select_all_btn)
        btn_layout.addWidget(self.select_none_btn)
        btn_layout.addWidget(self.batch_settings_btn)
        btn_layout.addWidget(self.convert_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.auto_resize_btn)
        btn_layout.addWidget(self.play_all_btn)
        btn_layout.addWidget(self.stop_playback_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666666; font-size: 14px;")
        layout.addWidget(self.status_label)
        
        # 文本列表表格 - 包含高级参数列
        self.text_table = QTableWidget()
        self.text_table.setColumnCount(16)
        self.text_table.setHorizontalHeaderLabels([
            "选择", "文本内容", "参考音频", "推理模式", "Do Sample", "Temperature", "Top P", "Top K", 
            "Num Beams", "Rep Penalty", "Length Penalty", "Max Mel Tokens", "Max Text Tokens", "Bucket Size", "转换状态", "音频路径"
        ])
        
        # 设置表格属性
        self.text_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.text_table.setAlternatingRowColors(True)
        
        # 设置表头可手动调整大小
        header = self.text_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # 允许手动调整所有列
        header.setStretchLastSection(True)  # 最后一列自动拉伸填充剩余空间
        
        # 确保表格能够自动调整以适应内容变化
        self.text_table.setWordWrap(True)
        self.text_table.setTextElideMode(Qt.ElideNone)  # 不省略文本，完整显示
        
        # 设置默认列宽 - 用户可以手动调整
        self.text_table.setColumnWidth(0, 50)   # 选择列
        self.text_table.setColumnWidth(1, 400)  # 文本内容列 - 增加初始宽度以支持自适应
        self.text_table.setColumnWidth(2, 150)  # 参考音频列
        self.text_table.setColumnWidth(3, 100)  # 推理模式列
        self.text_table.setColumnWidth(4, 80)   # Do Sample列
        self.text_table.setColumnWidth(5, 90)   # Temperature列
        self.text_table.setColumnWidth(6, 80)   # Top P列
        self.text_table.setColumnWidth(7, 70)   # Top K列
        self.text_table.setColumnWidth(8, 90)   # Num Beams列
        self.text_table.setColumnWidth(9, 100)  # Rep Penalty列
        self.text_table.setColumnWidth(10, 100) # Length Penalty列
        self.text_table.setColumnWidth(11, 120) # Max Mel Tokens列
        self.text_table.setColumnWidth(12, 120) # Max Text Tokens列
        self.text_table.setColumnWidth(13, 100) # Bucket Size列
        self.text_table.setColumnWidth(14, 100) # 转换状态列
        # 音频路径列会自动拉伸填充剩余空间
        
        # 设置最小列宽，防止列被调整得太小
        header.setMinimumSectionSize(40)
        
        # 设置行高 - 增加高度以适应更大字体和自适应内容
        self.text_table.verticalHeader().setDefaultSectionSize(120)  # 增加默认行高
        self.text_table.verticalHeader().setMinimumSectionSize(90)   # 增加最小行高
        self.text_table.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)  # 允许手动调整行高
        
        # 启用文本换行和自动调整行高
        self.text_table.setWordWrap(True)
        self.text_table.resizeRowsToContents()
        
        # 允许编辑文本内容列
        self.text_table.setEditTriggers(QAbstractItemView.DoubleClicked)
        
        # 连接单元格点击事件和编辑事件
        self.text_table.cellClicked.connect(self.on_cell_clicked)
        self.text_table.itemChanged.connect(self.on_item_changed)
        
        # 监听列宽变化事件
        header.sectionResized.connect(self.on_column_resized)
        
        layout.addWidget(self.text_table)
        
        # 可折叠的日志区域
        self.create_collapsible_log_area(layout)
        
    def on_column_resized(self, logical_index, old_size, new_size):
        """处理列宽变化事件"""
        # 只处理第1列（文本内容列）的宽度变化
        if logical_index == 1:
            # 通知所有文本编辑器调整大小，但不强制调整行高
            for row in range(self.text_table.rowCount()):
                text_edit = self.text_table.cellWidget(row, 1)
                if text_edit and hasattr(text_edit, 'adjust_size'):
                    # 增加延迟时间，确保列宽已经更新
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(50, lambda edit=text_edit: edit.adjust_size_without_row_resize())
        
    def create_collapsible_log_area(self, layout):
        """创建可折叠的日志区域"""
        # 日志区域容器
        self.log_container = QWidget()
        log_container_layout = QVBoxLayout(self.log_container)
        log_container_layout.setContentsMargins(0, 0, 0, 0)
        log_container_layout.setSpacing(0)
        
        # 日志标题栏（可点击展开/收起）
        self.log_header = QWidget()
        self.log_header.setFixedHeight(40)
        self.log_header.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QWidget:hover {
                background-color: #e8f4fd;
            }
        """)
        self.log_header.setCursor(Qt.PointingHandCursor)
        
        # 标题栏布局
        header_layout = QHBoxLayout(self.log_header)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        # 展开/收起图标
        self.log_toggle_icon = QLabel("▼")
        self.log_toggle_icon.setStyleSheet("font-size: 12px; color: #666666;")
        self.log_toggle_icon.setFixedWidth(20)
        
        # 标题文本
        self.log_title = QLabel("转换日志")
        self.log_title.setStyleSheet("font-weight: bold; color: #333333; font-size: 14px;")
        
        # 日志状态指示器
        self.log_status = QLabel("就绪")
        self.log_status.setStyleSheet("color: #666666; font-size: 12px;")
        
        header_layout.addWidget(self.log_toggle_icon)
        header_layout.addWidget(self.log_title)
        header_layout.addStretch()
        header_layout.addWidget(self.log_status)
        
        # 日志内容区域
        self.log_content = QWidget()
        self.log_content.setVisible(False)  # 默认收起
        log_content_layout = QVBoxLayout(self.log_content)
        log_content_layout.setContentsMargins(0, 5, 0, 0)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)  # 增加最大高度
        self.log_text.setMinimumHeight(120)  # 设置最小高度
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 8px;
            }
        """)
        
        # 日志操作按钮
        log_buttons_layout = QHBoxLayout()
        
        self.clear_log_btn = PushButton("清空日志")
        self.clear_log_btn.setFixedSize(80, 30)
        self.clear_log_btn.clicked.connect(self.clear_log)
        
        self.save_log_btn = PushButton("保存日志")
        self.save_log_btn.setFixedSize(80, 30)
        self.save_log_btn.clicked.connect(self.save_log)
        
        log_buttons_layout.addWidget(self.clear_log_btn)
        log_buttons_layout.addWidget(self.save_log_btn)
        log_buttons_layout.addStretch()
        
        log_content_layout.addWidget(self.log_text)
        log_content_layout.addLayout(log_buttons_layout)
        
        # 添加到容器
        log_container_layout.addWidget(self.log_header)
        log_container_layout.addWidget(self.log_content)
        
        # 添加到主布局
        layout.addWidget(self.log_container)
        
        # 连接点击事件
        self.log_header.mousePressEvent = self.toggle_log_area
        
        # 初始状态
        self.log_expanded = False
        
    def toggle_log_area(self, event):
        """切换日志区域的展开/收起状态"""
        self.log_expanded = not self.log_expanded
        self.log_content.setVisible(self.log_expanded)
        
        # 更新图标
        if self.log_expanded:
            self.log_toggle_icon.setText("▲")
            self.log_title.setText("转换日志 (点击收起)")
        else:
            self.log_toggle_icon.setText("▼")
            self.log_title.setText("转换日志 (点击展开)")
            
        # 添加动画效果的提示
        InfoBar.info(
            title="日志区域",
            content="已展开" if self.log_expanded else "已收起",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=1000,
            parent=self
        )
        
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.log_message("日志已清空")
        
    def save_log(self):
        """保存日志到文件"""
        if not self.log_text.toPlainText().strip():
            MessageBox("提示", "日志为空，无需保存", self).exec()
            return
            
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存日志文件",
            f"tts_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                    
                InfoBar.success(
                    title="保存成功",
                    content=f"日志已保存到: {os.path.basename(file_path)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                MessageBox("错误", f"保存日志失败: {str(e)}", self).exec()
        
    def on_item_changed(self, item):
        """处理表格项目编辑后的保存"""
        if not self.draft_data:
            return
            
        row = item.row()
        col = item.column()
        
        # 只处理文本内容列的编辑（第1列）
        if col == 1:
            text_id = item.data(Qt.UserRole)
            new_content = item.text()
            
            try:
                # 更新原始数据中的文本内容
                texts = self.draft_data.get("materials", {}).get("texts", [])
                for text in texts:
                    if text.get("id") == text_id:
                        content_data = json.loads(text.get("content", "{}"))
                        content_data["text"] = new_content
                        
                        # 修复样式范围问题：确保只有一个样式，并且范围覆盖整个文本
                        if "styles" in content_data and content_data["styles"]:
                            # 只保留第一个样式，删除其他样式
                            first_style = content_data["styles"][0]
                            first_style["range"] = [0, len(new_content)]
                            content_data["styles"] = [first_style]
                        else:
                            # 如果没有样式，创建默认样式
                            content_data["styles"] = [{
                                "size": 15,
                                "font": {
                                    "path": "C:/Users/shiya/AppData/Local/JianyingPro/Apps/5.9.0.11632/Resources/Font/SystemFont/zh-hans.ttf",
                                    "id": ""
                                },
                                "fill": {
                                    "content": {
                                        "solid": {
                                            "color": [1, 1, 1]
                                        }
                                    }
                                },
                                "range": [0, len(new_content)]
                            }]
                        
                        text["content"] = json.dumps(content_data, ensure_ascii=False)
                        
                        # 同时更新顶级的 base_content 字段（如果存在）
                        if "base_content" in text:
                            text["base_content"] = new_content
                        break
                
                # 更新工具提示
                item.setToolTip(new_content)
                
                # 自动调整行高以适应新内容
                self.text_table.resizeRowToContents(row)
                
                self.log_message(f"已更新文本内容: {new_content[:30]}{'...' if len(new_content) > 30 else ''}")
                
                InfoBar.success(
                    title="文本已更新",
                    content="文本内容已保存到工程文件",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=1500,
                    parent=self
                )
                
            except Exception as e:
                self.log_message(f"更新文本内容失败: {str(e)}")
                MessageBox("错误", f"更新文本内容失败: {str(e)}", self).exec()
                # 恢复原始内容
                self.refresh_text_list()
        
    # 音频播放器信号处理方法
    def on_audio_playback_started(self, audio_path):
        """音频播放开始时的处理"""
        filename = os.path.basename(audio_path)
        self.log_message(f"开始播放音频: {filename}")
        
        InfoBar.info(
            title="正在播放音频",
            content=f"正在播放: {filename}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def on_audio_playback_finished(self, audio_path):
        """音频播放完成时的处理"""
        filename = os.path.basename(audio_path)
        self.log_message(f"播放完成: {filename}")
        
    def on_audio_playback_error(self, audio_path, error_message):
        """音频播放错误时的处理"""
        filename = os.path.basename(audio_path) if audio_path else "未知文件"
        self.log_message(f"播放错误 {filename}: {error_message}")
        
        InfoBar.error(
            title="播放错误",
            content=f"播放 {filename} 时出错: {error_message}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        
    def on_batch_playback_finished(self):
        """批量播放完成时的处理"""
        self.log_message("批量播放完成")
        
        InfoBar.success(
            title="播放完成",
            content="所有音频文件播放完成",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            TTSManager {
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
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0d0d0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #1976d2;
            }
            QTextEdit {
                background-color: #f8f9fa;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
            QProgressBar {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 3px;
            }
        """)
        
    def load_draft_file(self, file_path):
        """加载剪映工程文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.draft_data = json.load(f)
            self.draft_file_path = file_path
            self.refresh_text_list()
            self.log_message(f"已加载工程文件: {os.path.basename(file_path)}")
            InfoBar.success(
                title="文件已加载",
                content=f"已加载: {os.path.basename(file_path)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            error_msg = f"加载文件失败: {str(e)}"
            self.log_message(error_msg)
            MessageBox("错误", error_msg, self).exec()
            
    def refresh_text_list(self):
        """刷新文本列表"""
        self.text_table.setRowCount(0)
        if not self.draft_data:
            return
            
        texts = self.draft_data.get("materials", {}).get("texts", [])
        self.text_table.setRowCount(len(texts))
        
        for row, text in enumerate(texts):
            text_id = text.get("id")
            content_data = json.loads(text.get("content", "{}"))
            text_content = content_data.get("text", f"文本 {row+1}")
            
            # 初始化配置
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
                        'length_penalty': 1.0,
                        'max_mel_tokens': 800,
                        'max_text_tokens_per_sentence': 120,
                        'sentences_bucket_max_size': 4,
                    }
                }
            
            config = self.text_configs[text_id]
            params = config['tts_params']
            
            # 选择框
            checkbox = QCheckBox()
            self.text_table.setCellWidget(row, 0, checkbox)
            
            # 文本内容 - 使用内嵌的多行文本编辑器
            text_edit = MultiLineTextEdit(text_content, text_id, self, None)
            self.text_table.setCellWidget(row, 1, text_edit)
            
            # 参考音频预览组件
            audio_preview = AudioPreviewWidget()
            audio_preview.set_audio_path(config['reference_voice'])
            self.text_table.setCellWidget(row, 2, audio_preview)
            
            # 推理模式
            mode_item = QTableWidgetItem(config['infer_mode'])
            self.text_table.setItem(row, 3, mode_item)
            
            # 高级参数 - 使用可编辑的输入框
            # Do Sample 复选框
            do_sample_checkbox = ParameterCheckBox(params['do_sample'])
            do_sample_checkbox.toggled.connect(lambda v, tid=text_id: self.update_parameter(tid, 'do_sample', v))
            self.text_table.setCellWidget(row, 4, do_sample_checkbox)
            
            temp_spin = ParameterSpinBox(0.1, 2.0, params['temperature'], 0.1, 2)
            temp_spin.valueChanged.connect(lambda v, tid=text_id: self.update_parameter(tid, 'temperature', v))
            self.text_table.setCellWidget(row, 5, temp_spin)
            
            top_p_spin = ParameterSpinBox(0.0, 1.0, params['top_p'], 0.01, 3)
            top_p_spin.valueChanged.connect(lambda v, tid=text_id: self.update_parameter(tid, 'top_p', v))
            self.text_table.setCellWidget(row, 6, top_p_spin)
            
            top_k_spin = ParameterIntSpinBox(0, 100, params['top_k'])
            top_k_spin.valueChanged.connect(lambda v, tid=text_id: self.update_parameter(tid, 'top_k', v))
            self.text_table.setCellWidget(row, 7, top_k_spin)
            
            beams_spin = ParameterIntSpinBox(1, 10, params['num_beams'])
            beams_spin.valueChanged.connect(lambda v, tid=text_id: self.update_parameter(tid, 'num_beams', v))
            self.text_table.setCellWidget(row, 8, beams_spin)
            
            # 新增的参数列
            rep_penalty_spin = ParameterSpinBox(0.1, 20.0, params['repetition_penalty'], 0.1, 1)
            rep_penalty_spin.valueChanged.connect(lambda v, tid=text_id: self.update_parameter(tid, 'repetition_penalty', v))
            self.text_table.setCellWidget(row, 9, rep_penalty_spin)
            
            length_penalty_spin = ParameterSpinBox(-2.0, 2.0, params['length_penalty'], 0.1, 1)
            length_penalty_spin.valueChanged.connect(lambda v, tid=text_id: self.update_parameter(tid, 'length_penalty', v))
            self.text_table.setCellWidget(row, 10, length_penalty_spin)
            
            max_mel_spin = ParameterIntSpinBox(50, 1000, params['max_mel_tokens'])
            max_mel_spin.valueChanged.connect(lambda v, tid=text_id: self.update_parameter(tid, 'max_mel_tokens', v))
            self.text_table.setCellWidget(row, 11, max_mel_spin)
            
            max_text_spin = ParameterIntSpinBox(20, 300, params['max_text_tokens_per_sentence'])
            max_text_spin.valueChanged.connect(lambda v, tid=text_id: self.update_parameter(tid, 'max_text_tokens_per_sentence', v))
            self.text_table.setCellWidget(row, 12, max_text_spin)
            
            # Bucket Size 参数（批次推理生效）
            bucket_size_spin = ParameterIntSpinBox(1, 16, params['sentences_bucket_max_size'])
            bucket_size_spin.valueChanged.connect(lambda v, tid=text_id: self.update_parameter(tid, 'sentences_bucket_max_size', v))
            self.text_table.setCellWidget(row, 13, bucket_size_spin)
            
            # 检查是否已存在音频并设置状态
            existing_audio_info = self.get_existing_audio_info(text_id)
            
            if existing_audio_info:
                # 已有音频 - 创建播放按钮和文件名
                audio_widget = QWidget()
                audio_layout = QHBoxLayout(audio_widget)
                audio_layout.setContentsMargins(2, 2, 2, 2)
                audio_layout.setSpacing(5)
                
                # 播放按钮
                play_btn = QPushButton("▶")
                play_btn.setFixedSize(20, 20)
                play_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4caf50;
                        color: white;
                        border: none;
                        border-radius: 10px;
                        font-size: 10px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                    QPushButton:pressed {
                        background-color: #3d8b40;
                    }
                """)
                play_btn.clicked.connect(lambda checked, path=existing_audio_info.get('full_path', ''): self.play_audio_file(path))
                
                # 文件名标签
                audio_filename = existing_audio_info.get('filename', '')
                audio_label = QLabel(audio_filename)
                audio_label.setStyleSheet("color: #4caf50; font-size: 11px;")
                audio_label.setToolTip(existing_audio_info.get('full_path', ''))
                
                audio_layout.addWidget(play_btn)
                audio_layout.addWidget(audio_label)
                audio_layout.addStretch()
                
                self.text_table.setCellWidget(row, 15, audio_widget)
                
                status_item = QTableWidgetItem("已有音频")
                status_item.setForeground(QColor(76, 175, 80))  # 绿色
            else:
                # 未转换
                status_item = QTableWidgetItem("未转换")
                status_item.setForeground(QColor(128, 128, 128))  # 灰色
                
                # 空音频路径
                audio_path_item = QTableWidgetItem("")
                self.text_table.setItem(row, 15, audio_path_item)
            
            self.text_table.setItem(row, 14, status_item)  # 转换状态列现在是第14列
            
        # 刷新完成后，调整所有行的高度以适应内容
        self.text_table.resizeRowsToContents()
        
        # 延迟再次调整行高，确保内嵌编辑器的初始化完成
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self.smart_resize_rows)
        
        self.log_message(f"已刷新文本列表，共 {len(texts)} 个文本")
        
    def smart_resize_rows(self):
        """智能调整行高 - 既保持手动调整能力又能自动适应内容"""
        for row in range(self.text_table.rowCount()):
            # 获取该行的文本编辑器
            text_edit = self.text_table.cellWidget(row, 1)
            if text_edit and hasattr(text_edit, 'height'):
                # 获取文本编辑器的理想高度
                ideal_height = text_edit.height()
                # 添加一些额外的边距
                row_height = max(90, ideal_height + 20)  # 最小90px，加20px边距
                # 设置行高
                self.text_table.setRowHeight(row, row_height)
                
    def auto_resize_all_rows(self):
        """自动调整所有行高的按钮响应方法"""
        self.smart_resize_rows()
        InfoBar.success(
            title="行高已调整",
            content="已根据文本内容自动调整所有行的高度",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def log_message(self, message):
        """添加日志消息"""
        if hasattr(self, 'log_text'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.append(f"[{timestamp}] {message}")
        
    def on_text_content_changed(self, text_id, new_content):
        """处理内嵌文本编辑器的内容变化"""
        if not self.draft_data or not text_id:
            return
            
        try:
            # 更新数据中的文本内容
            self.update_text_content(text_id, new_content)
        except Exception as e:
            print(f"更新文本内容失败: {str(e)}")
            
    def update_text_content(self, text_id, content):
        """更新文本内容"""
        texts = self.draft_data.get("materials", {}).get("texts", [])
        for text in texts:
            if text.get("id") == text_id:
                content_data = json.loads(text.get("content", "{}"))
                content_data["text"] = content
                
                # 修复样式范围问题：确保只有一个样式，并且范围覆盖整个文本
                if "styles" in content_data and content_data["styles"]:
                    # 只保留第一个样式，删除其他样式
                    first_style = content_data["styles"][0]
                    first_style["range"] = [0, len(content)]
                    content_data["styles"] = [first_style]
                else:
                    # 如果没有样式，创建默认样式
                    content_data["styles"] = [{
                        "size": 15,
                        "font": {
                            "path": "C:/Users/shiya/AppData/Local/JianyingPro/Apps/5.9.0.11632/Resources/Font/SystemFont/zh-hans.ttf",
                            "id": ""
                        },
                        "fill": {
                            "content": {
                                "solid": {
                                    "color": [1, 1, 1]
                                }
                            }
                        },
                        "range": [0, len(content)]
                    }]
                
                text["content"] = json.dumps(content_data, ensure_ascii=False)
                
                # 同时更新顶级的 base_content 字段（如果存在）
                if "base_content" in text:
                    text["base_content"] = content
                break
        
    def get_text_content_by_id(self, text_id):
        """根据文本ID从原始数据中获取完整的文本内容"""
        if not self.draft_data:
            return ""
            
        try:
            texts = self.draft_data.get("materials", {}).get("texts", [])
            for text in texts:
                if text.get("id") == text_id:
                    content_data = json.loads(text.get("content", "{}"))
                    return content_data.get("text", "")
            return ""
        except Exception as e:
            print(f"获取文本内容失败: {e}")
            return ""
        
    def get_existing_audio_info(self, text_id):
        """获取现有音频信息"""
        if not self.draft_data:
            return None
            
        try:
            # 查找该文本ID对应的音频
            audios = self.draft_data.get("materials", {}).get("audios", [])
            for audio in audios:
                if audio.get("text_id") == text_id:
                    audio_path = audio.get("path", "")
                    if audio_path:
                        # 提取文件名
                        if "textReading/" in audio_path:
                            filename = audio_path.split("textReading/")[-1]
                        else:
                            filename = os.path.basename(audio_path)
                        
                        # 构建完整路径用于检查文件是否存在
                        if self.draft_file_path:
                            draft_dir = os.path.dirname(self.draft_file_path)
                            full_path = os.path.join(draft_dir, "textReading", filename)
                        else:
                            full_path = audio_path
                        
                        return {
                            'filename': filename,
                            'full_path': full_path,
                            'exists': os.path.exists(full_path) if full_path else False
                        }
            return None
        except Exception as e:
            print(f"获取现有音频信息失败: {e}")
            return None
        
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
            if audio_path:
                # 从内嵌的文本编辑器获取文本ID
                text_edit = self.text_table.cellWidget(row, 1)
                if not text_edit or not hasattr(text_edit, 'text_id'):
                    return
                text_id = text_edit.text_id
                
                self.text_configs[text_id]['reference_voice'] = audio_path
                
                # 更新表格显示
                audio_preview = self.text_table.cellWidget(row, 2)
                if audio_preview:
                    audio_preview.set_audio_path(audio_path)
                
                self.log_message(f"已设置参考音频: {os.path.basename(audio_path)}")
                
    def select_infer_mode(self, row):
        """选择推理模式"""
        # 从内嵌的文本编辑器获取文本ID
        text_edit = self.text_table.cellWidget(row, 1)
        if not text_edit or not hasattr(text_edit, 'text_id'):
            return
        text_id = text_edit.text_id
        
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
            self.log_message(f"已设置推理模式: {mode}")
            
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

    def get_selected_text_items(self):
        """获取选中的文本项"""
        selected_items = []
        for row in range(self.text_table.rowCount()):
            checkbox = self.text_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                # 从内嵌的文本编辑器获取文本ID
                text_edit = self.text_table.cellWidget(row, 1)
                if not text_edit or not hasattr(text_edit, 'text_id'):
                    continue
                text_id = text_edit.text_id
                
                # 从内嵌编辑器获取当前的文本内容
                text_content = text_edit.get_text()
                config = self.text_configs.get(text_id, {})
                
                # 调试信息：记录获取到的文本内容长度
                print(f"DEBUG: 文本ID {text_id} 的内容长度: {len(text_content)}, 内容: {text_content[:50]}{'...' if len(text_content) > 50 else ''}")
                
                selected_items.append({
                    'text_id': text_id,
                    'text_content': text_content,
                    'reference_voice': config.get('reference_voice', ''),
                    'infer_mode': config.get('infer_mode', '普通推理'),
                    'tts_params': config.get('tts_params', {}),
                    'row': row
                })
        return selected_items
        
    def start_conversion(self):
        """开始转换"""
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
        self.convert_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 更新选中文本的状态
        for item in selected_items:
            row = item['row']
            status_item = self.text_table.item(row, 14)  # 转换状态列现在是第14列
            status_item.setText("等待转换")
            status_item.setForeground(QColor(255, 165, 0))  # 橙色
            
        self.log_message(f"开始转换 {len(selected_items)} 个文本...")
        
        # 调试：在日志中显示每个文本的完整内容
        for i, item in enumerate(selected_items, 1):
            text_content = item['text_content']
            self.log_message(f"文本 {i}: 长度={len(text_content)}, 内容=\"{text_content}\"")
        
        # 启动工作线程
        self.tts_worker = TTSWorker(selected_items, self.draft_file_path, self.draft_data)
        self.tts_worker.progress_updated.connect(self.on_progress_updated)
        self.tts_worker.conversion_finished.connect(self.on_conversion_finished)
        self.tts_worker.error_occurred.connect(self.on_error_occurred)
        self.tts_worker.finished.connect(self.on_worker_finished)
        self.tts_worker.start()
        
    def stop_conversion(self):
        """停止转换"""
        if self.tts_worker and self.tts_worker.isRunning():
            self.tts_worker.cancel()
            self.log_message("正在停止转换...")
            
    @pyqtSlot(int, str)
    def on_progress_updated(self, progress, status):
        """进度更新"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
        
    @pyqtSlot(str, str, bool)
    def on_conversion_finished(self, text_id, output_path, success):
        """转换完成"""
        # 查找对应的行
        for row in range(self.text_table.rowCount()):
            # 从内嵌的文本编辑器获取文本ID进行比较
            text_edit = self.text_table.cellWidget(row, 1)
            if text_edit and hasattr(text_edit, 'text_id') and text_edit.text_id == text_id:
                status_item = self.text_table.item(row, 14)  # 转换状态列现在是第14列
                audio_path_item = self.text_table.item(row, 15)  # 音频路径列现在是第15列
                
                if success:
                    status_item.setText("转换成功")
                    status_item.setForeground(QColor(76, 175, 80))  # 绿色
                    
                    # 创建播放按钮和文件名显示
                    audio_widget = QWidget()
                    audio_layout = QHBoxLayout(audio_widget)
                    audio_layout.setContentsMargins(2, 2, 2, 2)
                    audio_layout.setSpacing(5)
                    
                    # 播放按钮
                    play_btn = QPushButton("▶")
                    play_btn.setFixedSize(20, 20)
                    play_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #4caf50;
                            color: white;
                            border: none;
                            border-radius: 10px;
                            font-size: 10px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #45a049;
                        }
                        QPushButton:pressed {
                            background-color: #3d8b40;
                        }
                    """)
                    play_btn.clicked.connect(lambda checked, path=output_path: self.play_audio_file(path))
                    
                    # 文件名标签
                    audio_filename = os.path.basename(output_path)
                    audio_label = QLabel(audio_filename)
                    audio_label.setStyleSheet("color: #4caf50; font-size: 11px;")
                    audio_label.setToolTip(output_path)
                    
                    audio_layout.addWidget(play_btn)
                    audio_layout.addWidget(audio_label)
                    audio_layout.addStretch()
                    
                    self.text_table.setCellWidget(row, 15, audio_widget)
                    
                    self.log_message(f"转换成功: {output_path}")
                    
                    # 更新剪映工程文件中的音频路径
                    self.update_audio_in_draft(text_id, output_path)
                else:
                    status_item.setText("转换失败")
                    status_item.setForeground(QColor(244, 67, 54))  # 红色
                    
                break
                
    @pyqtSlot(str, str)
    def on_error_occurred(self, text_id, error_message):
        """转换错误"""
        self.log_message(f"转换错误 [{text_id}]: {error_message}")
        
    @pyqtSlot()
    def on_worker_finished(self):
        """工作线程完成"""
        self.convert_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("转换完成")
        self.log_message("所有转换任务已完成")
        
        InfoBar.success(
            title="转换完成",
            content="文本转语音任务已完成",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        
    def update_audio_in_draft(self, text_id, audio_path):
        """更新剪映工程文件中的音频"""
        if not self.draft_data:
            return
            
        try:
            # 检查是否已存在对应的音频
            audios = self.draft_data.get("materials", {}).get("audios", [])
            existing_audio = None
            
            for audio in audios:
                if audio.get("text_id") == text_id:
                    existing_audio = audio
                    break
            # 获取音频文件信息
            audio_duration = self.get_audio_duration(audio_path)
            if existing_audio:
                # 更新现有音频路径 - 保持原有的占位符格式
                original_path = existing_audio.get("path", "")
                if "##_draftpath_placeholder_" in original_path and "textReading/" in original_path:
                    # 保持原有的占位符格式，只更新文件名
                    placeholder_part = original_path.split("/textReading/")[0]
                    new_filename = os.path.basename(audio_path)
                    draft_audio_path = f"{placeholder_part}/textReading/{new_filename}"
                else:
                    # 使用绝对路径
                    draft_audio_path = os.path.abspath(audio_path)
                
                existing_audio["path"] = draft_audio_path
                existing_audio["name"] = os.path.splitext(os.path.basename(audio_path))[0]
                # 更新音频时长
                existing_audio["duration"] = self.get_audio_duration(audio_path)
                self.log_message(f"已更新音频路径: {text_id}")
            else:
                
                # 对于新音频，使用绝对路径确保可访问性
                draft_audio_path = os.path.abspath(audio_path)
                
                # 创建新的音频条目（参考JSON结构）
                new_audio = {
                    "app_id": 0,
                    "category_id": "",
                    "category_name": "",
                    "check_flag": 1,
                    "copyright_limit_type": "none",
                    "duration": audio_duration,
                    "effect_id": "",
                    "formula_id": "",
                    "id": str(uuid.uuid4()).upper(),
                    "intensifies_path": "",
                    "is_ai_clone_tone": False,
                    "is_text_edit_overdub": False,
                    "is_ugc": True,
                    "local_material_id": "",
                    "music_id": "",
                    "name": os.path.splitext(os.path.basename(audio_path))[0],
                    "path": draft_audio_path,
                    "query": "",
                    "request_id": "",
                    "resource_id": "",
                    "search_id": "",
                    "source_from": "",
                    "source_platform": 0,
                    "team_id": "",
                    "text_id": text_id,
                    "tone_category_id": "",
                    "tone_category_name": "",
                    "tone_effect_id": "",
                    "tone_effect_name": "",
                    "tone_platform": "sami",
                    "tone_second_category_id": "",
                    "tone_second_category_name": "",
                    "tone_speaker": "BV408_streaming",
                    "tone_type": "译制片男",
                    "type": "text_to_audio",
                    "video_id": "",
                    "wave_points": []
                }
                
                if "materials" not in self.draft_data:
                    self.draft_data["materials"] = {}
                if "audios" not in self.draft_data["materials"]:
                    self.draft_data["materials"]["audios"] = []
                    
                self.draft_data["materials"]["audios"].append(new_audio)
                
                # 添加到音频轨道
                self.add_audio_to_track(new_audio, text_id)
                self.log_message(f"已添加新音频: {text_id}")
            
            # 同步文本和音频的显示时长
            self.sync_text_audio_duration(text_id, audio_duration)
            
            # 自动保存工程文件
            self.auto_save_draft_file()
                
        except Exception as e:
            self.log_message(f"更新音频失败: {str(e)}")
            
    def get_audio_duration(self, audio_path):
        """获取音频时长（微秒）"""
        try:
            # 尝试使用多种方法获取音频时长
            duration_us = None
            
            # 方法1：尝试使用wave库（适用于WAV文件）
            if audio_path.lower().endswith('.wav'):
                try:
                    import wave
                    with wave.open(audio_path, 'rb') as wav_file:
                        frames = wav_file.getnframes()
                        sample_rate = wav_file.getframerate()
                        duration_seconds = frames / float(sample_rate)
                        duration_us = int(duration_seconds * 1000000)  # 转换为微秒
                        self.log_message(f"使用wave库获取音频时长: {duration_seconds:.2f}秒")
                except Exception as e:
                    print(f"wave库获取时长失败: {e}")
            
            # 方法2：尝试使用mutagen库（支持多种格式）
            if duration_us is None:
                try:
                    from mutagen import File
                    audio_file = File(audio_path)
                    if audio_file is not None and hasattr(audio_file, 'info'):
                        duration_seconds = audio_file.info.length
                        duration_us = int(duration_seconds * 1000000)  # 转换为微秒
                        self.log_message(f"使用mutagen库获取音频时长: {duration_seconds:.2f}秒")
                except ImportError:
                    self.log_message("提示: 安装mutagen库可获得更准确的音频时长 (pip install mutagen)")
                except Exception as e:
                    print(f"mutagen库获取时长失败: {e}")
            
            # 方法3：尝试使用pydub库（备用方法）
            if duration_us is None:
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(audio_path)
                    duration_seconds = len(audio) / 1000.0  # pydub返回毫秒
                    duration_us = int(duration_seconds * 1000000)  # 转换为微秒
                    self.log_message(f"使用pydub库获取音频时长: {duration_seconds:.2f}秒")
                except ImportError:
                    self.log_message("提示: 安装pydub库可获得更准确的音频时长 (pip install pydub)")
                except Exception as e:
                    print(f"pydub库获取时长失败: {e}")
            
            # 方法4：使用文件大小估算（最后的备用方法）
            if duration_us is None:
                file_size = os.path.getsize(audio_path)
                # 粗略估算：假设是44.1kHz 16bit 单声道 WAV
                estimated_duration = int((file_size / (44100 * 2)) * 1000000)  # 转换为微秒
                duration_us = max(estimated_duration, 1000000)  # 至少1秒
                self.log_message(f"使用文件大小估算音频时长: {duration_us/1000000:.2f}秒 (建议安装音频处理库获得准确时长)")
            
            return duration_us
            
        except Exception as e:
            self.log_message(f"获取音频时长失败: {str(e)}")
            return 3000000  # 默认3秒
            
    def sync_text_audio_duration(self, text_id, audio_duration):
        """同步文本和音频的显示时长"""
        if not self.draft_data:
            return
            
        try:
            tracks = self.draft_data.get("tracks", [])
            
            # 更新文本轨道的时长
            for track in tracks:
                if track.get("type") == "text":
                    segments = track.get("segments", [])
                    for segment in segments:
                        if segment.get("material_id") == text_id:
                            if "target_timerange" not in segment:
                                segment["target_timerange"] = {}
                            # 保持开始时间不变，只更新持续时间
                            start_time = segment["target_timerange"].get("start", 0)
                            segment["target_timerange"]["duration"] = audio_duration
                            self.log_message(f"已同步文本显示时长: {audio_duration/1000000:.2f}秒")
                            break
                            
            # 更新音频轨道的时长
            for track in tracks:
                if track.get("type") == "audio":
                    segments = track.get("segments", [])
                    for segment in segments:
                        # 通过音频材料ID查找对应的音频
                        material_id = segment.get("material_id")
                        if material_id:
                            # 查找音频材料
                            audios = self.draft_data.get("materials", {}).get("audios", [])
                            for audio in audios:
                                if audio.get("id") == material_id and audio.get("text_id") == text_id:
                                    # 更新音频轨道时长
                                    if "target_timerange" not in segment:
                                        segment["target_timerange"] = {}
                                    if "source_timerange" not in segment:
                                        segment["source_timerange"] = {}
                                    
                                    # 保持开始时间不变，更新持续时间
                                    start_time = segment["target_timerange"].get("start", 0)
                                    segment["target_timerange"]["duration"] = audio_duration
                                    segment["source_timerange"]["duration"] = audio_duration
                                    segment["source_timerange"]["start"] = 0
                                    
                                    self.log_message(f"已同步音频轨道时长: {audio_duration/1000000:.2f}秒")
                                    break
                                    
            # 更新工程文件总时长
            self.update_project_duration()
                                    
        except Exception as e:
            self.log_message(f"同步时长失败: {str(e)}")
            
    def add_audio_to_track(self, audio_data, text_id):
        """将音频添加到轨道"""
        try:
            # 查找文本的时间信息
            tracks = self.draft_data.get("tracks", [])
            text_start_time = 0
            audio_duration = audio_data.get("duration", 3000000)  # 使用音频实际时长
            
            for track in tracks:
                if track.get("type") == "text":
                    segments = track.get("segments", [])
                    for segment in segments:
                        if segment.get("material_id") == text_id:
                            timerange = segment.get("target_timerange", {})
                            text_start_time = timerange.get("start", 0)
                            # 同时更新文本轨道的时长为音频时长
                            segment["target_timerange"]["duration"] = audio_duration
                            self.log_message(f"已同步文本轨道时长为音频时长: {audio_duration/1000000:.2f}秒")
                            break
                            
            # 查找或创建音频轨道
            audio_track = None
            for track in tracks:
                if track.get("type") == "audio":
                    audio_track = track
                    break
                    
            if not audio_track:
                # 创建完整的音频轨道结构（参考JSON格式）
                audio_track = {
                    "attribute": 0,
                    "flag": 0,
                    "id": str(uuid.uuid4()).upper(),
                    "is_default_name": True,
                    "name": "",
                    "segments": [],
                    "type": "audio"
                }
                tracks.append(audio_track)
                
            # 创建完整的音频段结构（参考JSON格式）
            audio_segment = {
                "caption_info": None,
                "cartoon": False,
                "clip": None,
                "common_keyframes": [],
                "enable_adjust": False,
                "enable_color_correct_adjust": False,
                "enable_color_curves": True,
                "enable_color_match_adjust": False,
                "enable_color_wheels": True,
                "enable_lut": False,
                "enable_smart_color_adjust": False,
                "extra_material_refs": [
                    "E6D754F0-93FD-42aa-88C8-00CA2F323D38",  # speed
                    "1ACBBAC6-1DD0-4853-A61F-AC05E4B3420F",  # beats
                    "67E01E62-6DA9-426c-A8CA-86A49EE40367",  # sound_channel_mapping
                    "63A4D7A1-73A2-4234-BEF6-1F0204FAE3B5"   # vocal_separation
                ],
                "group_id": "",
                "hdr_settings": None,
                "id": str(uuid.uuid4()).upper(),
                "intensifies_audio": False,
                "is_placeholder": False,
                "is_tone_modify": False,
                "keyframe_refs": [],
                "last_nonzero_volume": 1.0,
                "material_id": audio_data["id"],
                "render_index": 0,
                "responsive_layout": {
                    "enable": False,
                    "horizontal_pos_layout": 0,
                    "size_layout": 0,
                    "target_follow": "",
                    "vertical_pos_layout": 0
                },
                "reverse": False,
                "source_timerange": {
                    "duration": audio_duration,
                    "start": 0
                },
                "speed": 1.0,
                "target_timerange": {
                    "duration": audio_duration,
                    "start": text_start_time
                },
                "template_id": "",
                "template_scene": "default",
                "track_attribute": 0,
                "track_render_index": 0,
                "uniform_scale": None,
                "visible": True,
                "volume": 1.0
            }
            
            audio_track["segments"].append(audio_segment)
            self.log_message(f"已添加音频段到轨道: {text_id}")
            
            # 更新工程文件总时长
            self.update_project_duration()
            
        except Exception as e:
            self.log_message(f"添加音频到轨道失败: {str(e)}")
            
    def auto_save_draft_file(self):
        """自动保存剪映工程文件"""
        if not self.draft_data or not self.draft_file_path:
            return
            
        try:
            # 保存前自动计算并更新总时长
            self.update_project_duration()
            
            with open(self.draft_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.draft_data, f, ensure_ascii=False, indent=2)
                
            self.log_message(f"已自动保存工程文件: {os.path.basename(self.draft_file_path)}")
        except Exception as e:
            self.log_message(f"自动保存失败: {str(e)}")
            
    def save_draft_file(self):
        """手动保存剪映工程文件"""
        if not self.draft_data or not self.draft_file_path:
            MessageBox("错误", "没有可保存的文件", self).exec()
            return
            
        try:
            # 保存前自动计算并更新总时长
            self.update_project_duration()
            
            with open(self.draft_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.draft_data, f, ensure_ascii=False, indent=2)
                
            self.log_message(f"已手动保存工程文件: {self.draft_file_path}")
            InfoBar.success(
                title="文件已保存",
                content=f"已保存到: {self.draft_file_path}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            error_msg = f"保存文件失败: {str(e)}"
            self.log_message(error_msg)
            MessageBox("错误", error_msg, self).exec()
            
    def open_batch_settings(self):
        """打开批量参数设置对话框"""
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            MessageBox("提示", "请先选择要批量设置的文本项", self).exec()
            return
            
        dialog = BatchParameterDialog(self)
        if dialog.exec() == QDialog.Accepted:
            batch_settings = dialog.get_batch_settings()
            if batch_settings:
                self.apply_batch_settings(selected_rows, batch_settings)
            else:
                MessageBox("提示", "没有选择任何要批量设置的参数", self).exec()
                
    def get_selected_rows(self):
        """获取选中的行"""
        selected_rows = []
        for row in range(self.text_table.rowCount()):
            checkbox = self.text_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_rows.append(row)
        return selected_rows
        
    def apply_batch_settings(self, selected_rows, batch_settings):
        """应用批量设置"""
        try:
            updated_count = 0
            
            for row in selected_rows:
                # 从内嵌的文本编辑器获取文本ID
                text_edit = self.text_table.cellWidget(row, 1)
                if not text_edit or not hasattr(text_edit, 'text_id'):
                    continue
                text_id = text_edit.text_id
                if text_id not in self.text_configs:
                    continue
                    
                config = self.text_configs[text_id]
                
                # 应用参考音频设置
                if 'reference_voice' in batch_settings:
                    config['reference_voice'] = batch_settings['reference_voice']
                    # 更新表格中的音频预览
                    audio_preview = self.text_table.cellWidget(row, 2)
                    if audio_preview:
                        audio_preview.set_audio_path(batch_settings['reference_voice'])
                        
                # 应用推理模式设置
                if 'infer_mode' in batch_settings:
                    config['infer_mode'] = batch_settings['infer_mode']
                    # 更新表格中的推理模式显示
                    mode_item = self.text_table.item(row, 3)
                    if mode_item:
                        mode_item.setText(batch_settings['infer_mode'])
                        
                # 应用TTS参数设置
                if 'tts_params' in batch_settings:
                    tts_params = batch_settings['tts_params']
                    for param_name, param_value in tts_params.items():
                        config['tts_params'][param_name] = param_value
                        
                    # 更新表格中的参数控件
                    self.update_table_parameters(row, tts_params)
                    
                updated_count += 1
                
            self.log_message(f"已批量更新 {updated_count} 个文本的参数设置")
            
            InfoBar.success(
                title="批量设置完成",
                content=f"已更新 {updated_count} 个文本的参数",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
        except Exception as e:
            error_msg = f"批量设置失败: {str(e)}"
            self.log_message(error_msg)
            MessageBox("错误", error_msg, self).exec()
            
    def update_table_parameters(self, row, tts_params):
        """更新表格中的参数控件"""
        try:
            # 更新Do Sample
            if 'do_sample' in tts_params:
                widget = self.text_table.cellWidget(row, 4)
                if isinstance(widget, ParameterCheckBox):
                    widget.setChecked(tts_params['do_sample'])
                    
            # 更新Temperature
            if 'temperature' in tts_params:
                widget = self.text_table.cellWidget(row, 5)
                if isinstance(widget, ParameterSpinBox):
                    widget.setValue(tts_params['temperature'])
                    
            # 更新Top P
            if 'top_p' in tts_params:
                widget = self.text_table.cellWidget(row, 6)
                if isinstance(widget, ParameterSpinBox):
                    widget.setValue(tts_params['top_p'])
                    
            # 更新Top K
            if 'top_k' in tts_params:
                widget = self.text_table.cellWidget(row, 7)
                if isinstance(widget, ParameterIntSpinBox):
                    widget.setValue(tts_params['top_k'])
                    
            # 更新Num Beams
            if 'num_beams' in tts_params:
                widget = self.text_table.cellWidget(row, 8)
                if isinstance(widget, ParameterIntSpinBox):
                    widget.setValue(tts_params['num_beams'])
                    
            # 更新Repetition Penalty
            if 'repetition_penalty' in tts_params:
                widget = self.text_table.cellWidget(row, 9)
                if isinstance(widget, ParameterSpinBox):
                    widget.setValue(tts_params['repetition_penalty'])
                    
            # 更新Length Penalty
            if 'length_penalty' in tts_params:
                widget = self.text_table.cellWidget(row, 10)
                if isinstance(widget, ParameterSpinBox):
                    widget.setValue(tts_params['length_penalty'])
                    
            # 更新Max Mel Tokens
            if 'max_mel_tokens' in tts_params:
                widget = self.text_table.cellWidget(row, 11)
                if isinstance(widget, ParameterIntSpinBox):
                    widget.setValue(tts_params['max_mel_tokens'])
                    
            # 更新Max Text Tokens
            if 'max_text_tokens_per_sentence' in tts_params:
                widget = self.text_table.cellWidget(row, 12)
                if isinstance(widget, ParameterIntSpinBox):
                    widget.setValue(tts_params['max_text_tokens_per_sentence'])
                    
            # 更新Bucket Size
            if 'sentences_bucket_max_size' in tts_params:
                widget = self.text_table.cellWidget(row, 13)
                if isinstance(widget, ParameterIntSpinBox):
                    widget.setValue(tts_params['sentences_bucket_max_size'])
                    
        except Exception as e:
            self.log_message(f"更新表格参数失败: {str(e)}")
            
    def play_audio_file(self, audio_path):
        """使用 pygame 播放音频文件"""
        if not audio_path or not os.path.exists(audio_path):
            MessageBox("错误", "音频文件不存在", self).exec()
            return
            
        try:
            if self.audio_player and PYGAME_PLAYER_AVAILABLE:
                # 使用 pygame 播放器
                success = self.audio_player.play_audio(audio_path)
                if not success:
                    # 如果 pygame 播放失败，回退到系统默认播放器
                    self.play_audio_with_system_player(audio_path)
            else:
                # 使用系统默认播放器
                self.play_audio_with_system_player(audio_path)
                
        except Exception as e:
            error_msg = f"播放音频失败: {str(e)}"
            self.log_message(error_msg)
            MessageBox("错误", error_msg, self).exec()
            
    def play_audio_with_system_player(self, audio_path):
        """使用系统默认播放器播放音频"""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            filename = os.path.basename(audio_path)
            
            # 显示播放提示
            InfoBar.info(
                title="正在播放音频",
                content=f"正在播放: {filename}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
            # 根据操作系统选择播放方式
            if system == "Windows":
                # Windows系统使用默认播放器
                os.startfile(audio_path)
            elif system == "Darwin":
                # macOS系统
                subprocess.run(["open", audio_path], check=True)
            else:
                # Linux系统
                subprocess.run(["xdg-open", audio_path], check=True)
                
            self.log_message(f"已播放音频文件: {filename}")
            
        except Exception as e:
            error_msg = f"播放音频失败: {str(e)}"
            self.log_message(error_msg)
            MessageBox("错误", error_msg, self).exec()
            
    def stop_audio_playback(self):
        """停止当前音频播放"""
        try:
            if self.audio_player and PYGAME_PLAYER_AVAILABLE:
                # 停止单个音频播放
                self.audio_player.stop_audio()
                # 停止批量播放
                self.audio_player.stop_batch_playback()
                
                self.log_message("已停止音频播放")
                
                InfoBar.success(
                    title="播放已停止",
                    content="音频播放已停止",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=1500,
                    parent=self
                )
            else:
                # 如果没有pygame播放器，显示提示信息
                InfoBar.warning(
                    title="无法停止播放",
                    content="pygame播放器不可用，无法停止系统播放器",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                self.log_message("pygame播放器不可用，无法停止系统播放器")
                
        except Exception as e:
            error_msg = f"停止播放失败: {str(e)}"
            self.log_message(error_msg)
            MessageBox("错误", error_msg, self).exec()
            
    def play_all_audio(self):
        """使用 pygame 逐个播放所有已转换的音频文件"""
        audio_files = []
        
        # 收集所有已转换的音频文件
        for row in range(self.text_table.rowCount()):
            status_item = self.text_table.item(row, 14)  # 转换状态列
            if status_item and status_item.text() in ["已有音频", "转换成功"]:
                # 获取音频路径
                audio_widget = self.text_table.cellWidget(row, 15)
                if audio_widget:
                    # 从音频标签获取完整路径
                    for child in audio_widget.children():
                        if isinstance(child, QLabel):
                            audio_path = child.toolTip()
                            if audio_path and os.path.exists(audio_path):
                                audio_files.append(audio_path)
                            break
                            
        if not audio_files:
            MessageBox("提示", "没有找到已转换的音频文件", self).exec()
            return
            
        # 使用 pygame 音频播放器进行批量播放
        if self.audio_player and PYGAME_PLAYER_AVAILABLE:
            # 显示播放提示
            InfoBar.info(
                title="批量播放音频",
                content=f"正在逐个播放 {len(audio_files)} 个音频文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
            self.log_message(f"开始批量播放 {len(audio_files)} 个音频文件")
            
            # 使用 pygame 播放器的批量播放功能，设置文件间延迟为1秒
            success = self.audio_player.play_audio_list(audio_files, delay_between_files=1.0)
            
            if not success:
                # 如果 pygame 播放失败，回退到系统默认播放器
                self.play_all_audio_with_system_player(audio_files)
        else:
            # 使用系统默认播放器
            self.play_all_audio_with_system_player(audio_files)
            
    def play_all_audio_with_system_player(self, audio_files):
        """使用系统默认播放器播放所有音频文件"""
        # 显示播放提示
        InfoBar.info(
            title="批量播放音频",
            content=f"正在播放 {len(audio_files)} 个音频文件",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        
        # 逐个播放音频文件
        for i, audio_path in enumerate(audio_files, 1):
            filename = os.path.basename(audio_path)
            self.log_message(f"播放音频 {i}/{len(audio_files)}: {filename}")
            
            try:
                import subprocess
                import platform
                import time
                
                system = platform.system()
                
                # 根据操作系统选择播放方式
                if system == "Windows":
                    os.startfile(audio_path)
                elif system == "Darwin":
                    subprocess.run(["open", audio_path], check=True)
                else:
                    subprocess.run(["xdg-open", audio_path], check=True)
                    
                # 等待一小段时间再播放下一个
                if i < len(audio_files):
                    time.sleep(0.5)
                    
            except Exception as e:
                self.log_message(f"播放音频失败 {filename}: {str(e)}")
                
        self.log_message(f"批量播放完成，共播放 {len(audio_files)} 个音频文件")
            
    @pyqtSlot(int, str)
    def on_progress_updated(self, progress, status):
        """进度更新"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
        
    @pyqtSlot(str, str, bool)
    def on_conversion_finished(self, text_id, output_path, success):
        """转换完成"""
        # 查找对应的行
        for row in range(self.text_table.rowCount()):
            # 从内嵌的文本编辑器获取文本ID进行比较
            text_edit = self.text_table.cellWidget(row, 1)
            if text_edit and hasattr(text_edit, 'text_id') and text_edit.text_id == text_id:
                status_item = self.text_table.item(row, 14)  # 转换状态列现在是第14列
                
                if success:
                    status_item.setText("转换成功")
                    status_item.setForeground(QColor(76, 175, 80))  # 绿色
                    
                    # 创建播放按钮和文件名显示
                    audio_widget = QWidget()
                    audio_layout = QHBoxLayout(audio_widget)
                    audio_layout.setContentsMargins(2, 2, 2, 2)
                    audio_layout.setSpacing(5)
                    
                    # 播放按钮
                    play_btn = QPushButton("▶")
                    play_btn.setFixedSize(20, 20)
                    play_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #4caf50;
                            color: white;
                            border: none;
                            border-radius: 10px;
                            font-size: 10px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #45a049;
                        }
                        QPushButton:pressed {
                            background-color: #3d8b40;
                        }
                    """)
                    play_btn.clicked.connect(lambda checked, path=output_path: self.play_audio_file(path))
                    
                    # 文件名标签
                    audio_filename = os.path.basename(output_path)
                    audio_label = QLabel(audio_filename)
                    audio_label.setStyleSheet("color: #4caf50; font-size: 11px;")
                    audio_label.setToolTip(output_path)
                    
                    audio_layout.addWidget(play_btn)
                    audio_layout.addWidget(audio_label)
                    audio_layout.addStretch()
                    
                    self.text_table.setCellWidget(row, 15, audio_widget)
                    
                    self.log_message(f"转换成功: {output_path}")
                    
                    # 更新剪映工程文件中的音频路径
                    self.update_audio_in_draft(text_id, output_path)
                else:
                    status_item.setText("转换失败")
                    status_item.setForeground(QColor(244, 67, 54))  # 红色
                    
                break
                
    @pyqtSlot(str, str)
    def on_error_occurred(self, text_id, error_message):
        """转换错误"""
        self.log_message(f"转换错误 [{text_id}]: {error_message}")
        
    @pyqtSlot()
    def on_worker_finished(self):
        """工作线程完成"""
        self.convert_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("转换完成")
        self.log_message("所有转换任务已完成")
        
        InfoBar.success(
            title="转换完成",
            content="文本转语音任务已完成",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
            
    def get_audio_duration(self, audio_path):
        """获取音频时长（微秒）"""
        try:
            # 尝试使用多种方法获取音频时长
            duration_us = None
            
            # 方法1：尝试使用wave库（适用于WAV文件）
            if audio_path.lower().endswith('.wav'):
                try:
                    import wave
                    with wave.open(audio_path, 'rb') as wav_file:
                        frames = wav_file.getnframes()
                        sample_rate = wav_file.getframerate()
                        duration_seconds = frames / float(sample_rate)
                        duration_us = int(duration_seconds * 1000000)  # 转换为微秒
                        self.log_message(f"使用wave库获取音频时长: {duration_seconds:.2f}秒")
                except Exception as e:
                    print(f"wave库获取时长失败: {e}")
            
            # 方法2：尝试使用mutagen库（支持多种格式）
            if duration_us is None:
                try:
                    from mutagen import File
                    audio_file = File(audio_path)
                    if audio_file is not None and hasattr(audio_file, 'info'):
                        duration_seconds = audio_file.info.length
                        duration_us = int(duration_seconds * 1000000)  # 转换为微秒
                        self.log_message(f"使用mutagen库获取音频时长: {duration_seconds:.2f}秒")
                except ImportError:
                    self.log_message("提示: 安装mutagen库可获得更准确的音频时长 (pip install mutagen)")
                except Exception as e:
                    print(f"mutagen库获取时长失败: {e}")
            
            # 方法3：尝试使用pydub库（备用方法）
            if duration_us is None:
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(audio_path)
                    duration_seconds = len(audio) / 1000.0  # pydub返回毫秒
                    duration_us = int(duration_seconds * 1000000)  # 转换为微秒
                    self.log_message(f"使用pydub库获取音频时长: {duration_seconds:.2f}秒")
                except ImportError:
                    self.log_message("提示: 安装pydub库可获得更准确的音频时长 (pip install pydub)")
                except Exception as e:
                    print(f"pydub库获取时长失败: {e}")
            
            # 方法4：使用文件大小估算（最后的备用方法）
            if duration_us is None:
                file_size = os.path.getsize(audio_path)
                # 粗略估算：假设是44.1kHz 16bit 单声道 WAV
                estimated_duration = int((file_size / (44100 * 2)) * 1000000)  # 转换为微秒
                duration_us = max(estimated_duration, 1000000)  # 至少1秒
                self.log_message(f"使用文件大小估算音频时长: {duration_us/1000000:.2f}秒 (建议安装音频处理库获得准确时长)")
            
            return duration_us
            
        except Exception as e:
            self.log_message(f"获取音频时长失败: {str(e)}")
            return 3000000  # 默认3秒
            
    def sync_text_audio_duration(self, text_id, audio_duration):
        """同步文本和音频的显示时长"""
        if not self.draft_data:
            return
            
        try:
            tracks = self.draft_data.get("tracks", [])
            
            # 更新文本轨道的时长
            for track in tracks:
                if track.get("type") == "text":
                    segments = track.get("segments", [])
                    for segment in segments:
                        if segment.get("material_id") == text_id:
                            if "target_timerange" not in segment:
                                segment["target_timerange"] = {}
                            # 保持开始时间不变，只更新持续时间
                            start_time = segment["target_timerange"].get("start", 0)
                            segment["target_timerange"]["duration"] = audio_duration
                            self.log_message(f"已同步文本显示时长: {audio_duration/1000000:.2f}秒")
                            break
                            
            # 更新音频轨道的时长
            for track in tracks:
                if track.get("type") == "audio":
                    segments = track.get("segments", [])
                    for segment in segments:
                        # 通过音频材料ID查找对应的音频
                        material_id = segment.get("material_id")
                        if material_id:
                            audios = self.draft_data.get("materials", {}).get("audios", [])
                            for audio in audios:
                                if audio.get("id") == material_id and audio.get("text_id") == text_id:
                                    if "target_timerange" not in segment:
                                        segment["target_timerange"] = {}
                                    segment["target_timerange"]["duration"] = audio_duration
                                    self.log_message(f"已同步音频轨道时长: {audio_duration/1000000:.2f}秒")
                                    break
                            
        except Exception as e:
            self.log_message(f"同步时长失败: {str(e)}")
            
    def add_audio_to_track(self, audio_data, text_id):
        """添加音频到轨道"""
        if not self.draft_data:
            return
            
        try:
            tracks = self.draft_data.get("tracks", [])
            
            # 查找对应的文本段，获取其时间信息
            text_segment_info = None
            for track in tracks:
                if track.get("type") == "text":
                    segments = track.get("segments", [])
                    for segment in segments:
                        if segment.get("material_id") == text_id:
                            text_segment_info = segment.get("target_timerange", {})
                            break
                    if text_segment_info:
                        break
            
            # 查找或创建音频轨道
            audio_track = None
            for track in tracks:
                if track.get("type") == "audio":
                    audio_track = track
                    break
                    
            if not audio_track:
                # 创建新的音频轨道
                audio_track = {
                    "attribute": 0,
                    "flag": 0,
                    "id": str(uuid.uuid4()).upper(),
                    "segments": [],
                    "type": "audio"
                }
                tracks.append(audio_track)
                
            # 创建音频段
            audio_segment = {
                "cartoon": False,
                "clip": {
                    "alpha": 1.0,
                    "flip": {
                        "horizontal": False,
                        "vertical": False
                    },
                    "rotation": 0.0,
                    "scale": {
                        "x": 1.0,
                        "y": 1.0
                    },
                    "transform": {
                        "x": 0.0,
                        "y": 0.0
                    }
                },
                "common_keyframes": [],
                "enable_adjust": True,
                "enable_color_curves": True,
                "enable_color_match_adjust": False,
                "enable_color_wheels": True,
                "enable_lut": True,
                "enable_smart_color_adjust": False,
                "extra_material_refs": [],
                "group_id": "",
                "hdr_settings": {
                    "intensity": 1.0,
                    "mode": 1,
                    "nits": 1000
                },
                "id": str(uuid.uuid4()).upper(),
                "intensifies_audio": False,
                "is_placeholder": False,
                "is_tone_modify": False,
                "keyframe_refs": [],
                "last_nonzero_volume": 1.0,
                "material_id": audio_data["id"],
                "render_index": 4000000,
                "reverse": False,
                "source_timerange": {
                    "duration": audio_data["duration"],
                    "start": 0
                },
                "speed": 1.0,
                "target_timerange": {
                    "duration": audio_data["duration"],
                    "start": text_segment_info.get("start", 0) if text_segment_info else 0
                },
                "template_id": "",
                "template_scene": "default",
                "track_attribute": 0,
                "track_render_index": 0,
                "uniform_scale": {
                    "on": True,
                    "value": 1.0
                },
                "visible": True,
                "volume": 1.0
            }
            
            audio_track["segments"].append(audio_segment)
            self.log_message(f"已添加音频段到轨道: {text_id}")
            
        except Exception as e:
            self.log_message(f"添加音频到轨道失败: {str(e)}")
            
    def auto_save_draft_file(self):
        """自动保存工程文件"""
        if not self.draft_file_path or not self.draft_data:
            return
            
        try:
            with open(self.draft_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.draft_data, f, ensure_ascii=False, indent=2)
            self.log_message("工程文件已自动保存")
        except Exception as e:
            self.log_message(f"自动保存失败: {str(e)}")
            
    def save_draft_file(self):
        """手动保存工程文件"""
        if not self.draft_file_path or not self.draft_data:
            MessageBox("提示", "没有加载的工程文件", self).exec()
            return
            
        try:
            with open(self.draft_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.draft_data, f, ensure_ascii=False, indent=2)
            
            InfoBar.success(
                title="保存成功",
                content="工程文件已保存",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            self.log_message("工程文件已手动保存")
        except Exception as e:
            error_msg = f"保存失败: {str(e)}"
            self.log_message(error_msg)
            MessageBox("错误", error_msg, self).exec()
            
    def open_batch_settings(self):
        """打开批量设置对话框"""
        dialog = BatchParameterDialog(self)
        if dialog.exec() == QDialog.Accepted:
            settings = dialog.get_batch_settings()
            if settings:
                self.apply_batch_settings(settings)
                
    def apply_batch_settings(self, settings):
        """应用批量设置"""
        applied_count = 0
        
        for row in range(self.text_table.rowCount()):
            checkbox = self.text_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                # 从内嵌的文本编辑器获取文本ID
                text_edit = self.text_table.cellWidget(row, 1)
                if not text_edit or not hasattr(text_edit, 'text_id'):
                    continue
                text_id = text_edit.text_id
                
                # 应用参考音频设置
                if 'reference_voice' in settings:
                    self.text_configs[text_id]['reference_voice'] = settings['reference_voice']
                    audio_preview = self.text_table.cellWidget(row, 2)
                    if audio_preview:
                        audio_preview.set_audio_path(settings['reference_voice'])
                
                # 应用推理模式设置
                if 'infer_mode' in settings:
                    self.text_configs[text_id]['infer_mode'] = settings['infer_mode']
                    mode_item = self.text_table.item(row, 3)
                    if mode_item:
                        mode_item.setText(settings['infer_mode'])
                
                # 应用TTS参数设置
                if 'tts_params' in settings:
                    for param_name, param_value in settings['tts_params'].items():
                        self.text_configs[text_id]['tts_params'][param_name] = param_value
                        
                        # 更新表格中的对应控件
                        if param_name == 'do_sample':
                            widget = self.text_table.cellWidget(row, 4)
                            if widget:
                                widget.setChecked(param_value)
                        elif param_name == 'temperature':
                            widget = self.text_table.cellWidget(row, 5)
                            if widget:
                                widget.setValue(param_value)
                        elif param_name == 'top_p':
                            widget = self.text_table.cellWidget(row, 6)
                            if widget:
                                widget.setValue(param_value)
                        elif param_name == 'top_k':
                            widget = self.text_table.cellWidget(row, 7)
                            if widget:
                                widget.setValue(param_value)
                        elif param_name == 'num_beams':
                            widget = self.text_table.cellWidget(row, 8)
                            if widget:
                                widget.setValue(param_value)
                        elif param_name == 'repetition_penalty':
                            widget = self.text_table.cellWidget(row, 9)
                            if widget:
                                widget.setValue(param_value)
                        elif param_name == 'length_penalty':
                            widget = self.text_table.cellWidget(row, 10)
                            if widget:
                                widget.setValue(param_value)
                        elif param_name == 'max_mel_tokens':
                            widget = self.text_table.cellWidget(row, 11)
                            if widget:
                                widget.setValue(param_value)
                        elif param_name == 'max_text_tokens_per_sentence':
                            widget = self.text_table.cellWidget(row, 12)
                            if widget:
                                widget.setValue(param_value)
                        elif param_name == 'sentences_bucket_max_size':
                            widget = self.text_table.cellWidget(row, 13)
                            if widget:
                                widget.setValue(param_value)
                
                applied_count += 1
        
        InfoBar.success(
            title="批量设置完成",
            content=f"已对 {applied_count} 个文本应用设置",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
        self.log_message(f"批量设置已应用到 {applied_count} 个文本")
        
    def calculate_total_duration(self):
        """计算工程文件的总时长（微秒）"""
        if not self.draft_data:
            return 0
            
        tracks = self.draft_data.get("tracks", [])
        max_end_time = 0
        
        # 遍历所有轨道，找到最晚的结束时间
        for track in tracks:
            segments = track.get("segments", [])
            for segment in segments:
                timerange = segment.get("target_timerange", {})
                start_time = timerange.get("start", 0)
                duration = timerange.get("duration", 0)
                end_time = start_time + duration
                max_end_time = max(max_end_time, end_time)
        
        return max_end_time
        
    def update_project_duration(self):
        """更新工程文件的总时长"""
        if not self.draft_data:
            return
            
        total_duration = self.calculate_total_duration()
        if total_duration > 0:
            self.draft_data["duration"] = total_duration
            self.log_message(f"已更新工程文件总时长: {total_duration/1000000:.2f}秒 ({total_duration}微秒)")
            

            
