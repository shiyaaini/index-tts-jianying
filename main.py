import sys
import json
import os

# 添加当前目录到Python模块搜索路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 确保当前工作目录是项目根目录
os.chdir(current_dir)

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QIcon
from qfluentwidgets import (FluentIcon, NavigationInterface, NavigationItemPosition, 
                           MessageBox, setTheme, Theme, PushButton, LineEdit, 
                           ComboBox, SpinBox, ColorPickerButton, TextEdit)

from config_manager import ConfigManager
from text_editor import TextEditor
from project_manager import ProjectManager
from tts_manager import TTSManager
from multi_voice_tts_manager import MultiVoiceTTSManager
from frame_interpolation_manager import FrameInterpolationManager
from video_extraction_manager import VideoExtractionManager
from about_dialog import AboutDialog

# 在QApplication创建之前设置高DPI缩放
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.project_manager = ProjectManager(self.config_manager)
        self.text_editor = TextEditor()
        self.tts_manager = TTSManager()
        self.multi_voice_tts_manager = MultiVoiceTTSManager()
        self.frame_interpolation_manager = FrameInterpolationManager()
        self.video_extraction_manager = VideoExtractionManager()
        
        self.setWindowTitle("剪映工程文件编辑器")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), "static", "favicon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.init_ui()
        self.setup_theme()
        
    def setup_theme(self):
        """设置主题和样式"""
        # 强制使用浅色主题
        setTheme(Theme.LIGHT)
        
        # 设置应用程序样式表
        app = QApplication.instance()
        if app:
            app.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                }
                QWidget {
                    background-color: #ffffff;
                    color: #333333;
                }
                QListWidget {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                }
                QListWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #f0f0f0;
                }
                QListWidget::item:selected {
                    background-color: #e3f2fd;
                    color: #1976d2;
                }
                QListWidget::item:hover {
                    background-color: #f5f5f5;
                }
                QLineEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 6px;
                }
                QLineEdit:focus {
                    border: 2px solid #1976d2;
                }
                QPushButton {
                    background-color: #1976d2;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
                QPushButton:pressed {
                    background-color: #0d47a1;
                }
                QSpinBox, QDoubleSpinBox {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 4px;
                }
                QComboBox {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 6px;
                }
                QLabel {
                    color: #333333;
                    font-weight: bold;
                }
                QFormLayout QLabel {
                    color: #555555;
                }
            """)
        
    def init_ui(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建导航界面
        self.navigation = NavigationInterface(self, showMenuButton=True)
        self.navigation.addItem(
            routeKey='project',
            icon=FluentIcon.FOLDER,
            text='项目管理',
            onClick=self.show_project_manager
        )
        self.navigation.addItem(
            routeKey='text',
            icon=FluentIcon.EDIT,
            text='文字编辑',
            onClick=self.show_text_editor
        )
        self.navigation.addItem(
            routeKey='tts',
            icon=FluentIcon.MICROPHONE,
            text='文本转语音',
            onClick=self.show_tts_manager
        )
        self.navigation.addItem(
            routeKey='multi_voice_tts',
            icon=FluentIcon.PEOPLE,
            text='多人语音合成',
            onClick=self.show_multi_voice_tts_manager
        )
        self.navigation.addItem(
            routeKey='frame_interpolation',
            icon=FluentIcon.VIDEO,
            text='插帧算法补偿',
            onClick=self.show_frame_interpolation_manager
        )
        self.navigation.addItem(
            routeKey='video_extraction',
            icon=FluentIcon.MUSIC,
            text='视频提取音频',
            onClick=self.show_video_extraction_manager
        )
        
        # 添加关于页面到底部
        self.navigation.addItem(
            routeKey='about',
            icon=FluentIcon.INFO,
            text='关于',
            onClick=self.show_about_dialog,
            position=NavigationItemPosition.BOTTOM
        )
        
        # 连接信号
        self.project_manager.project_selected.connect(self.text_editor.load_draft_file)
        self.project_manager.project_selected.connect(self.tts_manager.load_draft_file)
        self.project_manager.project_selected.connect(lambda: self.show_text_editor())
        
        # 添加到布局
        main_layout.addWidget(self.navigation, 0)
        main_layout.addWidget(self.project_manager, 1)
        main_layout.addWidget(self.text_editor, 1)
        main_layout.addWidget(self.tts_manager, 1)
        main_layout.addWidget(self.multi_voice_tts_manager, 1)
        main_layout.addWidget(self.frame_interpolation_manager, 1)
        main_layout.addWidget(self.video_extraction_manager, 1)
        
        # 初始显示项目管理
        self.show_project_manager()
        
    def show_project_manager(self):
        self.project_manager.show()
        self.text_editor.hide()
        self.tts_manager.hide()
        self.multi_voice_tts_manager.hide()
        self.frame_interpolation_manager.hide()
        self.video_extraction_manager.hide()
        
    def show_text_editor(self):
        self.project_manager.hide()
        self.text_editor.show()
        self.tts_manager.hide()
        self.multi_voice_tts_manager.hide()
        self.frame_interpolation_manager.hide()
        self.video_extraction_manager.hide()
        
    def show_tts_manager(self):
        self.project_manager.hide()
        self.text_editor.hide()
        self.tts_manager.show()
        self.multi_voice_tts_manager.hide()
        self.frame_interpolation_manager.hide()
        self.video_extraction_manager.hide()
        
    def show_multi_voice_tts_manager(self):
        self.project_manager.hide()
        self.text_editor.hide()
        self.tts_manager.hide()
        self.multi_voice_tts_manager.show()
        self.frame_interpolation_manager.hide()
        self.video_extraction_manager.hide()
        
    def show_frame_interpolation_manager(self):
        self.project_manager.hide()
        self.text_editor.hide()
        self.tts_manager.hide()
        self.multi_voice_tts_manager.hide()
        self.frame_interpolation_manager.show()
        self.video_extraction_manager.hide()
        
    def show_video_extraction_manager(self):
        self.project_manager.hide()
        self.text_editor.hide()
        self.tts_manager.hide()
        self.multi_voice_tts_manager.hide()
        self.frame_interpolation_manager.hide()
        self.video_extraction_manager.show()
        
    def show_about_dialog(self):
        """显示关于对话框"""
        about_dialog = AboutDialog(self)
        about_dialog.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    icon_path = os.path.join(os.path.dirname(__file__), "static", "favicon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())