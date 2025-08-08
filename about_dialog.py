import os
import webbrowser
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QGridLayout, QScrollArea
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QCursor
from qfluentwidgets import MessageBox, PushButton, setTheme, Theme

class ClickableLinkLabel(QLabel):
    """可点击的链接标签"""
    def __init__(self, text, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.setText(text)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip(f"点击访问：{url}")
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setStyleSheet("""
            ClickableLinkLabel {
                color: #1976d2;
                font-size: 12px;
                margin-bottom: 10px;
                text-decoration: underline;
                padding: 5px;
                border-radius: 4px;
            }
            ClickableLinkLabel:hover {
                background-color: #e3f2fd;
                color: #0d47a1;
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            webbrowser.open(self.url)

class ClickableQRLabel(QLabel):
    """可点击放大的二维码标签"""
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.original_pixmap = None
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip("点击放大查看")
        
        # 加载图片
        if os.path.exists(image_path):
            self.original_pixmap = QPixmap(image_path)
            scaled_pixmap = self.original_pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
        else:
            self.setText("QR码未找到")
            self.setStyleSheet("color: #999999; border: 1px dashed #ccc; width: 180px; height: 180px;")
        
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            ClickableQRLabel {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                background-color: #fafafa;
            }
            ClickableQRLabel:hover {
                border: 2px solid #1976d2;
                background-color: #f5f5f5;
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.original_pixmap:
            self.show_enlarged_image()
    
    def show_enlarged_image(self):
        """显示放大的图片"""
        dialog = QDialog(self)
        dialog.setWindowTitle("二维码")
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 放大的图片
        img_label = QLabel()
        enlarged_pixmap = self.original_pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img_label.setPixmap(enlarged_pixmap)
        img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(img_label)
        
        # 关闭按钮
        close_btn = PushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        close_btn.setFixedWidth(100)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.resize(450, 500)
        dialog.exec_()

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setFixedSize(800, 700)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # 强制使用浅色主题
        setTheme(Theme.LIGHT)
        
        self.init_ui()
        
    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
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
        
        # 创建滚动内容容器
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(25)
        scroll_layout.setContentsMargins(40, 40, 40, 20)
        
        # 标题
        title_label = QLabel("剪映工程文件编辑器")
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #1976d2; margin-bottom: 15px;")
        scroll_layout.addWidget(title_label)
        
        # 描述
        desc_label = QLabel("一个用于编辑剪映工程文件的工具，支持文本编辑和语音合成功能。")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666666; font-size: 15px; margin-bottom: 25px; line-height: 1.5;")
        scroll_layout.addWidget(desc_label)
        
        # 交流群信息标题
        group_label = QLabel("加入我们的交流群")
        group_label.setAlignment(Qt.AlignCenter)
        group_font = QFont()
        group_font.setPointSize(16)
        group_font.setBold(True)
        group_label.setFont(group_font)
        group_label.setStyleSheet("color: #333333; margin-bottom: 20px;")
        scroll_layout.addWidget(group_label)
        
        # 使用网格布局来放置三个平台
        groups_layout = QGridLayout()
        groups_layout.setSpacing(20)
        groups_layout.setContentsMargins(10, 0, 10, 0)
        
        # QQ群组
        qq_widget = QWidget()
        qq_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        qq_layout = QVBoxLayout(qq_widget)
        qq_layout.setSpacing(12)
        qq_layout.setAlignment(Qt.AlignCenter)
        
        qq_title = QLabel("QQ交流群")
        qq_title_font = QFont()
        qq_title_font.setPointSize(13)
        qq_title_font.setBold(True)
        qq_title.setFont(qq_title_font)
        qq_title.setAlignment(Qt.AlignCenter)
        qq_title.setStyleSheet("color: #333333; margin-bottom: 5px;")
        qq_layout.addWidget(qq_title)
        
        qq_number = QLabel("群号：700598581")
        qq_number.setAlignment(Qt.AlignCenter)
        qq_number.setStyleSheet("color: #666666; font-size: 12px; margin-bottom: 8px;")
        qq_layout.addWidget(qq_number)
        
        # QQ二维码 - 使用可点击组件，调整大小
        qq_qr_path = os.path.join("static", "QQ.jpg")
        qq_qr_label = ClickableQRLabel(qq_qr_path)
        # 重新设置QQ二维码大小
        if os.path.exists(qq_qr_path):
            pixmap = QPixmap(qq_qr_path)
            scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            qq_qr_label.setPixmap(scaled_pixmap)
        qq_layout.addWidget(qq_qr_label, 0, Qt.AlignCenter)
        
        # Telegram群组
        tg_widget = QWidget()
        tg_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        tg_layout = QVBoxLayout(tg_widget)
        tg_layout.setSpacing(12)
        tg_layout.setAlignment(Qt.AlignCenter)
        
        tg_title = QLabel("Telegram交流群")
        tg_title_font = QFont()
        tg_title_font.setPointSize(13)
        tg_title_font.setBold(True)
        tg_title.setFont(tg_title_font)
        tg_title.setAlignment(Qt.AlignCenter)
        tg_title.setStyleSheet("color: #333333; margin-bottom: 5px;")
        tg_layout.addWidget(tg_title)
        
        # 使用可点击的链接
        tg_link = ClickableLinkLabel("https://t.me/+4QnanwbKUZNhZjc1", "https://t.me/+4QnanwbKUZNhZjc1")
        tg_layout.addWidget(tg_link)
        
        # Telegram二维码 - 使用可点击组件，调整大小
        tg_qr_path = os.path.join("static", "telegram.png")
        tg_qr_label = ClickableQRLabel(tg_qr_path)
        # 重新设置Telegram二维码大小
        if os.path.exists(tg_qr_path):
            pixmap = QPixmap(tg_qr_path)
            scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            tg_qr_label.setPixmap(scaled_pixmap)
        tg_layout.addWidget(tg_qr_label, 0, Qt.AlignCenter)
        
        # 哔哩哔哩 - 特别设计，突出显示
        bili_widget = QWidget()
        bili_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #e3f2fd, stop:1 #f8f9fa);
                border: 2px solid #00a1d6;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        bili_layout = QVBoxLayout(bili_widget)
        bili_layout.setSpacing(15)
        bili_layout.setAlignment(Qt.AlignCenter)
        
        # 哔哩哔哩标题和引导文字
        bili_title = QLabel("🎬 哔哩哔哩")
        bili_title_font = QFont()
        bili_title_font.setPointSize(15)
        bili_title_font.setBold(True)
        bili_title.setFont(bili_title_font)
        bili_title.setAlignment(Qt.AlignCenter)
        bili_title.setStyleSheet("color: #00a1d6; margin-bottom: 5px;")
        bili_layout.addWidget(bili_title)
        
        # 引导文字
        bili_guide = QLabel("关注UP主，获取最新教程和更新！")
        bili_guide.setAlignment(Qt.AlignCenter)
        bili_guide.setStyleSheet("color: #333333; font-size: 13px; font-weight: bold; margin-bottom: 5px;")
        bili_layout.addWidget(bili_guide)
        
        # 一键三连提示
        bili_action = QLabel("👍 点赞 | 🔔 关注 | ⭐ 收藏")
        bili_action.setAlignment(Qt.AlignCenter)
        bili_action.setStyleSheet("""
            color: #ff6b6b; 
            font-size: 14px; 
            font-weight: bold; 
            background-color: rgba(255, 255, 255, 0.8);
            border-radius: 8px;
            padding: 8px;
            margin-bottom: 10px;
        """)
        bili_layout.addWidget(bili_action)
        
        # 使用可点击的链接
        bili_link = ClickableLinkLabel("🔗 点击访问我的B站主页", "https://space.bilibili.com/519965290")
        bili_link.setStyleSheet("""
            ClickableLinkLabel {
                color: #00a1d6;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 10px;
                text-decoration: underline;
                padding: 8px;
                border-radius: 6px;
                background-color: rgba(255, 255, 255, 0.9);
            }
            ClickableLinkLabel:hover {
                background-color: #ffffff;
                color: #0066cc;
                transform: scale(1.05);
            }
        """)
        bili_layout.addWidget(bili_link)
        
        # 哔哩哔哩图标
        bili_icon = QLabel("📺")
        bili_icon.setAlignment(Qt.AlignCenter)
        bili_icon.setStyleSheet("""
            QLabel {
                font-size: 100px;
                color: #00a1d6;
                background-color: #ffffff;
                border: 3px solid #00a1d6;
                border-radius: 12px;
                padding: 25px;
                margin: 15px;
                width: 180px;
                height: 180px;
            }
        """)
        bili_layout.addWidget(bili_icon, 0, Qt.AlignCenter)
        
        # 将三个平台添加到网格布局 - 第一行放QQ和Telegram，第二行放哔哩哔哩
        groups_layout.addWidget(qq_widget, 0, 0)
        groups_layout.addWidget(tg_widget, 0, 1)
        groups_layout.addWidget(bili_widget, 1, 0, 1, 2)  # 跨两列
        
        scroll_layout.addLayout(groups_layout)
        
        # 添加一些额外的空间
        scroll_layout.addSpacing(30)
        
        # 感谢文字
        thanks_label = QLabel("感谢您的使用和支持！🙏")
        thanks_label.setAlignment(Qt.AlignCenter)
        thanks_font = QFont()
        thanks_font.setPointSize(14)
        thanks_font.setBold(True)
        thanks_label.setFont(thanks_font)
        thanks_label.setStyleSheet("color: #666666; margin: 20px 0;")
        scroll_layout.addWidget(thanks_label)
        
        # 设置滚动区域内容
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # 关闭按钮 - 固定在底部
        close_btn = PushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(120)
        close_btn.setStyleSheet("""
            PushButton {
                font-size: 14px;
                padding: 10px 20px;
                border-radius: 6px;
                margin: 10px;
            }
        """)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        btn_layout.setContentsMargins(0, 10, 0, 20)
        
        main_layout.addLayout(btn_layout)
        
        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                background-color: transparent;
            }
        """)