import os
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPalette, QColor
from qfluentwidgets import (PushButton, LineEdit, MessageBox, InfoBar, InfoBarPosition,
                           CardWidget, BodyLabel, StrongBodyLabel, FluentIcon)

class ProjectManager(QWidget):
    project_selected = pyqtSignal(str)  # 项目选择信号
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.init_ui()
        self.load_projects()
        self.setup_styles()
        
    def setup_styles(self):
        """设置组件样式"""
        self.setStyleSheet("""
            ProjectManager {
                background-color: #ffffff;
                color: #333333;
            }
            CardWidget {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin: 8px;
            }
            StrongBodyLabel {
                color: #1976d2;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 8px;
            }
            BodyLabel {
                color: #555555;
                font-size: 14px;
            }
            QListWidget {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
                color: #333333;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 项目目录设置
        dir_card = CardWidget()
        dir_layout = QVBoxLayout(dir_card)
        dir_layout.setContentsMargins(16, 16, 16, 16)
        
        dir_layout.addWidget(StrongBodyLabel("项目目录设置"))
        
        dir_input_layout = QHBoxLayout()
        self.dir_input = LineEdit()
        self.dir_input.setPlaceholderText("剪映项目目录路径")
        self.dir_input.setText(self.config_manager.get("project_directory", ""))
        self.dir_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #1976d2;
            }
        """)
        self.auto_get_path = PushButton(FluentIcon.FOLDER, "自动获取")
        self.auto_get_path.clicked.connect(self.check_jianying_path)
        self.auto_get_path.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        
        self.browse_btn = PushButton(FluentIcon.FOLDER, "浏览")
        self.browse_btn.clicked.connect(self.browse_directory)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        
        self.save_dir_btn = PushButton(FluentIcon.SAVE, "保存")
        self.save_dir_btn.clicked.connect(self.save_directory)
        self.save_dir_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        dir_input_layout.addWidget(self.dir_input, 1)
        dir_input_layout.addWidget(self.auto_get_path)
        dir_input_layout.addWidget(self.browse_btn)
        dir_input_layout.addWidget(self.save_dir_btn)
        
        dir_layout.addLayout(dir_input_layout)
        layout.addWidget(dir_card)
        
        # 项目列表
        project_card = CardWidget()
        project_layout = QVBoxLayout(project_card)
        project_layout.setContentsMargins(16, 16, 16, 16)
        
        project_layout.addWidget(StrongBodyLabel("项目列表"))
        
        self.project_list = QListWidget()
        self.project_list.itemDoubleClicked.connect(self.open_project)
        self.project_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f0f0f0;
                color: #333333;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        project_layout.addWidget(self.project_list)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        self.refresh_btn = PushButton(FluentIcon.SYNC, "刷新")
        self.refresh_btn.clicked.connect(self.load_projects)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
            QPushButton:pressed {
                background-color: #ef6c00;
            }
        """)
        
        self.open_btn = PushButton(FluentIcon.FOLDER, "打开项目")
        self.open_btn.clicked.connect(self.open_selected_project)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.open_btn)
        btn_layout.addStretch()
        
        project_layout.addLayout(btn_layout)
        layout.addWidget(project_card)

    def check_jianying_path(self):
        # 获取当前用户的AppData目录
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            print("config.json不存在，正在创建")
            config = {
                  "project_directory": "",
                  "current_project": "",
                  "recent_projects": [
                  ],
                  "theme": "auto",
                  "auto_backup": True
                }
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        try:
            appdata_path = os.getenv('LOCALAPPDATA')
            if not appdata_path:
                return False

            # 构造剪映项目路径
            jianying_path = os.path.join(
                appdata_path,
                'JianyingPro',
                'User Data',
                'Projects',
                'com.lveditor.draft'
            )

            # 检查路径是否存在
            config["project_directory"] = jianying_path
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            self.dir_input.setText(jianying_path)
            return os.path.exists(jianying_path)
        except:
            print("Windown没有该目录,若是其他系统,请自行在填写网页中填写")
        
    def browse_directory(self):
        """浏览目录"""
        from PyQt5.QtWidgets import QFileDialog
        directory = QFileDialog.getExistingDirectory(self, "选择剪映项目目录")
        if directory:
            self.dir_input.setText(directory)
            
    def save_directory(self):
        """保存目录设置"""
        directory = self.dir_input.text().strip()
        if directory and os.path.exists(directory):
            self.config_manager.set("project_directory", directory)
            InfoBar.success(
                title="保存成功",
                content="项目目录已保存",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            #清空config.json中recent_projects
            self.config_manager.set("recent_projects", [])
            self.load_projects()
        else:
            MessageBox("错误", "请输入有效的目录路径", self).exec()
            
    def load_projects(self):
        """加载项目列表"""
        self.project_list.clear()
        project_dir = self.config_manager.get("project_directory", "")
        
        if not project_dir or not os.path.exists(project_dir):
            return
            
        try:
            for item in os.listdir(project_dir):
                item_path = os.path.join(project_dir, item)
                if os.path.isdir(item_path):
                    draft_file = os.path.join(item_path, "draft_content.json")
                    if os.path.exists(draft_file):
                        list_item = QListWidgetItem(item)
                        list_item.setData(Qt.UserRole, item_path)
                        self.project_list.addItem(list_item)
        except Exception as e:
            MessageBox("错误", f"加载项目列表失败: {str(e)}", self).exec()
            
    def open_project(self, item):
        """双击打开项目"""
        project_path = item.data(Qt.UserRole)
        self.open_project_by_path(project_path)
        
    def open_selected_project(self):
        """打开选中的项目"""
        current_item = self.project_list.currentItem()
        if current_item:
            project_path = current_item.data(Qt.UserRole)
            self.open_project_by_path(project_path)
        else:
            MessageBox("提示", "请先选择一个项目", self).exec()
            
    def open_project_by_path(self, project_path):
        """根据路径打开项目"""
        draft_file = os.path.join(project_path, "draft_content.json")
        if os.path.exists(draft_file):
            self.config_manager.set("current_project", project_path)
            self.config_manager.add_recent_project(project_path)
            self.project_selected.emit(draft_file)
            InfoBar.success(
                title="项目已打开",
                content=f"已打开项目: {os.path.basename(project_path)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        else:
            MessageBox("错误", "项目文件不存在", self).exec()