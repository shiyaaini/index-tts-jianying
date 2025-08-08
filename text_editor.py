import json
import os
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QCheckBox,
                             QInputDialog, QColorDialog, QAbstractItemView,
                             QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit,
                             QDialog, QListWidget, QListWidgetItem, QLabel,
                             QScrollArea, QFrame, QGraphicsView, QGraphicsScene,
                             QGraphicsTextItem, QGraphicsRectItem, QFileDialog,
                             QTextEdit, QPlainTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QColor, QFont, QFontDatabase, QPen, QBrush, QTransform, QFontMetrics
from qfluentwidgets import (CardWidget, StrongBodyLabel, BodyLabel,
                           ColorPickerButton, PushButton, MessageBox, InfoBar, InfoBarPosition,
                           FluentIcon)

class ColorDisplayWidget(QWidget):
    """颜色显示组件，用于在字体颜色列中显示颜色"""
    
    def __init__(self, color_array=None, parent=None):
        super().__init__(parent)
        self.color_array = color_array or [0.13, 0.63, 0.24]  # 默认绿色
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # 颜色方块
        self.color_label = QLabel()
        self.color_label.setFixedSize(20, 20)
        self.color_label.setStyleSheet("border: 1px solid #d0d0d0; border-radius: 3px;")
        layout.addWidget(self.color_label)
        
        # 颜色文本
        self.text_label = QLabel()
        self.text_label.setStyleSheet("font-size: 12px; color: #333333;")
        layout.addWidget(self.text_label)
        
        layout.addStretch()
        self.update_color()
        
    def update_color(self):
        """更新颜色显示"""
        if self.color_array and len(self.color_array) >= 3:
            try:
                color = QColor(
                    int(self.color_array[0] * 255),
                    int(self.color_array[1] * 255),
                    int(self.color_array[2] * 255)
                )
                if color.isValid():
                    # 更新颜色方块
                    self.color_label.setStyleSheet(f"""
                        background-color: rgb({color.red()}, {color.green()}, {color.blue()});
                        border: 1px solid #d0d0d0;
                        border-radius: 3px;
                    """)
                    
                    # 更新颜色文本
                    self.text_label.setText(f"RGB({color.red()}, {color.green()}, {color.blue()})")
                else:
                    self.set_default_color()
            except (ValueError, TypeError, IndexError):
                self.set_default_color()
        else:
            self.set_default_color()
            
    def set_default_color(self):
        """设置默认颜色"""
        self.color_label.setStyleSheet("""
            background-color: rgb(34, 162, 62);
            border: 1px solid #d0d0d0;
            border-radius: 3px;
        """)
        self.text_label.setText("RGB(34, 162, 62)")
        
    def set_color(self, color_array):
        """设置颜色"""
        self.color_array = color_array
        self.update_color()
        
    def get_color(self):
        """获取颜色数组"""
        return self.color_array

class MultiLineTextEdit(QTextEdit):
    """多行文本编辑器，用于表格中的文本编辑"""
    
    def __init__(self, text="", text_id="", text_editor=None, parent=None):
        super().__init__(parent)
        self.text_id = text_id
        self.text_editor = text_editor  # 保存对TextEditor实例的引用
        self._updating = False
        
        # 设置更大的字体和样式
        self.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 10px;
                font-size: 16px;
                font-family: 'Microsoft YaHei', 'SimHei', sans-serif;
                background-color: #ffffff;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #2196f3;
                background-color: #f8f9fa;
            }
        """)
        
        # 设置文本内容
        self.setPlainText(text)
        
        # 设置文本编辑器属性
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().Expanding)
        
        # 连接信号
        self.textChanged.connect(self.on_text_changed)
        self.document().contentsChanged.connect(self.adjust_height)
        
        # 初始化时延迟调整高度，确保文档已完全加载
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(50, self.initial_adjust_height)
        
    def initial_adjust_height(self):
        """初始化时调整高度"""
        self.adjust_height()
        
    def on_text_changed(self):
        """文本改变时发出信号"""
        if not self._updating and self.text_editor:
            # 使用保存的text_editor引用，传递文本ID和内容
            if hasattr(self.text_editor, 'on_text_content_changed'):
                self.text_editor.on_text_content_changed(self.text_id, self.toPlainText())
                
    def adjust_height(self):
        """根据内容自动调整高度"""
        # 计算文档的理想高度
        doc_height = self.document().size().height()
        # 添加一些边距
        margins = self.contentsMargins()
        total_height = int(doc_height + margins.top() + margins.bottom() + 20)
        
        # 设置最小和最大高度限制 - 适应更大字体
        min_height = 80   # 增加最小高度
        max_height = 300  # 增加最大高度
        
        # 限制高度范围
        final_height = max(min_height, min(max_height, total_height))
        
        # 只有当高度发生变化时才调整
        if self.height() != final_height:
            self.setFixedHeight(final_height)
            # 通知父表格调整行高
            parent = self.parent()
            while parent:
                if hasattr(parent, 'resizeRowsToContents'):
                    parent.resizeRowsToContents()
                    break
                parent = parent.parent()
            
    def setPlainText(self, text):
        """重写setPlainText方法，避免触发信号"""
        self._updating = True
        super().setPlainText(text)
        self._updating = False
        
    def get_text(self):
        """获取文本内容"""
        return self.toPlainText()
        
    def set_text(self, text):
        """设置文本内容"""
        self.setPlainText(text)

class MultiLineTextEditDialog(QDialog):
    """多行文本编辑对话框"""
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.original_text = text
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("编辑文本内容")
        self.setMinimumSize(500, 400)
        self.resize(600, 450)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("编辑文本内容")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976d2; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 说明文字
        info_label = QLabel("提示：支持多行文本，按 Enter 键换行")
        info_label.setStyleSheet("color: #666666; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # 文本编辑区域
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.original_text)
        self.text_edit.setFont(QFont("Microsoft YaHei", 12))
        self.text_edit.setMinimumHeight(250)
        layout.addWidget(self.text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = PushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setFixedSize(80, 35)
        
        self.cancel_button = PushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setFixedSize(80, 35)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # 设置样式
        self.setStyleSheet("""
            MultiLineTextEditDialog {
                background-color: #ffffff;
            }
            QTextEdit {
                border: 2px solid #d0d0d0;
                border-radius: 6px;
                padding: 10px;
                font-size: 12px;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #2196f3;
            }
            QPushButton {
                background-color: #2196f3;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        
    def get_text(self):
        """获取编辑后的文本"""
        return self.text_edit.toPlainText()

class WrappedTextTableItem(QTableWidgetItem):
    """支持自动换行的表格项"""
    
    def __init__(self, text=""):
        super().__init__(text)
        self.setFlags(self.flags() | Qt.ItemIsEditable)
        self.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        # 启用自动换行
        self.setData(Qt.UserRole, True)
        
    def paint(self, painter, option, index):
        """自定义绘制方法，支持文本换行"""
        # 获取单元格矩形
        rect = option.rect
        text = self.text()
        
        if not text:
            return
            
        # 设置绘制选项
        painter.save()
        
        # 设置字体
        font = self.font()
        if not font:
            font = painter.font()
        painter.setFont(font)
        
        # 设置文本颜色
        if option.state & Qt.ItemIsSelected:
            painter.setPen(QColor("#1976d2"))
        else:
            painter.setPen(QColor("#000000"))
        
        # 计算文本换行
        text_rect = rect.adjusted(8, 8, -8, -8)  # 留出边距
        wrapped_text = self.wrap_text(text, text_rect.width(), painter.font())
        
        # 绘制文本
        painter.drawText(text_rect, Qt.AlignTop | Qt.AlignLeft | Qt.TextWordWrap, wrapped_text)
        
        painter.restore()
        
    def wrap_text(self, text, max_width, font):
        """将文本按宽度换行"""
        if not text or max_width <= 0:
            return text
            
        # 创建字体度量对象
        fm = QFontMetrics(font)
        
        # 如果文本宽度小于最大宽度，直接返回
        if fm.horizontalAdvance(text) <= max_width:
            return text
            
        # 按字符分割文本
        words = list(text)
        lines = []
        current_line = ""
        
        for char in words:
            test_line = current_line + char
            if fm.horizontalAdvance(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = char
                else:
                    # 单个字符就超宽，强制换行
                    lines.append(char)
                    current_line = ""
        
        if current_line:
            lines.append(current_line)
            
        return "\n".join(lines) if lines else text

class SmartTextAddDialog(QDialog):
    """智能文本添加对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.text_segments = []
        self.char_duration = 300  # 每个字符的默认显示时长（毫秒）
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("智能添加文本")
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("智能添加文本")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 输入区域
        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.Box)
        input_frame.setStyleSheet("QFrame { border: 1px solid #d0d0d0; border-radius: 6px; padding: 15px; }")
        input_layout = QVBoxLayout(input_frame)
        
        # 原始文本输入
        input_layout.addWidget(QLabel("输入文本内容:"))
        self.text_input = QTextEdit()
        self.text_input.setMinimumHeight(120)
        self.text_input.setPlaceholderText("请输入要分句的文本内容...")
        input_layout.addWidget(self.text_input)
        
        # 分句设置
        settings_layout = QHBoxLayout()
        
        # 分句符号设置
        settings_layout.addWidget(QLabel("分句符号:"))
        self.punctuation_input = QLineEdit("，。！；？")
        self.punctuation_input.setFixedWidth(120)
        self.punctuation_input.setToolTip("用于分句的标点符号，不需要分隔")
        settings_layout.addWidget(self.punctuation_input)
        
        # 字符时长设置
        settings_layout.addWidget(QLabel("每字时长(ms):"))
        self.char_duration_spin = QSpinBox()
        self.char_duration_spin.setRange(100, 2000)
        self.char_duration_spin.setValue(self.char_duration)
        self.char_duration_spin.setFixedWidth(80)
        self.char_duration_spin.valueChanged.connect(self.on_char_duration_changed)
        settings_layout.addWidget(self.char_duration_spin)
        
        # 文本间隔设置
        settings_layout.addWidget(QLabel("文本间隔(ms):"))
        self.text_gap_spin = QSpinBox()
        self.text_gap_spin.setRange(0, 1000)
        self.text_gap_spin.setValue(20)  # 默认20ms间隔
        self.text_gap_spin.setFixedWidth(80)
        self.text_gap_spin.setToolTip("文本之间的间隔时间，避免重叠显示")
        settings_layout.addWidget(self.text_gap_spin)
        
        # 分句按钮
        self.split_button = PushButton("分句预览")
        self.split_button.clicked.connect(self.split_text)
        self.split_button.setFixedSize(100, 35)
        settings_layout.addWidget(self.split_button)
        
        settings_layout.addStretch()
        input_layout.addLayout(settings_layout)
        
        layout.addWidget(input_frame)
        
        # 预览表格
        preview_label = QLabel("分句预览:")
        preview_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        layout.addWidget(preview_label)
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(4)
        self.preview_table.setHorizontalHeaderLabels(["文本内容", "字符数", "显示时长(ms)", "操作"])
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.preview_table.horizontalHeader().setStretchLastSection(False)
        
        # 设置列宽，文本内容列使用弹性宽度
        self.preview_table.setColumnWidth(0, 350)  # 减少文本列宽度，为换行留出空间
        self.preview_table.setColumnWidth(1, 80)
        self.preview_table.setColumnWidth(2, 120)
        self.preview_table.setColumnWidth(3, 150)
        
        # 设置表格支持自动换行
        self.preview_table.setWordWrap(True)
        self.preview_table.setTextElideMode(Qt.ElideRight)
        
        # 设置表格样式
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f8f9fa;
                gridline-color: #e0e0e0;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
                word-wrap: break-word;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #000000;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        
        # 设置表格大小策略，让文本列能够自适应
        self.preview_table.horizontalHeader().setStretchLastSection(False)
        self.preview_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)  # 文本列可调整
        self.preview_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)  # 字符数列固定
        self.preview_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)  # 时长列固定
        self.preview_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)  # 操作列固定
        
        layout.addWidget(self.preview_table)
        
        # 操作按钮区域
        button_layout = QHBoxLayout()
        
        # 合并按钮
        self.merge_up_btn = PushButton("向上合并")
        self.merge_up_btn.clicked.connect(self.merge_up)
        self.merge_up_btn.setFixedSize(100, 35)
        
        self.merge_down_btn = PushButton("向下合并")
        self.merge_down_btn.clicked.connect(self.merge_down)
        self.merge_down_btn.setFixedSize(100, 35)
        
        # 删除按钮
        self.delete_row_btn = PushButton("删除选中")
        self.delete_row_btn.clicked.connect(self.delete_selected_row)
        self.delete_row_btn.setFixedSize(100, 35)
        
        # 调整行高按钮
        self.adjust_height_btn = PushButton("调整行高")
        self.adjust_height_btn.clicked.connect(self.optimize_table_layout)
        self.adjust_height_btn.setFixedSize(100, 35)
        self.adjust_height_btn.setToolTip("根据文本内容自动调整列宽和行高")
        
        button_layout.addWidget(self.merge_up_btn)
        button_layout.addWidget(self.merge_down_btn)
        button_layout.addWidget(self.delete_row_btn)
        button_layout.addWidget(self.adjust_height_btn)
        button_layout.addStretch()
        
        # 确定取消按钮
        self.ok_button = PushButton("确定添加")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setFixedSize(100, 35)
        
        self.cancel_button = PushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setFixedSize(80, 35)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setup_styles()
        
    def setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            SmartTextAddDialog {
                background-color: #ffffff;
            }
            QTextEdit {
                border: 2px solid #d0d0d0;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
                font-family: 'Microsoft YaHei', sans-serif;
            }
            QTextEdit:focus {
                border-color: #2196f3;
            }
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2196f3;
            }
            QSpinBox {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QSpinBox:focus {
                border-color: #2196f3;
            }
            QTableWidget {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                gridline-color: #e0e0e0;
                font-size: 14px;
                background-color: #ffffff;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #333333;
                padding: 10px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
            QPushButton {
                background-color: #2196f3;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """)
        
    def optimize_table_layout(self):
        """优化表格布局（列宽和行高）"""
        self.optimize_column_widths()
        self.adjust_table_row_heights()
        
    def on_char_duration_changed(self, value):
        """字符时长改变时更新预览"""
        self.char_duration = value
        self.update_preview_table()
        
    def split_text(self):
        """分句处理"""
        text = self.text_input.toPlainText().strip()
        print(f"输入文本: {text}")
        
        if not text:
            from qfluentwidgets import MessageBox
            MessageBox("提示", "请先输入文本内容", self).exec()
            return
            
        punctuation = self.punctuation_input.text().strip()
        if not punctuation:
            punctuation = "，。！；？"
            
        print(f"分句符号: {punctuation}")
        
        # 分句逻辑
        self.text_segments = self.smart_split_text(text, punctuation)
        print(f"分句结果: {self.text_segments}")
        self.update_preview_table()
        
    def smart_split_text(self, text, punctuation):
        """智能分句"""
        import re
        
        # 创建正则表达式模式，匹配标点符号
        pattern = f"[{re.escape(punctuation)}]"
        
        # 按标点符号分割，但保留标点符号
        parts = re.split(f"({pattern})", text)
        
        segments = []
        current_segment = ""
        
        for part in parts:
            if not part.strip():
                continue
                
            current_segment += part
            
            # 如果当前部分是标点符号，结束当前段落
            if re.match(pattern, part):
                if current_segment.strip():
                    segments.append(current_segment.strip())
                    current_segment = ""
            # 如果累积的文本过长（超过50个字符），也可以考虑分割
            elif len(current_segment) > 50 and part in punctuation:
                if current_segment.strip():
                    segments.append(current_segment.strip())
                    current_segment = ""
        
        # 处理剩余的文本
        if current_segment.strip():
            segments.append(current_segment.strip())
            
        # 过滤掉空段落和只有标点的段落
        segments = [seg for seg in segments if seg.strip() and not all(c in punctuation for c in seg.strip())]
        
        return segments
        
    def update_preview_table(self):
        """更新预览表格"""
        print(f"更新预览表格，文本段落数量: {len(self.text_segments)}")
        print(f"文本段落内容: {self.text_segments}")
        
        self.preview_table.setRowCount(len(self.text_segments))
        
        for row, segment in enumerate(self.text_segments):
            print(f"处理第{row}行，内容: {segment}")
            # 文本内容 - 支持自动换行
            text_item = QTableWidgetItem(segment)
            text_item.setFlags(text_item.flags() | Qt.ItemIsEditable)
            # 设置文本自动换行
            text_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            # 启用自动换行
            text_item.setData(Qt.UserRole, True)  # 标记为需要换行的项
            self.preview_table.setItem(row, 0, text_item)
            
            # 字符数
            char_count = len(segment)
            char_item = QTableWidgetItem(str(char_count))
            char_item.setFlags(char_item.flags() & ~Qt.ItemIsEditable)
            char_item.setTextAlignment(Qt.AlignCenter)
            self.preview_table.setItem(row, 1, char_item)
            
            # 显示时长
            duration = char_count * self.char_duration
            duration_item = QTableWidgetItem(str(duration))
            duration_item.setFlags(duration_item.flags() | Qt.ItemIsEditable)
            duration_item.setTextAlignment(Qt.AlignCenter)
            self.preview_table.setItem(row, 2, duration_item)
            
            # 操作按钮
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(5, 2, 5, 2)
            button_layout.setSpacing(5)
            
            edit_btn = PushButton("编辑")
            edit_btn.setFixedSize(50, 25)
            edit_btn.clicked.connect(lambda checked, r=row: self.edit_text(r))
            
            button_layout.addWidget(edit_btn)
            button_layout.addStretch()
            
            self.preview_table.setCellWidget(row, 3, button_widget)
            
        # 连接表格编辑信号
        self.preview_table.itemChanged.connect(self.on_table_item_changed)
        
        # 优化列宽和行高
        self.optimize_column_widths()
        self.adjust_table_row_heights()
        
    def optimize_column_widths(self):
        """根据内容优化列宽"""
        if not self.text_segments:
            return
            
        # 计算文本列的理想宽度
        font = QFont()
        font.setPointSize(9)
        fm = QFontMetrics(font)
        
        max_text_width = 0
        for segment in self.text_segments:
            # 计算文本宽度
            text_width = fm.horizontalAdvance(segment)
            max_text_width = max(max_text_width, text_width)
        
        # 设置文本列宽度（最小350，最大600）
        ideal_width = max_text_width + 50  # 添加一些边距
        text_column_width = max(350, min(600, ideal_width))
        
        # 更新列宽
        self.preview_table.setColumnWidth(0, text_column_width)
        
        # 重新计算行高
        self.adjust_table_row_heights()
        
    def adjust_table_row_heights(self):
        """根据文本内容自动调整表格行高"""
        # 获取实际的文本列宽度
        actual_column_width = self.preview_table.columnWidth(0)
        
        for row in range(self.preview_table.rowCount()):
            # 获取文本内容
            text_item = self.preview_table.item(row, 0)
            if text_item:
                text_content = text_item.text()
                
                # 计算实际显示行数（考虑自动换行）
                actual_lines = self.calculate_display_lines(text_content, actual_column_width)
                
                # 根据文本长度和行数计算理想高度
                char_count = len(text_content)
                base_height = 45  # 基础高度
                
                # 根据字符数调整高度（更平滑的算法）
                if char_count <= 30:
                    height_factor = 1.0
                elif char_count <= 60:
                    height_factor = 1.3
                elif char_count <= 100:
                    height_factor = 1.6
                else:
                    height_factor = 2.0
                
                # 根据实际显示行数调整高度
                if actual_lines == 1:
                    line_factor = 1.0
                elif actual_lines == 2:
                    line_factor = 1.6
                elif actual_lines == 3:
                    line_factor = 2.2
                elif actual_lines == 4:
                    line_factor = 2.8
                else:
                    line_factor = 3.2
                
                # 计算最终高度（取字符数和行数的最大值）
                ideal_height = int(base_height * max(height_factor, line_factor))
                
                # 设置最小和最大高度限制
                min_height = 45
                max_height = 300  # 增加最大高度以适应更多行
                final_height = max(min_height, min(max_height, ideal_height))
                
                # 设置行高
                self.preview_table.setRowHeight(row, final_height)
                
    def calculate_display_lines(self, text, column_width):
        """计算文本在指定列宽下的实际显示行数"""
        if not text:
            return 1
            
        # 创建字体度量对象来准确计算字符宽度
        font = QFont()
        font.setPointSize(9)  # 表格默认字体大小
        fm = QFontMetrics(font)
        
        # 计算可用宽度（列宽减去左右边距）
        available_width = column_width - 16  # 减去左右边距
        
        # 计算换行符分割的行数
        explicit_lines = text.count('\n') + 1
        
        # 计算自动换行产生的行数
        current_line = ""
        auto_wrap_lines = 1
        
        for char in text:
            if char == '\n':
                # 遇到换行符，重置当前行
                current_line = ""
                auto_wrap_lines += 1
                continue
                
            test_line = current_line + char
            if fm.horizontalAdvance(test_line) <= available_width:
                current_line = test_line
            else:
                # 需要换行
                if current_line:
                    current_line = char
                    auto_wrap_lines += 1
                else:
                    # 单个字符就超宽，强制换行
                    current_line = ""
                    auto_wrap_lines += 1
        
        # 返回实际显示行数（取最大值）
        return max(explicit_lines, auto_wrap_lines)
        
    def adjust_single_row_height(self, row):
        """调整单个行的行高"""
        if row >= self.preview_table.rowCount():
            return
            
        # 获取文本内容
        text_item = self.preview_table.item(row, 0)
        if text_item:
            text_content = text_item.text()
            
            # 获取实际的文本列宽度
            actual_column_width = self.preview_table.columnWidth(0)
            
            # 计算实际显示行数（考虑自动换行）
            actual_lines = self.calculate_display_lines(text_content, actual_column_width)
            
            # 根据文本长度和行数计算理想高度
            char_count = len(text_content)
            base_height = 45  # 基础高度
            
            # 根据字符数调整高度（更平滑的算法）
            if char_count <= 30:
                height_factor = 1.0
            elif char_count <= 60:
                height_factor = 1.3
            elif char_count <= 100:
                height_factor = 1.6
            else:
                height_factor = 2.0
            
            # 根据实际显示行数调整高度
            if actual_lines == 1:
                line_factor = 1.0
            elif actual_lines == 2:
                line_factor = 1.6
            elif actual_lines == 3:
                line_factor = 2.2
            elif actual_lines == 4:
                line_factor = 2.8
            else:
                line_factor = 3.2
            
            # 计算最终高度（取字符数和行数的最大值）
            ideal_height = int(base_height * max(height_factor, line_factor))
            
            # 设置最小和最大高度限制
            min_height = 45
            max_height = 300  # 增加最大高度以适应更多行
            final_height = max(min_height, min(max_height, ideal_height))
            
            # 设置行高
            self.preview_table.setRowHeight(row, final_height)
        
    def on_table_item_changed(self, item):
        """表格项改变时的处理"""
        row = item.row()
        col = item.column()
        
        if col == 0:  # 文本内容改变
            new_text = item.text()
            if row < len(self.text_segments):
                self.text_segments[row] = new_text
                # 更新字符数和时长
                char_count = len(new_text)
                
                # 安全地更新字符数列
                char_item = self.preview_table.item(row, 1)
                if char_item:
                    char_item.setText(str(char_count))
                else:
                    # 如果项不存在，创建新项
                    char_item = QTableWidgetItem(str(char_count))
                    char_item.setFlags(char_item.flags() & ~Qt.ItemIsEditable)
                    self.preview_table.setItem(row, 1, char_item)
                
                # 安全地更新时长列
                duration = char_count * self.char_duration
                duration_item = self.preview_table.item(row, 2)
                if duration_item:
                    duration_item.setText(str(duration))
                else:
                    # 如果项不存在，创建新项
                    duration_item = QTableWidgetItem(str(duration))
                    duration_item.setFlags(duration_item.flags() | Qt.ItemIsEditable)
                    self.preview_table.setItem(row, 2, duration_item)
                
                # 调整当前行的行高
                self.adjust_single_row_height(row)
                    
        elif col == 2:  # 显示时长改变
            try:
                # 先转换为浮点数，再转换为整数，以处理"100.0"这样的输入
                new_duration = int(float(item.text()))
                if new_duration < 100:
                    item.setText("100")
            except ValueError:
                # 如果输入无效，恢复原值
                if row < len(self.text_segments):
                    char_count = len(self.text_segments[row])
                    duration = char_count * self.char_duration
                    item.setText(str(duration))
                    
    def edit_text(self, row):
        """编辑指定行的文本"""
        if row >= len(self.text_segments):
            return
            
        current_text = self.text_segments[row]
        dialog = MultiLineTextEditDialog(current_text, self)
        if dialog.exec() == QDialog.Accepted:
            new_text = dialog.get_text()
            self.text_segments[row] = new_text
            self.update_preview_table()
            # 编辑完成后调整当前行的行高
            self.adjust_single_row_height(row)
            
    def merge_up(self):
        """向上合并"""
        current_row = self.preview_table.currentRow()
        if current_row <= 0 or current_row >= len(self.text_segments):
            from qfluentwidgets import MessageBox
            MessageBox("提示", "请选择要合并的行（不能是第一行）", self).exec()
            return
            
        # 合并到上一行
        self.text_segments[current_row - 1] += self.text_segments[current_row]
        del self.text_segments[current_row]
        self.update_preview_table()
        
        # 选中合并后的行
        if current_row - 1 < self.preview_table.rowCount():
            self.preview_table.selectRow(current_row - 1)
            
    def merge_down(self):
        """向下合并"""
        current_row = self.preview_table.currentRow()
        if current_row < 0 or current_row >= len(self.text_segments) - 1:
            from qfluentwidgets import MessageBox
            MessageBox("提示", "请选择要合并的行（不能是最后一行）", self).exec()
            return
            
        # 合并到当前行
        self.text_segments[current_row] += self.text_segments[current_row + 1]
        del self.text_segments[current_row + 1]
        self.update_preview_table()
        
        # 选中合并后的行
        self.preview_table.selectRow(current_row)
        
    def delete_selected_row(self):
        """删除选中的行"""
        current_row = self.preview_table.currentRow()
        if current_row < 0 or current_row >= len(self.text_segments):
            from qfluentwidgets import MessageBox
            MessageBox("提示", "请选择要删除的行", self).exec()
            return
            
        from qfluentwidgets import MessageBox
        reply = QMessageBox.question(
            self, "确认删除", 
            "确定要删除选中的文本段落吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.text_segments[current_row]
            self.update_preview_table()
            
    def get_text_segments(self):
        """获取文本段落列表，包含时长信息"""
        segments_with_duration = []
        for row in range(len(self.text_segments)):
            text = self.text_segments[row]
            try:
                duration_item = self.preview_table.item(row, 2)
                # 先转换为浮点数，再转换为整数，以处理"100.0"这样的输入
                duration = int(float(duration_item.text())) if duration_item else len(text) * self.char_duration
            except (ValueError, AttributeError):
                duration = len(text) * self.char_duration
                
            segments_with_duration.append({
                'text': text,
                'duration': duration
            })
            
        return segments_with_duration

class TextPositionPreviewDialog(QDialog):
    """文本位置预览对话框"""
    def __init__(self, draft_data, text_id, parent=None):
        super().__init__(parent)
        self.draft_data = draft_data
        self.text_id = text_id
        self.init_ui()
        self.setup_canvas()
        
    def init_ui(self):
        self.setWindowTitle("文本位置预览")
        self.setMinimumSize(900, 700)
        self.resize(1200, 800)  # 设置初始大小，但允许调整
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("文本位置预览")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 画布信息
        canvas_config = self.draft_data.get("canvas_config", {})
        width = canvas_config.get("width", 1920)
        height = canvas_config.get("height", 1080)
        ratio = canvas_config.get("ratio", "16:9")
        
        info_label = QLabel(f"画布尺寸: {width} x {height} ({ratio})")
        info_label.setStyleSheet("font-size: 14px; color: #666666; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # 图形视图
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        from PyQt5.QtGui import QPainter
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        
        layout.addWidget(self.graphics_view)
        
        # 坐标和旋转编辑区域
        edit_frame = QFrame()
        edit_frame.setFrameStyle(QFrame.Box)
        edit_frame.setStyleSheet("QFrame { border: 1px solid #d0d0d0; border-radius: 4px; padding: 10px; }")
        edit_layout = QVBoxLayout(edit_frame)
        
        # 坐标编辑
        coord_layout = QHBoxLayout()
        coord_layout.addWidget(QLabel("X坐标:"))
        
        self.x_spinbox = QDoubleSpinBox()
        self.x_spinbox.setRange(-1.0, 1.0)
        self.x_spinbox.setSingleStep(0.01)
        self.x_spinbox.setDecimals(3)
        self.x_spinbox.valueChanged.connect(self.on_position_changed)
        self.x_spinbox.setStyleSheet("QDoubleSpinBox { min-width: 80px; }")
        coord_layout.addWidget(self.x_spinbox)
        
        coord_layout.addWidget(QLabel("Y坐标:"))
        
        self.y_spinbox = QDoubleSpinBox()
        self.y_spinbox.setRange(-1.0, 1.0)
        self.y_spinbox.setSingleStep(0.01)
        self.y_spinbox.setDecimals(3)
        self.y_spinbox.valueChanged.connect(self.on_position_changed)
        self.y_spinbox.setStyleSheet("QDoubleSpinBox { min-width: 80px; }")
        coord_layout.addWidget(self.y_spinbox)
        
        coord_layout.addWidget(QLabel("旋转角度:"))
        
        self.rotation_spinbox = QDoubleSpinBox()
        self.rotation_spinbox.setRange(-360.0, 360.0)
        self.rotation_spinbox.setSingleStep(1.0)
        self.rotation_spinbox.setDecimals(1)
        self.rotation_spinbox.setSuffix("°")
        self.rotation_spinbox.valueChanged.connect(self.on_position_changed)
        self.rotation_spinbox.setStyleSheet("QDoubleSpinBox { min-width: 80px; }")
        coord_layout.addWidget(self.rotation_spinbox)
        
        coord_layout.addStretch()
        edit_layout.addLayout(coord_layout)
        
        # 说明文字
        info_label = QLabel("提示：坐标范围 [-1, 1]，(0, 0) 为画布中心，坐标点为文本中心")
        info_label.setStyleSheet("color: #666666; font-size: 12px;")
        edit_layout.addWidget(info_label)
        
        layout.addWidget(edit_frame)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_button = PushButton("应用")
        self.apply_button.clicked.connect(self.apply_position)
        self.apply_button.setFixedSize(80, 35)
        
        self.close_button = PushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setFixedSize(80, 35)
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
        
    def setup_canvas(self):
        """设置画布和文本预览"""
        # 获取画布配置
        canvas_config = self.draft_data.get("canvas_config", {})
        canvas_width = canvas_config.get("width", 1920)
        canvas_height = canvas_config.get("height", 1080)
        
        # 计算缩放比例以适应视图
        view_width = 800
        view_height = 500
        scale_x = view_width / canvas_width
        scale_y = view_height / canvas_height
        scale = min(scale_x, scale_y)
        
        # 设置场景大小
        scene_width = canvas_width * scale
        scene_height = canvas_height * scale
        self.graphics_scene.setSceneRect(0, 0, scene_width, scene_height)
        
        # 绘制画布背景
        canvas_rect = QGraphicsRectItem(0, 0, scene_width, scene_height)
        canvas_rect.setPen(QPen(QColor(200, 200, 200), 2))
        canvas_rect.setBrush(QBrush(QColor(240, 240, 240)))
        self.graphics_scene.addItem(canvas_rect)
        
        # 绘制中心线
        center_x = scene_width / 2
        center_y = scene_height / 2
        
        # 垂直中心线
        v_line = self.graphics_scene.addLine(center_x, 0, center_x, scene_height, 
                                           QPen(QColor(150, 150, 150), 1, Qt.DashLine))
        # 水平中心线
        h_line = self.graphics_scene.addLine(0, center_y, scene_width, center_y, 
                                           QPen(QColor(150, 150, 150), 1, Qt.DashLine))
        
        # 查找并显示所有文本
        self.display_texts(scale, scene_width, scene_height)
        
    def display_texts(self, scale, scene_width, scene_height):
        """只显示当前编辑的文本"""
        texts = self.draft_data.get("materials", {}).get("texts", [])
        tracks = self.draft_data.get("tracks", [])
        
        # 只查找当前编辑的文本
        current_text = None
        for text in texts:
            if text.get("id") == self.text_id:
                current_text = text
                break
        
        if not current_text:
            return
            
        # 获取当前文本的内容和样式
        content_data = json.loads(current_text.get("content", "{}"))
        text_content = content_data.get("text", "")
        
        # 获取文本样式
        styles = content_data.get("styles", [])
        style = styles[0] if styles else {}
        font_size = style.get("size", 6)
        fill_color = style.get("fill", {}).get("content", {}).get("solid", {}).get("color", [0.13, 0.63, 0.24])
        
        # 查找文本位置和旋转
        pos_x, pos_y, rotation = 0, 0, 0
        for track in tracks:
            if track.get("type") == "text":
                segments = track.get("segments", [])
                for segment in segments:
                    if segment.get("material_id") == self.text_id:
                        transform = segment.get("clip", {}).get("transform", {})
                        pos_x = transform.get("x", 0)
                        pos_y = transform.get("y", 0)
                        rotation = segment.get("clip", {}).get("rotation", 0)
                        break
        
        # 转换坐标系统
        # 剪映坐标系：中心为(0,0)，范围[-1,1]
        # Qt坐标系：左上角为(0,0)
        scene_x = (pos_x + 1) * scene_width / 2
        scene_y = (1 - pos_y) * scene_height / 2  # Y轴翻转
        
        # 创建当前编辑的文本项
        text_item = QGraphicsTextItem(text_content)
        
        # 设置字体（使用固定的合适大小以便清晰显示）
        font = QFont()
        font.setPointSize(16)  # 使用固定的16pt字体大小，便于预览
        text_item.setFont(font)
        
        # 设置正常颜色
        if fill_color and len(fill_color) >= 3:
            color = QColor(
                int(fill_color[0] * 255),
                int(fill_color[1] * 255),
                int(fill_color[2] * 255)
            )
            text_item.setDefaultTextColor(color)
        
        # 计算文本的边界矩形，用于居中定位
        text_rect = text_item.boundingRect()
        text_width = text_rect.width()
        text_height = text_rect.height()
        
        # 应用旋转和位置
        if rotation != 0:
            import math
            angle_rad = math.radians(rotation)
            offset_x = -text_width / 2
            offset_y = -text_height / 2
            rotated_offset_x = offset_x * math.cos(angle_rad) - offset_y * math.sin(angle_rad)
            rotated_offset_y = offset_x * math.sin(angle_rad) + offset_y * math.cos(angle_rad)
            final_x = scene_x + rotated_offset_x
            final_y = scene_y + rotated_offset_y
            text_item.setPos(final_x, final_y)
            transform = QTransform()
            transform.rotate(rotation)
            text_item.setTransform(transform)
        else:
            text_item.setPos(scene_x - text_width / 2, scene_y - text_height / 2)
        
        # 添加高亮边框
        rect = text_item.boundingRect()
        border_rect = QGraphicsRectItem(rect)
        border_rect.setPen(QPen(QColor(255, 0, 0), 3))  # 红色边框
        border_rect.setBrush(QBrush(QColor(255, 255, 0, 50)))  # 淡黄色背景
        border_rect.setParentItem(text_item)
        
        # 添加中心位置标记（红色圆点）
        marker = QGraphicsRectItem(-8, -8, 16, 16)
        marker.setPen(QPen(QColor(255, 0, 0), 2))
        marker.setBrush(QBrush(QColor(255, 0, 0)))
        marker.setPos(scene_x, scene_y)
        self.graphics_scene.addItem(marker)
        
        # 添加坐标轴线（帮助定位）
        # 垂直线
        v_guide = self.graphics_scene.addLine(scene_x, scene_y - 30, scene_x, scene_y + 30, 
                                            QPen(QColor(255, 0, 0), 2, Qt.DashLine))
        # 水平线
        h_guide = self.graphics_scene.addLine(scene_x - 30, scene_y, scene_x + 30, scene_y, 
                                            QPen(QColor(255, 0, 0), 2, Qt.DashLine))
        
        self.graphics_scene.addItem(text_item)
        
        # 设置当前文本的坐标值到输入框
        self.load_current_text_position()
        
    def load_current_text_position(self):
        """加载当前文本的位置和旋转到输入框"""
        tracks = self.draft_data.get("tracks", [])
        for track in tracks:
            if track.get("type") == "text":
                segments = track.get("segments", [])
                for segment in segments:
                    if segment.get("material_id") == self.text_id:
                        transform = segment.get("clip", {}).get("transform", {})
                        pos_x = transform.get("x", 0)
                        pos_y = transform.get("y", 0)
                        rotation = segment.get("clip", {}).get("rotation", 0)
                        
                        # 设置输入框的值
                        self.x_spinbox.setValue(pos_x)
                        self.y_spinbox.setValue(pos_y)
                        self.rotation_spinbox.setValue(rotation)
                        return
                        
    def on_position_changed(self):
        """位置改变时实时更新预览"""
        self.update_text_position_preview()
        
    def update_text_position_preview(self):
        """更新文本位置预览"""
        # 临时保存当前输入框的值
        current_x = self.x_spinbox.value()
        current_y = self.y_spinbox.value()
        current_rotation = self.rotation_spinbox.value()
        
        # 临时更新数据中的位置和旋转（仅用于预览）
        self.update_preview_data(current_x, current_y, current_rotation)
        
        # 清除场景并重新绘制
        self.graphics_scene.clear()
        self.setup_canvas_preview()
        
    def setup_canvas_preview(self):
        """设置画布预览（不重新加载输入框值）"""
        # 获取画布配置
        canvas_config = self.draft_data.get("canvas_config", {})
        canvas_width = canvas_config.get("width", 1920)
        canvas_height = canvas_config.get("height", 1080)
        
        # 计算缩放比例以适应视图
        view_width = 800
        view_height = 500
        scale_x = view_width / canvas_width
        scale_y = view_height / canvas_height
        scale = min(scale_x, scale_y)
        
        # 设置场景大小
        scene_width = canvas_width * scale
        scene_height = canvas_height * scale
        self.graphics_scene.setSceneRect(0, 0, scene_width, scene_height)
        
        # 绘制画布背景
        canvas_rect = QGraphicsRectItem(0, 0, scene_width, scene_height)
        canvas_rect.setPen(QPen(QColor(200, 200, 200), 2))
        canvas_rect.setBrush(QBrush(QColor(240, 240, 240)))
        self.graphics_scene.addItem(canvas_rect)
        
        # 绘制中心线
        center_x = scene_width / 2
        center_y = scene_height / 2
        
        # 垂直中心线
        v_line = self.graphics_scene.addLine(center_x, 0, center_x, scene_height, 
                                           QPen(QColor(150, 150, 150), 1, Qt.DashLine))
        # 水平中心线
        h_line = self.graphics_scene.addLine(0, center_y, scene_width, center_y, 
                                           QPen(QColor(150, 150, 150), 1, Qt.DashLine))
        
        # 查找并显示所有文本
        self.display_texts(scale, scene_width, scene_height)
        
    def update_preview_data(self, x, y, rotation):
        """临时更新预览数据"""
        tracks = self.draft_data.get("tracks", [])
        for track in tracks:
            if track.get("type") == "text":
                segments = track.get("segments", [])
                for segment in segments:
                    if segment.get("material_id") == self.text_id:
                        if "clip" not in segment:
                            segment["clip"] = {}
                        if "transform" not in segment["clip"]:
                            segment["clip"]["transform"] = {}
                        
                        # 临时更新位置和旋转
                        segment["clip"]["transform"]["x"] = x
                        segment["clip"]["transform"]["y"] = y
                        segment["clip"]["rotation"] = rotation
                        return
        
    def apply_position(self):
        """应用位置和旋转更改到数据"""
        new_x = self.x_spinbox.value()
        new_y = self.y_spinbox.value()
        new_rotation = self.rotation_spinbox.value()
        
        # 更新数据中的位置和旋转
        tracks = self.draft_data.get("tracks", [])
        for track in tracks:
            if track.get("type") == "text":
                segments = track.get("segments", [])
                for segment in segments:
                    if segment.get("material_id") == self.text_id:
                        if "clip" not in segment:
                            segment["clip"] = {}
                        if "transform" not in segment["clip"]:
                            segment["clip"]["transform"] = {}
                        
                        # 更新位置
                        segment["clip"]["transform"]["x"] = new_x
                        segment["clip"]["transform"]["y"] = new_y
                        
                        # 更新旋转角度
                        segment["clip"]["rotation"] = new_rotation
                        
                        InfoBar.success(
                            title="参数已更新",
                            content=f"文本参数已设置为: X={new_x:.3f}, Y={new_y:.3f}, 旋转={new_rotation:.1f}°",
                            orient=Qt.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=2000,
                            parent=self
                        )
                        return

class FontPreviewDialog(QDialog):
    """字体预览对话框"""
    def __init__(self, available_fonts, current_font="默认字体", parent=None):
        super().__init__(parent)
        self.available_fonts = available_fonts
        self.selected_font = current_font
        self.init_ui()
        self.setup_styles()
        
    def init_ui(self):
        self.setWindowTitle("字体预览选择")
        self.setFixedSize(800, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("字体预览选择")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976d2; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 主要内容区域
        content_layout = QHBoxLayout()
        
        # 左侧字体列表
        left_widget = QFrame()
        left_widget.setFixedWidth(250)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        font_list_label = QLabel("字体列表:")
        font_list_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        left_layout.addWidget(font_list_label)
        
        self.font_list = QListWidget()
        self.font_list.addItems(self.available_fonts)
        self.font_list.currentTextChanged.connect(self.on_font_selected)
        
        # 设置当前选中的字体
        if self.selected_font in self.available_fonts:
            current_index = self.available_fonts.index(self.selected_font)
            self.font_list.setCurrentRow(current_index)
        
        left_layout.addWidget(self.font_list)
        content_layout.addWidget(left_widget)
        
        # 右侧预览区域
        right_widget = QFrame()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(20, 10, 10, 10)
        
        preview_label = QLabel("字体预览:")
        preview_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        right_layout.addWidget(preview_label)
        
        # 预览文本区域
        self.preview_area = QScrollArea()
        self.preview_area.setWidgetResizable(True)
        self.preview_area.setMinimumHeight(400)
        
        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        self.preview_layout.setContentsMargins(15, 15, 15, 15)
        self.preview_layout.setSpacing(20)
        
        # 创建预览文本标签
        self.create_preview_labels()
        
        self.preview_area.setWidget(self.preview_widget)
        right_layout.addWidget(self.preview_area)
        
        content_layout.addWidget(right_widget)
        layout.addLayout(content_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = PushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setFixedSize(80, 35)
        
        self.cancel_button = PushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setFixedSize(80, 35)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # 初始预览（在创建标签后）
        self.update_preview()
        
    def create_preview_labels(self):
        """创建预览文本标签"""
        # 关雎古诗预览文本
        preview_texts = [
            ("关雎", "24px", "bold"),
            ("关关雎鸠，在河之洲。", "18px", "normal"),
            ("窈窕淑女，君子好逑。", "18px", "normal"),
            ("参差荇菜，左右流之。", "18px", "normal"),
            ("窈窕淑女，寤寐求之。", "18px", "normal"),
            ("", "10px", "normal"),  # 空行
            ("English Preview", "20px", "bold"),
            ("The Quick Brown Fox", "16px", "normal"),
            ("Jumps Over The Lazy Dog", "16px", "normal"),
            ("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "14px", "normal"),
            ("abcdefghijklmnopqrstuvwxyz", "14px", "normal"),
            ("0123456789", "14px", "normal"),
        ]
        
        self.preview_labels = []
        for text, size, weight in preview_texts:
            label = QLabel(text)
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignLeft)
            label.setStyleSheet(f"""
                font-size: {size};
                font-weight: {weight};
                color: #333333;
                padding: 5px;
                line-height: 1.5;
            """)
            self.preview_labels.append(label)
            self.preview_layout.addWidget(label)
            
    def setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            FontPreviewDialog {
                background-color: #ffffff;
            }
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-size: 14px;
                padding: 5px;
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
            QScrollArea {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #2196f3;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        
    def on_font_selected(self, font_name):
        """字体选择改变时的处理"""
        if font_name:
            self.selected_font = font_name
            if hasattr(self, 'preview_labels'):
                self.update_preview()
            
    def update_preview(self):
        """更新字体预览"""
        if not self.selected_font:
            return
            
        # 加载字体
        font_path = None
        if self.selected_font != "默认字体":
            font_path = os.path.join("fonts", f"{self.selected_font}.ttf")
            if not os.path.exists(font_path):
                font_path = os.path.join("fonts", f"{self.selected_font}.TTF")
                
        # 更新所有预览标签的字体
        for label in self.preview_labels:
            if font_path and os.path.exists(font_path):
                # 加载自定义字体
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    if font_families:
                        font_family = font_families[0]
                        current_style = label.styleSheet()
                        # 添加字体家族到样式中
                        new_style = current_style + f"font-family: '{font_family}';"
                        label.setStyleSheet(new_style)
            else:
                # 使用系统默认字体
                current_style = label.styleSheet()
                # 移除之前的字体设置，使用默认字体
                lines = current_style.split(';')
                filtered_lines = [line for line in lines if not line.strip().startswith('font-family')]
                new_style = ';'.join(filtered_lines)
                label.setStyleSheet(new_style)
                
    def get_selected_font(self):
        """获取选中的字体"""
        return self.selected_font

class TextEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.draft_data = None
        self.draft_file_path = None
        self.available_fonts = self.get_available_fonts()
        self.loaded_fonts = {}  # 缓存已加载的字体
        self.init_ui()
        self.setup_styles()
        
    def get_available_fonts(self):
        """获取可用字体列表"""
        fonts = ["默认字体"]
        fonts_dir = "fonts"
        if os.path.exists(fonts_dir):
            for file in os.listdir(fonts_dir):
                if file.endswith(('.ttf', '.TTF', '.otf', '.OTF')):
                    # 存储完整路径和显示名称的映射
                    font_name = os.path.splitext(file)[0]
                    fonts.append(font_name)
        return fonts
        
    def get_font_path_from_name(self, font_name):
        """根据字体名称获取绝对路径"""
        if font_name == "默认字体" or not font_name:
            return "默认字体"
            
        # 如果已经是绝对路径，直接返回
        if os.path.isabs(font_name):
            return font_name
            
        # 在本地fonts目录中查找，并返回绝对路径
        fonts_dir = "fonts"
        for ext in ['.ttf', '.TTF', '.otf', '.OTF']:
            local_path = os.path.join(fonts_dir, f"{font_name}{ext}")
            if os.path.exists(local_path):
                # 返回绝对路径
                return os.path.abspath(local_path)
                
        # 如果找不到，返回绝对路径（即使文件不存在）
        return os.path.abspath(os.path.join(fonts_dir, f"{font_name}.ttf"))
        
    def get_font_name_from_path(self, font_path):
        """根据字体路径获取显示名称"""
        if not font_path or font_path == "默认字体":
            return "默认字体"
            
        # 如果是/fonts/格式的路径，提取文件名
        if font_path.startswith("/fonts/"):
            return os.path.splitext(os.path.basename(font_path))[0]
            
        # 如果是完整路径，提取文件名
        if os.path.isabs(font_path):
            return os.path.splitext(os.path.basename(font_path))[0]
            
        # 如果不是完整路径，直接返回
        return font_path
        
    def load_font(self, font_path_or_name):
        """加载字体并返回QFont对象"""
        if font_path_or_name == "默认字体" or not font_path_or_name:
            return QFont()  # 返回系统默认字体
            
        # 检查是否已经加载过这个字体
        if font_path_or_name in self.loaded_fonts:
            return self.loaded_fonts[font_path_or_name]
            
        local_font_path = None
        
        # 如果是/fonts/格式的路径，转换为本地路径
        if font_path_or_name.startswith("/fonts/"):
            # 将/fonts/路径转换为本地fonts目录路径
            relative_path = font_path_or_name[7:]  # 去掉"/fonts/"前缀
            local_font_path = os.path.join("fonts", relative_path)
        elif os.path.isabs(font_path_or_name) and os.path.exists(font_path_or_name):
            # 如果是其他完整路径，直接使用
            local_font_path = font_path_or_name
        else:
            # 否则在本地fonts目录中查找
            fonts_dir = "fonts"
            for ext in ['.ttf', '.TTF', '.otf', '.OTF']:
                test_path = os.path.join(fonts_dir, f"{font_path_or_name}{ext}")
                if os.path.exists(test_path):
                    local_font_path = test_path
                    break
            
        if local_font_path and os.path.exists(local_font_path):
            # 加载自定义字体
            font_id = QFontDatabase.addApplicationFont(local_font_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    font = QFont(font_families[0])
                    self.loaded_fonts[font_path_or_name] = font
                    return font
                    
        # 如果加载失败，返回默认字体
        default_font = QFont()
        self.loaded_fonts[font_path_or_name] = default_font
        return default_font
        
    def apply_text_style(self, item, font_name, font_size, color_array):
        """为表格项应用文本样式"""
        if not item:
            return
            
        # 加载字体
        font = self.load_font(font_name)
        if font:
            # 设置与表格其他列相同的字体大小
            font.setPointSize(9)  # 使用标准的9pt字体大小，与表格其他列保持一致
            item.setFont(font)
        
        # 应用颜色
        if color_array and len(color_array) >= 3:
            try:
                color = QColor(
                    int(color_array[0] * 255),
                    int(color_array[1] * 255),
                    int(color_array[2] * 255)
                )
                if color.isValid():
                    item.setForeground(color)
            except (ValueError, TypeError, IndexError):
                # 如果颜色数据有问题，使用默认颜色
                item.setForeground(QColor(34, 162, 62))
        
    def setup_styles(self):
        """设置组件样式"""
        self.setStyleSheet("""
            TextEditor {
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
            QTableWidget {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                gridline-color: #e0e0e0;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #f0f0f0;
                color: #333333;
                min-height: 60px;
                vertical-align: top;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QTableWidget::item:focus {
                background-color: #e8f5e8;
                border: 2px solid #4caf50;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #333333;
                padding: 8px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2196f3;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 标题
        layout.addWidget(StrongBodyLabel("文本编辑器"))
        
        # 总时长显示区域
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("工程总时长:"))
        self.duration_label = QLabel("未加载文件")
        self.duration_label.setStyleSheet("color: #1976d2; font-weight: bold; font-size: 14px;")
        duration_layout.addWidget(self.duration_label)
        duration_layout.addStretch()
        layout.addLayout(duration_layout)
        
        # 批量操作按钮区域
        batch_layout = QHBoxLayout()
        
        self.select_all_btn = PushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all_texts)
        
        self.select_none_btn = PushButton("取消全选")
        self.select_none_btn.clicked.connect(self.select_none_texts)
        
        self.batch_font_size_btn = PushButton("批量字体大小")
        self.batch_font_size_btn.clicked.connect(self.batch_font_size)
        
        self.batch_color_btn = PushButton("批量颜色")
        self.batch_color_btn.clicked.connect(self.batch_color)
        
        self.batch_position_btn = PushButton("批量位置")
        self.batch_position_btn.clicked.connect(self.batch_position)
        
        self.batch_rotation_btn = PushButton("批量旋转")
        self.batch_rotation_btn.clicked.connect(self.batch_rotation)
        
        self.batch_font_style_btn = PushButton("批量字体")
        self.batch_font_style_btn.clicked.connect(self.batch_font_style)
        
        self.auto_resize_btn = PushButton(FluentIcon.ZOOM_IN, "自动调整行高")
        self.auto_resize_btn.clicked.connect(self.auto_resize_all_rows)
        self.auto_resize_btn.setToolTip("根据文本内容自动调整所有行的高度")
        
        batch_layout.addWidget(self.select_all_btn)
        batch_layout.addWidget(self.select_none_btn)
        batch_layout.addWidget(self.batch_font_size_btn)
        batch_layout.addWidget(self.batch_color_btn)
        batch_layout.addWidget(self.batch_position_btn)
        batch_layout.addWidget(self.batch_rotation_btn)
        batch_layout.addWidget(self.batch_font_style_btn)
        batch_layout.addWidget(self.auto_resize_btn)
        batch_layout.addStretch()
        
        # 字幕导出按钮区域
        export_layout = QHBoxLayout()
        
        self.export_srt_btn = PushButton("导出SRT")
        self.export_srt_btn.clicked.connect(self.export_srt)
        
        self.export_lrc_btn = PushButton("导出LRC")
        self.export_lrc_btn.clicked.connect(self.export_lrc)
        
        self.export_ass_btn = PushButton("导出ASS")
        self.export_ass_btn.clicked.connect(self.export_ass)
        
        export_layout.addWidget(self.export_srt_btn)
        export_layout.addWidget(self.export_lrc_btn)
        export_layout.addWidget(self.export_ass_btn)
        export_layout.addStretch()
        
        layout.addLayout(export_layout)
        
        layout.addLayout(batch_layout)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        self.add_text_btn = PushButton(FluentIcon.ADD, "添加文本")
        self.add_text_btn.clicked.connect(self.add_text)
        
        self.smart_add_text_btn = PushButton(FluentIcon.ADD_TO, "智能添加")
        self.smart_add_text_btn.clicked.connect(self.smart_add_text)
        
        self.delete_text_btn = PushButton(FluentIcon.DELETE, "删除选中")
        self.delete_text_btn.clicked.connect(self.delete_selected_texts)
        
        self.save_file_btn = PushButton(FluentIcon.SAVE_AS, "保存文件")
        self.save_file_btn.clicked.connect(self.save_file)
        
        btn_layout.addWidget(self.add_text_btn)
        btn_layout.addWidget(self.smart_add_text_btn)
        btn_layout.addWidget(self.delete_text_btn)
        btn_layout.addWidget(self.save_file_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 主表格
        self.text_table = QTableWidget()
        self.text_table.setColumnCount(10)
        self.text_table.setHorizontalHeaderLabels([
            "选择", "文本内容", "字体大小", "字体颜色", "字体样式", 
            "X位置", "Y位置", "旋转角度", "开始时间(μs)", "持续时间(μs)"
        ])
        
        # 设置表格属性
        self.text_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.text_table.setAlternatingRowColors(True)
        self.text_table.horizontalHeader().setStretchLastSection(True)
        self.text_table.setColumnWidth(0, 60)  # 选择列
        self.text_table.setColumnWidth(1, 200)  # 文本内容列
        
        # 设置行高 - 增加高度以适应更大字体和自适应内容
        self.text_table.verticalHeader().setDefaultSectionSize(120)  # 增加默认行高
        self.text_table.verticalHeader().setMinimumSectionSize(90)   # 增加最小行高
        self.text_table.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)  # 允许手动调整行高
        
        # 允许编辑
        self.text_table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.text_table.itemChanged.connect(self.on_item_changed)
        self.text_table.cellClicked.connect(self.on_cell_clicked)  # 添加单元格点击事件
        
        # 改善编辑体验
        self.text_table.setWordWrap(True)  # 允许文本换行
        self.text_table.setTextElideMode(Qt.ElideRight)  # 文本过长时显示省略号
        self.text_table.setShowGrid(True)  # 显示网格线
        
        layout.addWidget(self.text_table)
        
    def load_draft_file(self, file_path):
        """加载剪映工程文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.draft_data = json.load(f)
            self.draft_file_path = file_path
            self.load_text_table()
            
            # 更新总时长显示
            self.update_duration_display()
            
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
            from qfluentwidgets import MessageBox
            MessageBox("错误", f"加载文件失败: {str(e)}", self).exec()
            
    def update_duration_display(self):
        """更新总时长显示"""
        if not self.draft_data:
            self.duration_label.setText("未加载文件")
            return
            
        # 计算总时长
        total_duration = self.calculate_total_duration()
        if total_duration > 0:
            duration_seconds = total_duration / 1000000  # 转换为秒
            duration_minutes = duration_seconds / 60
            duration_hours = duration_minutes / 60
            
            if duration_hours >= 1:
                duration_text = f"{duration_hours:.1f}小时 ({duration_seconds:.2f}秒)"
            elif duration_minutes >= 1:
                duration_text = f"{duration_minutes:.1f}分钟 ({duration_seconds:.2f}秒)"
            else:
                duration_text = f"{duration_seconds:.2f}秒"
                
            self.duration_label.setText(duration_text)
        else:
            self.duration_label.setText("无时长信息")
        
    def load_text_table(self):
        """加载文本表格"""
        self.text_table.setRowCount(0)
        if not self.draft_data:
            return
            
        texts = self.draft_data.get("materials", {}).get("texts", [])
        self.text_table.setRowCount(len(texts))
        
        # 存储样式信息，稍后应用
        style_info = []
        
        for row, text in enumerate(texts):
            content_data = json.loads(text.get("content", "{}"))
            text_content = content_data.get("text", f"文本 {row+1}")
            
            # 选择框
            checkbox = QCheckBox()
            self.text_table.setCellWidget(row, 0, checkbox)
            
            # 解析样式
            styles = content_data.get("styles", [])
            style = styles[0] if styles else {}
            
            # 获取字体样式信息，确保有默认值
            font_size = style.get("size", 6)
            # 确保字体大小是整数，处理JSON中可能是浮点数的情况
            if isinstance(font_size, float):
                font_size = int(font_size)
            elif isinstance(font_size, str):
                try:
                    font_size = int(float(font_size))
                except (ValueError, TypeError):
                    font_size = 6
            else:
                font_size = int(font_size)
            
            fill_color = style.get("fill", {}).get("content", {}).get("solid", {}).get("color", [0.13, 0.63, 0.24])
            # 正确的字体样式位置：["materials"]["texts"][0]["content"]["styles"][0]["font"]["path"]
            font_info = style.get("font", {})
            font_style = font_info.get("path", "默认字体")
            
            # 存储样式信息
            style_info.append((row, font_style, font_size, fill_color))
            
            # 文本内容 - 使用内嵌的多行文本编辑器
            text_edit = MultiLineTextEdit(text_content, text.get("id"), self, None)
            
            # 应用字体样式到文本编辑器
            font_style = font_info.get("path", "默认字体")
            # 不传递颜色参数，让文本内容不跟随颜色参数变化
            self.apply_text_style_to_editor(text_edit, font_style, font_size, None)
            
            self.text_table.setCellWidget(row, 1, text_edit)
            
            # 字体大小 - 可编辑，确保有默认值
            size_item = QTableWidgetItem(str(font_size))
            self.text_table.setItem(row, 2, size_item)
            
            # 字体颜色 - 使用颜色显示组件
            color_widget = ColorDisplayWidget(fill_color)
            self.text_table.setCellWidget(row, 3, color_widget)
            
            # 字体样式 - 显示友好的名称，但存储完整路径
            display_name = self.get_font_name_from_path(font_style)
            font_item = QTableWidgetItem(display_name)
            font_item.setData(Qt.UserRole, font_style)  # 存储完整路径
            self.text_table.setItem(row, 4, font_item)
            
            # 查找轨道信息，确保有默认值
            tracks = self.draft_data.get("tracks", [])
            pos_x, pos_y, rotation, start_time, duration = 0, 0, 0, 0, 3000000
            
            for track in tracks:
                if track.get("type") == "text":
                    segments = track.get("segments", [])
                    for segment in segments:
                        if segment.get("material_id") == text.get("id"):
                            transform = segment.get("clip", {}).get("transform", {})
                            pos_x = transform.get("x", 0)
                            pos_y = transform.get("y", 0)
                            rotation = segment.get("clip", {}).get("rotation", 0)
                            
                            timerange = segment.get("target_timerange", {})
                            start_time = timerange.get("start", 0)
                            duration = timerange.get("duration", 3000000)
                            break
            
            # X位置 - 可编辑，确保有默认值
            pos_x_item = QTableWidgetItem(f"{pos_x:.2f}")
            self.text_table.setItem(row, 5, pos_x_item)
            
            # Y位置 - 可编辑，确保有默认值
            pos_y_item = QTableWidgetItem(f"{pos_y:.2f}")
            self.text_table.setItem(row, 6, pos_y_item)
            
            # 旋转角度 - 可编辑，确保有默认值
            rotation_item = QTableWidgetItem(f"{rotation:.1f}")
            self.text_table.setItem(row, 7, rotation_item)
            
            # 开始时间 - 可编辑，确保有默认值
            start_item = QTableWidgetItem(str(start_time))
            self.text_table.setItem(row, 8, start_item)
            
            # 持续时间 - 可编辑，确保有默认值
            duration_item = QTableWidgetItem(str(duration))
            self.text_table.setItem(row, 9, duration_item)
            
        # 在所有表格项都设置完成后，调整行高以适应内容
        self.text_table.resizeRowsToContents()
        
        # 延迟再次调整行高，确保内嵌编辑器的初始化完成
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self.smart_resize_rows)
        
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
        
    def normalize_text_styles(self, content_data):
        """标准化文本样式，确保只有一个样式且范围正确"""
        text_length = len(content_data.get("text", ""))
        
        if "styles" not in content_data or not content_data["styles"]:
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
                "range": [0, text_length]
            }]
        else:
            # 只保留第一个样式，删除其他样式
            first_style = content_data["styles"][0]
            first_style["range"] = [0, text_length]
            content_data["styles"] = [first_style]
        
        return content_data
    
    def on_text_content_changed(self, text_id, new_content):
        """处理内嵌文本编辑器的内容变化"""
        if not self.draft_data or not text_id:
            return
            
        try:
            # 更新数据中的文本内容
            self.update_text_content(text_id, new_content)
        except Exception as e:
            print(f"更新文本内容失败: {str(e)}")
            
    def apply_text_style_to_editor(self, text_edit, font_name, font_size, color_array):
        """为内嵌文本编辑器应用文本样式"""
        if not text_edit:
            return
            
        # 加载字体
        font = self.load_font(font_name)
        if font:
            # 设置合适的字体大小用于编辑器显示
            font.setPointSize(max(10, min(font_size, 14)))  # 限制字体大小在10-14之间，便于编辑
            text_edit.setFont(font)
        
        # 移除颜色应用部分，让文本内容不跟随颜色参数变化
        # 文本编辑器将使用默认的黑色文本颜色，便于编辑和阅读
        
    def apply_all_text_styles(self, style_info):
        """批量应用所有文本样式"""
        for row, font_style, font_size, fill_color in style_info:
            # 获取内嵌的文本编辑器
            text_edit = self.text_table.cellWidget(row, 1)
            if text_edit and hasattr(text_edit, 'text_id'):
                # 直接应用到内嵌编辑器，不传递颜色参数
                self.apply_text_style_to_editor(text_edit, font_style, font_size, None)
            
    def on_item_changed(self, item):
        """表格项目改变时的处理"""
        if not self.draft_data:
            return
            
        row = item.row()
        col = item.column()
        
        # 获取文本ID，需要从内嵌的文本编辑器获取
        text_edit = self.text_table.cellWidget(row, 1)
        if not text_edit or not hasattr(text_edit, 'text_id'):
            return
            
        text_id = text_edit.text_id
        
        try:
            if col == 1:  # 文本内容列现在使用内嵌编辑器，不需要处理
                return  # 内嵌编辑器会自动处理文本变化
            elif col == 2:  # 字体大小
                # 验证输入是否为有效数字
                try:
                    # 先转换为浮点数，再转换为整数，以处理"5.0"这样的输入
                    new_size = int(float(item.text()))
                    if new_size < 1 or new_size > 100:
                        raise ValueError("字体大小必须在1-100之间")
                except ValueError as e:
                    from qfluentwidgets import MessageBox
                    MessageBox("错误", f"请输入有效的字体大小 (1-100): {str(e)}", self).exec()
                    self.load_text_table()  # 重新加载以恢复原值
                    return
                    
                self.update_font_size(text_id, new_size)
                # 更新内嵌文本编辑器的字体大小预览
                text_edit = self.text_table.cellWidget(row, 1)
                if text_edit and hasattr(text_edit, 'text_id'):
                    # 获取当前字体信息
                    font_style_item = self.text_table.item(row, 4)
                    font_style = font_style_item.data(Qt.UserRole) if font_style_item else "默认字体"
                    # 重新应用样式到内嵌编辑器，不传递颜色参数
                    self.apply_text_style_to_editor(text_edit, font_style, new_size, None)
            elif col == 5:  # X位置
                # 验证输入是否为有效数字
                try:
                    x_value = float(item.text())
                    if x_value < -1.0 or x_value > 1.0:
                        raise ValueError("X坐标必须在-1.0到1.0之间")
                except ValueError as e:
                    from qfluentwidgets import MessageBox
                    MessageBox("错误", f"请输入有效的X坐标 (-1.0到1.0): {str(e)}", self).exec()
                    self.load_text_table()  # 重新加载以恢复原值
                    return
                    
                self.update_position(text_id, x_value, None)
            elif col == 6:  # Y位置
                # 验证输入是否为有效数字
                try:
                    y_value = float(item.text())
                    if y_value < -1.0 or y_value > 1.0:
                        raise ValueError("Y坐标必须在-1.0到1.0之间")
                except ValueError as e:
                    from qfluentwidgets import MessageBox
                    MessageBox("错误", f"请输入有效的Y坐标 (-1.0到1.0): {str(e)}", self).exec()
                    self.load_text_table()  # 重新加载以恢复原值
                    return
                    
                self.update_position(text_id, None, y_value)
            elif col == 7:  # 旋转角度
                # 验证输入是否为有效数字
                try:
                    rotation_value = float(item.text())
                    if rotation_value < -360.0 or rotation_value > 360.0:
                        raise ValueError("旋转角度必须在-360到360之间")
                except ValueError as e:
                    from qfluentwidgets import MessageBox
                    MessageBox("错误", f"请输入有效的旋转角度 (-360到360): {str(e)}", self).exec()
                    self.load_text_table()  # 重新加载以恢复原值
                    return
                    
                self.update_rotation(text_id, rotation_value)
            elif col == 8:  # 开始时间
                # 验证输入是否为有效数字
                try:
                    # 先转换为浮点数，再转换为整数，以处理"1000.0"这样的输入
                    start_value = int(float(item.text()))
                    if start_value < 0:
                        raise ValueError("开始时间不能为负数")
                except ValueError as e:
                    from qfluentwidgets import MessageBox
                    MessageBox("错误", f"请输入有效的开始时间 (非负整数): {str(e)}", self).exec()
                    self.load_text_table()  # 重新加载以恢复原值
                    return
                    
                self.update_time(text_id, start_value, None)
                # 更新时间后刷新总时长显示
                self.update_duration_display()
            elif col == 9:  # 持续时间
                # 验证输入是否为有效数字
                try:
                    # 先转换为浮点数，再转换为整数，以处理"3000000.0"这样的输入
                    duration_value = int(float(item.text()))
                    if duration_value <= 0:
                        raise ValueError("持续时间必须大于0")
                except ValueError as e:
                    from qfluentwidgets import MessageBox
                    MessageBox("错误", f"请输入有效的持续时间 (正整数): {str(e)}", self).exec()
                    self.load_text_table()  # 重新加载以恢复原值
                    return
                    
                self.update_time(text_id, None, duration_value)
                # 更新时间后刷新总时长显示
                self.update_duration_display()
        except Exception as e:
            # 更详细的错误信息
            error_msg = f"更新失败: {str(e)}"
            if "ValueError" in str(type(e)):
                error_msg = "请输入有效的数值"
            from qfluentwidgets import MessageBox
            MessageBox("错误", error_msg, self).exec()
            self.load_text_table()  # 重新加载以恢复原值
            
    def on_cell_clicked(self, row, col):
        """处理单元格点击事件"""
        if not self.draft_data:
            return
            
        # 获取文本ID，需要从内嵌的文本编辑器获取
        if col == 1:  # 文本内容列
            text_edit = self.text_table.cellWidget(row, 1)
            if text_edit and hasattr(text_edit, 'text_id'):
                text_id = text_edit.text_id
            else:
                return
        else:
            # 其他列从第1列的文本编辑器获取text_id
            text_edit = self.text_table.cellWidget(row, 1)
            if text_edit and hasattr(text_edit, 'text_id'):
                text_id = text_edit.text_id
            else:
                return
        
        if col == 3:  # 字体颜色列
            self.edit_single_color(text_id, row)
        elif col == 4:  # 字体样式列
            self.edit_single_font_style(text_id, row)
        elif col == 5 or col == 6:  # X位置或Y位置列
            self.show_text_position_preview(text_id, row)
            
    def edit_multiline_text(self, row):
        """编辑多行文本"""
        if not self.draft_data:
            return
            
        # 获取内嵌的文本编辑器
        text_edit = self.text_table.cellWidget(row, 1)
        if not text_edit or not hasattr(text_edit, 'text_id'):
            return
            
        text_id = text_edit.text_id
        original_text = text_edit.get_text()  # 直接从编辑器获取文本
        
        # 打开多行文本编辑对话框
        dialog = MultiLineTextEditDialog(original_text, self)
        if dialog.exec() == QDialog.Accepted:
            new_text = dialog.get_text()
            
            # 更新数据
            try:
                self.update_text_content(text_id, new_text)
                
                # 更新内嵌编辑器的文本内容
                text_edit.set_text(new_text)
                
                # 重新应用字体样式到内嵌编辑器
                font_style_item = self.text_table.item(row, 4)
                font_size_item = self.text_table.item(row, 2)
                
                if font_style_item and font_size_item:
                    font_style = font_style_item.data(Qt.UserRole) or font_style_item.text()
                    try:
                        font_size = int(font_size_item.text())
                    except (ValueError, AttributeError):
                        font_size = 6
                    
                    # 重新应用样式到内嵌编辑器，不传递颜色参数
                    self.apply_text_style_to_editor(text_edit, font_style, font_size, None)
                
                InfoBar.success(
                    title="文本已更新",
                    content="多行文本内容已保存",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=1500,
                    parent=self
                )
                
            except Exception as e:
                from qfluentwidgets import MessageBox
                MessageBox("错误", f"更新文本失败: {str(e)}", self).exec()
            
    def show_text_position_preview(self, text_id, row):
        """显示文本位置预览对话框"""
        if not self.draft_data:
            return
            
        # 打开文本位置预览对话框
        dialog = TextPositionPreviewDialog(self.draft_data, text_id, self)
        dialog.exec()
            
    def edit_single_color(self, text_id, row):
        """编辑单个文本的颜色"""
        # 获取当前颜色
        color_widget = self.text_table.cellWidget(row, 3)
        current_color_data = color_widget.get_color() if color_widget and hasattr(color_widget, 'get_color') else [0.13, 0.63, 0.24]
        
        if current_color_data:
            current_qcolor = QColor(
                int(current_color_data[0] * 255),
                int(current_color_data[1] * 255),
                int(current_color_data[2] * 255)
            )
        else:
            current_qcolor = QColor(34, 162, 62)
            
        # 打开颜色选择对话框
        color = QColorDialog.getColor(current_qcolor, self, "选择字体颜色")
        if color.isValid():
            color_array = [color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0]
            
            try:
                # 更新数据
                texts = self.draft_data.get("materials", {}).get("texts", [])
                for text in texts:
                    if text.get("id") == text_id:
                        content_data = json.loads(text.get("content", "{}"))
                        if "styles" not in content_data:
                            content_data["styles"] = [{}]
                        
                        # 确保只有一个样式，并更新范围
                        first_style = content_data["styles"][0] if content_data["styles"] else {}
                        if "fill" not in first_style:
                            first_style["fill"] = {"content": {"solid": {}}}
                        first_style["fill"]["content"]["solid"]["color"] = color_array
                        first_style["range"] = [0, len(content_data.get("text", ""))]
                        content_data["styles"] = [first_style]
                        
                        text["content"] = json.dumps(content_data, ensure_ascii=False)
                        
                        # 同时更新顶级属性
                        text["text_color"] = f"#{int(color_array[0]*255):02X}{int(color_array[1]*255):02X}{int(color_array[2]*255):02X}"
                        text["text_alpha"] = 1.0
                        break
                
                # 更新表格显示 - 更新颜色显示组件
                color_widget = self.text_table.cellWidget(row, 3)
                if color_widget and hasattr(color_widget, 'set_color'):
                    color_widget.set_color(color_array)
                
                # 移除对内嵌文本编辑器的颜色更新，让文本内容不跟随颜色参数变化
                
                InfoBar.success(
                    title="颜色已更新",
                    content="字体颜色设置成功",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=1500,
                    parent=self
                )
                
            except Exception as e:
                from qfluentwidgets import MessageBox
                MessageBox("错误", f"设置颜色失败: {str(e)}", self).exec()
                
    def edit_single_font_style(self, text_id, row):
        """编辑单个文本的字体样式"""
        # 获取当前字体样式
        current_font_item = self.text_table.item(row, 4)
        current_font = current_font_item.text()
        
        # 打开字体预览对话框
        dialog = FontPreviewDialog(self.available_fonts, current_font, self)
        if dialog.exec() == QDialog.Accepted:
            selected_font_name = dialog.get_selected_font()
            
            # 获取完整的字体路径
            if selected_font_name == "默认字体":
                font_path = "默认字体"
            else:
                font_path = self.get_font_path_from_name(selected_font_name)
                if not font_path:
                    font_path = selected_font_name  # 如果找不到路径，使用名称
            
            if font_path != current_font_item.data(Qt.UserRole):
                try:
                    # 更新数据 - 存储完整路径
                    texts = self.draft_data.get("materials", {}).get("texts", [])
                    for text in texts:
                        if text.get("id") == text_id:
                            content_data = json.loads(text.get("content", "{}"))
                            if "styles" not in content_data:
                                content_data["styles"] = [{}]
                            if "font" not in content_data["styles"][0]:
                                content_data["styles"][0]["font"] = {}
                            # 转换为剪映格式的字体路径
                            if font_path == "默认字体":
                                jianying_font_path = "C:/Users/Administrator/AppData/Local/JianyingPro/Apps/5.9.0.11632/Resources/Font/SystemFont/zh-hans.ttf"
                            else:
                                # 如果是本地字体，转换为绝对路径
                                if os.path.isabs(font_path):
                                    jianying_font_path = font_path.replace("\\", "/")
                                else:
                                    jianying_font_path = os.path.abspath(font_path).replace("\\", "/")
                            
                            content_data["styles"][0]["font"]["path"] = jianying_font_path
                            content_data["styles"][0]["font"]["id"] = ""
                            text["content"] = json.dumps(content_data, ensure_ascii=False)
                            
                            # 同时更新顶级字体属性
                            text["font_path"] = jianying_font_path
                            text["font_name"] = ""
                            text["font_id"] = ""
                            break
                    
                    # 更新表格显示 - 显示友好名称，存储完整路径
                    display_name = self.get_font_name_from_path(font_path)
                    current_font_item.setText(display_name)
                    current_font_item.setData(Qt.UserRole, font_path)
                    
                    # 更新内嵌文本编辑器的字体预览
                    text_edit = self.text_table.cellWidget(row, 1)
                    if text_edit and hasattr(text_edit, 'text_id'):
                        # 获取当前字体大小信息
                        font_size_item = self.text_table.item(row, 2)
                        # 先转换为浮点数，再转换为整数，以处理"5.0"这样的输入
                        font_size = int(float(font_size_item.text())) if font_size_item else 6
                        # 重新应用样式到内嵌编辑器，不传递颜色参数
                        self.apply_text_style_to_editor(text_edit, font_path, font_size, None)
                    
                    InfoBar.success(
                        title="字体已更新",
                        content=f"字体样式已设置为: {display_name}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=1500,
                        parent=self
                    )
                    
                except Exception as e:
                    from qfluentwidgets import MessageBox
                    MessageBox("错误", f"设置字体失败: {str(e)}", self).exec()
            
    def update_text_content(self, text_id, content):
        """更新文本内容"""
        texts = self.draft_data.get("materials", {}).get("texts", [])
        for text in texts:
            if text.get("id") == text_id:
                content_data = json.loads(text.get("content", "{}"))
                content_data["text"] = content
                
                # 使用辅助函数标准化样式
                content_data = self.normalize_text_styles(content_data)
                
                text["content"] = json.dumps(content_data, ensure_ascii=False)
                
                # 同时更新顶级的 base_content 字段（如果存在）
                if "base_content" in text:
                    text["base_content"] = content
                break
                
    def update_font_size(self, text_id, size):
        """更新字体大小"""
        texts = self.draft_data.get("materials", {}).get("texts", [])
        for text in texts:
            if text.get("id") == text_id:
                content_data = json.loads(text.get("content", "{}"))
                if "styles" not in content_data:
                    content_data["styles"] = [{}]
                
                # 确保只有一个样式，并更新范围
                first_style = content_data["styles"][0] if content_data["styles"] else {}
                first_style["size"] = size
                first_style["range"] = [0, len(content_data.get("text", ""))]
                content_data["styles"] = [first_style]
                
                text["content"] = json.dumps(content_data, ensure_ascii=False)
                
                # 同时更新顶级属性
                text["font_size"] = float(size)
                text["text_size"] = size * 2  # 剪映的text_size通常是size的2倍
                break
                
    def update_position(self, text_id, x=None, y=None):
        """更新位置"""
        tracks = self.draft_data.get("tracks", [])
        for track in tracks:
            if track.get("type") == "text":
                segments = track.get("segments", [])
                for segment in segments:
                    if segment.get("material_id") == text_id:
                        if "clip" not in segment:
                            segment["clip"] = {}
                        if "transform" not in segment["clip"]:
                            segment["clip"]["transform"] = {}
                        if x is not None:
                            segment["clip"]["transform"]["x"] = x
                        if y is not None:
                            segment["clip"]["transform"]["y"] = y
                        break
                        
    def update_rotation(self, text_id, rotation):
        """更新旋转角度"""
        tracks = self.draft_data.get("tracks", [])
        for track in tracks:
            if track.get("type") == "text":
                segments = track.get("segments", [])
                for segment in segments:
                    if segment.get("material_id") == text_id:
                        if "clip" not in segment:
                            segment["clip"] = {}
                        segment["clip"]["rotation"] = rotation
                        break
                        
    def update_time(self, text_id, start=None, duration=None):
        """更新时间"""
        tracks = self.draft_data.get("tracks", [])
        for track in tracks:
            if track.get("type") == "text":
                segments = track.get("segments", [])
                for segment in segments:
                    if segment.get("material_id") == text_id:
                        if "target_timerange" not in segment:
                            segment["target_timerange"] = {}
                        if start is not None:
                            segment["target_timerange"]["start"] = start
                        if duration is not None:
                            segment["target_timerange"]["duration"] = duration
                        break
                        
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
                
    def get_selected_text_ids(self):
        """获取选中的文本ID列表"""
        selected_ids = []
        for row in range(self.text_table.rowCount()):
            checkbox = self.text_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                # 从内嵌的文本编辑器获取 text_id
                text_edit = self.text_table.cellWidget(row, 1)
                if text_edit and hasattr(text_edit, 'text_id'):
                    text_id = text_edit.text_id
                    if text_id:
                        selected_ids.append(text_id)
        return selected_ids
        
    def batch_font_size(self):
        """批量设置字体大小"""
        selected_ids = self.get_selected_text_ids()
        if not selected_ids:
            from qfluentwidgets import MessageBox
            MessageBox("提示", "请先选择要修改的文本", self).exec()
            return
            
        font_size, ok = QInputDialog.getInt(
            self, "批量设置字体大小", 
            "请输入字体大小 (1-100):", 
            value=6, min=1, max=100
        )
        
        if ok:
            try:
                for text_id in selected_ids:
                    self.update_font_size(text_id, font_size)
                
                self.load_text_table()
                InfoBar.success(
                    title="批量设置成功",
                    content=f"已为 {len(selected_ids)} 个文本设置字体大小",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                from qfluentwidgets import MessageBox
                MessageBox("错误", f"批量设置失败: {str(e)}", self).exec()
                
    def batch_color(self):
        """批量设置颜色"""
        selected_ids = self.get_selected_text_ids()
        if not selected_ids:
            from qfluentwidgets import MessageBox
            MessageBox("提示", "请先选择要修改的文本", self).exec()
            return
            
        color = QColorDialog.getColor(QColor(34, 162, 62), self, "选择颜色")
        if color.isValid():
            color_array = [color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0]
            
            try:
                texts = self.draft_data.get("materials", {}).get("texts", [])
                for text in texts:
                    if text.get("id") in selected_ids:
                        content_data = json.loads(text.get("content", "{}"))
                        if "styles" not in content_data:
                            content_data["styles"] = [{}]
                        
                        # 确保只有一个样式，并更新范围
                        first_style = content_data["styles"][0] if content_data["styles"] else {}
                        if "fill" not in first_style:
                            first_style["fill"] = {"content": {"solid": {}}}
                        first_style["fill"]["content"]["solid"]["color"] = color_array
                        first_style["range"] = [0, len(content_data.get("text", ""))]
                        content_data["styles"] = [first_style]
                        
                        text["content"] = json.dumps(content_data, ensure_ascii=False)
                        
                        # 同时更新顶级属性
                        text["text_color"] = f"#{int(color_array[0]*255):02X}{int(color_array[1]*255):02X}{int(color_array[2]*255):02X}"
                        text["text_alpha"] = 1.0
                
                self.load_text_table()
                InfoBar.success(
                    title="批量设置成功",
                    content=f"已为 {len(selected_ids)} 个文本设置颜色",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                from qfluentwidgets import MessageBox
                MessageBox("错误", f"批量设置失败: {str(e)}", self).exec()
                
    def batch_position(self):
        """批量设置位置"""
        selected_ids = self.get_selected_text_ids()
        if not selected_ids:
            from qfluentwidgets import MessageBox
            MessageBox("提示", "请先选择要修改的文本", self).exec()
            return
            
        x, ok1 = QInputDialog.getDouble(
            self, "批量设置位置", 
            "请输入X坐标 (-1.0 到 1.0):", 
            value=0.0, min=-1.0, max=1.0, decimals=2
        )
        
        if ok1:
            y, ok2 = QInputDialog.getDouble(
                self, "批量设置位置", 
                "请输入Y坐标 (-1.0 到 1.0):", 
                value=0.0, min=-1.0, max=1.0, decimals=2
            )
            
            if ok2:
                try:
                    for text_id in selected_ids:
                        self.update_position(text_id, x, y)
                    
                    self.load_text_table()
                    InfoBar.success(
                        title="批量设置成功",
                        content=f"已为 {len(selected_ids)} 个文本设置位置",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                except Exception as e:
                    from qfluentwidgets import MessageBox
                    MessageBox("错误", f"批量设置失败: {str(e)}", self).exec()
                    
    def batch_rotation(self):
        """批量设置旋转角度"""
        selected_ids = self.get_selected_text_ids()
        if not selected_ids:
            from qfluentwidgets import MessageBox
            MessageBox("提示", "请先选择要修改的文本", self).exec()
            return
            
        rotation, ok = QInputDialog.getDouble(
            self, "批量设置旋转角度", 
            "请输入旋转角度 (-360 到 360):", 
            value=0.0, min=-360.0, max=360.0, decimals=1
        )
        
        if ok:
            try:
                for text_id in selected_ids:
                    self.update_rotation(text_id, rotation)
                
                self.load_text_table()
                InfoBar.success(
                    title="批量设置成功",
                    content=f"已为 {len(selected_ids)} 个文本设置旋转角度",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                from qfluentwidgets import MessageBox
                MessageBox("错误", f"批量设置失败: {str(e)}", self).exec()
                
    def batch_font_style(self):
        """批量设置字体样式"""
        selected_ids = self.get_selected_text_ids()
        if not selected_ids:
            from qfluentwidgets import MessageBox
            MessageBox("提示", "请先选择要修改的文本", self).exec()
            return
            
        # 打开字体预览对话框
        dialog = FontPreviewDialog(self.available_fonts, "默认字体", self)
        if dialog.exec() == QDialog.Accepted:
            selected_font_name = dialog.get_selected_font()
            
            # 获取完整的字体路径
            if selected_font_name == "默认字体":
                font_path = "默认字体"
            else:
                font_path = self.get_font_path_from_name(selected_font_name)
                if not font_path:
                    font_path = selected_font_name  # 如果找不到路径，使用名称
            
            try:
                texts = self.draft_data.get("materials", {}).get("texts", [])
                for text in texts:
                    if text.get("id") in selected_ids:
                        content_data = json.loads(text.get("content", "{}"))
                        if "styles" not in content_data:
                            content_data["styles"] = [{}]
                        if "font" not in content_data["styles"][0]:
                            content_data["styles"][0]["font"] = {}
                        # 转换为剪映格式的字体路径
                        if font_path == "默认字体":
                            jianying_font_path = "C:/Users/Administrator/AppData/Local/JianyingPro/Apps/5.9.0.11632/Resources/Font/SystemFont/zh-hans.ttf"
                        else:
                            # 如果是本地字体，转换为绝对路径
                            if os.path.isabs(font_path):
                                jianying_font_path = font_path.replace("\\", "/")
                            else:
                                jianying_font_path = os.path.abspath(font_path).replace("\\", "/")
                        
                        content_data["styles"][0]["font"]["path"] = jianying_font_path
                        content_data["styles"][0]["font"]["id"] = ""
                        text["content"] = json.dumps(content_data, ensure_ascii=False)
                        
                        # 同时更新顶级字体属性
                        text["font_path"] = jianying_font_path
                        text["font_name"] = ""
                        text["font_id"] = ""
                
                self.load_text_table()
                display_name = self.get_font_name_from_path(font_path)
                InfoBar.success(
                    title="批量设置成功",
                    content=f"已为 {len(selected_ids)} 个文本设置字体样式为: {display_name}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                from qfluentwidgets import MessageBox
                MessageBox("错误", f"批量设置失败: {str(e)}", self).exec()
                
    def delete_selected_texts(self):
        """删除选中的文本"""
        selected_ids = self.get_selected_text_ids()
        if not selected_ids:
            from qfluentwidgets import MessageBox
            MessageBox("提示", "请先选择要删除的文本", self).exec()
            return
            
        # 使用 Qt 的 QMessageBox 进行确认
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除选中的 {len(selected_ids)} 个文本吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 从材料中删除
                texts = self.draft_data.get("materials", {}).get("texts", [])
                self.draft_data["materials"]["texts"] = [
                    text for text in texts if text.get("id") not in selected_ids
                ]
                
                # 从轨道中删除
                tracks = self.draft_data.get("tracks", [])
                for track in tracks:
                    if track.get("type") == "text":
                        track["segments"] = [
                            segment for segment in track.get("segments", [])
                            if segment.get("material_id") not in selected_ids
                        ]
                
                self.load_text_table()
                # 更新总时长显示
                self.update_duration_display()
                
                InfoBar.success(
                    title="删除成功",
                    content=f"已删除 {len(selected_ids)} 个文本",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                from qfluentwidgets import MessageBox
                MessageBox("错误", f"删除失败: {str(e)}", self).exec()
                
    def add_text(self):
        """添加新文本"""
        # 使用多行文本编辑对话框
        dialog = MultiLineTextEditDialog("", self)
        if dialog.exec() != QDialog.Accepted:
            return
            
        text_content = dialog.get_text()
        ok = bool(text_content.strip())
        
        if ok and text_content:
            self.create_single_text(text_content, 3000000)  # 默认3秒显示时长
            # 更新总时长显示
            self.update_duration_display()
            
    def smart_add_text(self):
        """智能添加文本"""
        if not self.draft_data:
            from qfluentwidgets import MessageBox
            MessageBox("错误", "请先加载剪映工程文件", self).exec()
            return
            
        dialog = SmartTextAddDialog(self)
        if dialog.exec() == QDialog.Accepted:
            segments = dialog.get_text_segments()
            if not segments:
                from qfluentwidgets import MessageBox
                MessageBox("提示", "没有要添加的文本段落", self).exec()
                return
                
            try:
                # 临时禁用表格编辑
                self.text_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
                
                # 计算起始时间（从现有文本的最后时间开始）
                start_time = self.get_next_start_time()
                
                # 文本间隔时间（20ms转换为微秒）
                text_gap = 20 * 1000  # 20ms = 20000微秒
                
                # 批量创建文本
                for i, segment in enumerate(segments):
                    text_content = segment['text']
                    duration = segment['duration'] * 1000  # 转换为微秒
                    
                    self.create_single_text(text_content, duration, start_time)
                    
                    # 下一个文本的开始时间 = 当前文本结束时间 + 间隔时间
                    start_time += duration + text_gap
                
                # 刷新表格
                self.load_text_table()
                
                # 重新启用表格编辑
                self.text_table.setEditTriggers(QAbstractItemView.DoubleClicked)
                
                # 更新总时长显示
                self.update_duration_display()
                
                InfoBar.success(
                    title="批量添加成功",
                    content=f"已添加 {len(segments)} 个文本段落，文本间隔 {text_gap // 1000}ms",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                
            except Exception as e:
                # 重新启用表格编辑
                self.text_table.setEditTriggers(QAbstractItemView.DoubleClicked)
                from qfluentwidgets import MessageBox
                MessageBox("错误", f"批量添加失败: {str(e)}", self).exec()
                
    def get_next_start_time(self):
        """获取下一个文本的开始时间"""
        if not self.draft_data:
            return 0
            
        max_end_time = 0
        tracks = self.draft_data.get("tracks", [])
        
        for track in tracks:
            if track.get("type") == "text":
                segments = track.get("segments", [])
                for segment in segments:
                    timerange = segment.get("target_timerange", {})
                    start_time = timerange.get("start", 0)
                    duration = timerange.get("duration", 0)
                    end_time = start_time + duration
                    max_end_time = max(max_end_time, end_time)
                    
        return max_end_time
        
    def create_single_text(self, text_content, duration_us, start_time=0):
        """创建单个文本"""
        try:
            # 生成新的文本ID
            import uuid
            new_text_id = str(uuid.uuid4())
            
            # 创建新的文本材料，包含所有必要的剪映格式字段
            new_text = {
                "add_type": 0,
                "alignment": 1,
                "background_alpha": 1.0,
                "background_color": "",
                "background_height": 0.14,
                "background_horizontal_offset": 0.0,
                "background_round_radius": 0.0,
                "background_style": 0,
                "background_vertical_offset": 0.0,
                "background_width": 0.14,
                "base_content": text_content,
                "bold_width": 0.0,
                "border_alpha": 1.0,
                "border_color": "",
                "border_width": 0.08,
                "caption_template_info": {
                    "category_id": "",
                    "category_name": "",
                    "effect_id": "",
                    "is_new": False,
                    "path": "",
                    "request_id": "",
                    "resource_id": "",
                    "resource_name": "",
                    "source_platform": 0
                },
                "check_flag": 7,
                "combo_info": {"text_templates": []},
                "content": json.dumps({
                    "text": text_content,
                    "styles": [{
                        "size": 6,
                        "font": {
                            "path": "C:/Users/Administrator/AppData/Local/JianyingPro/Apps/5.9.0.11632/Resources/Font/SystemFont/zh-hans.ttf",
                            "id": ""
                        },
                        "fill": {
                            "content": {
                                "solid": {
                                    "color": [0.13, 0.63, 0.24]
                                }
                            }
                        },
                        "range": [0, len(text_content)]
                    }]
                }, ensure_ascii=False),
                "fixed_height": -1.0,
                "fixed_width": -1.0,
                "font_category_id": "",
                "font_category_name": "",
                "font_id": "",
                "font_name": "",
                "font_path": "C:/Users/Administrator/AppData/Local/JianyingPro/Apps/5.9.0.11632/Resources/Font/SystemFont/zh-hans.ttf",
                "font_resource_id": "",
                "font_size": 6.0,
                "font_source_platform": 0,
                "font_team_id": "",
                "font_title": "none",
                "font_url": "",
                "fonts": [],
                "force_apply_line_max_width": False,
                "global_alpha": 1.0,
                "group_id": "",
                "has_shadow": False,
                "id": new_text_id,
                "initial_scale": 1.0,
                "inner_padding": -1.0,
                "is_rich_text": False,
                "italic_degree": 0,
                "ktv_color": "",
                "language": "",
                "layer_weight": 1,
                "letter_spacing": 0.0,
                "line_feed": 1,
                "line_max_width": 0.82,
                "line_spacing": 0.02,
                "multi_language_current": "none",
                "name": "",
                "original_size": [],
                "preset_category": "",
                "preset_category_id": "",
                "preset_has_set_alignment": False,
                "preset_id": "",
                "preset_index": 0,
                "preset_name": "",
                "recognize_task_id": "",
                "recognize_type": 0,
                "relevance_segment": [],
                "shadow_alpha": 0.9,
                "shadow_angle": -45.0,
                "shadow_color": "",
                "shadow_distance": 5.0,
                "shadow_point": {"x": 0.6363961030678928, "y": -0.6363961030678928},
                "shadow_smoothing": 0.45,
                "shape_clip_x": False,
                "shape_clip_y": False,
                "source_from": "",
                "style_name": "",
                "sub_type": 0,
                "subtitle_keywords": None,
                "subtitle_template_original_fontsize": 0.0,
                "text_alpha": 1.0,
                "text_color": "#22A23E",
                "text_curve": None,
                "text_preset_resource_id": "",
                "text_size": 12,
                "text_to_audio_ids": [],
                "tts_auto_update": False,
                "type": "text",
                "typesetting": 0,
                "underline": False,
                "underline_offset": 0.22,
                "underline_width": 0.05,
                "use_effect_default_color": True,
                "words": {"end_time": [], "start_time": [], "text": []}
            }
            
            # 添加到材料列表
            if "materials" not in self.draft_data:
                self.draft_data["materials"] = {}
            if "texts" not in self.draft_data["materials"]:
                self.draft_data["materials"]["texts"] = []
            
            self.draft_data["materials"]["texts"].append(new_text)
            
            # 创建轨道段
            new_segment = {
                "id": str(uuid.uuid4()),
                "material_id": new_text_id,
                "target_timerange": {
                    "start": start_time,
                    "duration": duration_us
                },
                "clip": {
                    "transform": {
                        "x": 0,
                        "y": 0
                    },
                    "rotation": 0
                }
            }
            
            # 添加到文本轨道
            text_track = None
            for track in self.draft_data.get("tracks", []):
                if track.get("type") == "text":
                    text_track = track
                    break
            
            if not text_track:
                text_track = {
                    "id": str(uuid.uuid4()),
                    "type": "text",
                    "segments": []
                }
                if "tracks" not in self.draft_data:
                    self.draft_data["tracks"] = []
                self.draft_data["tracks"].append(text_track)
            
            text_track["segments"].append(new_segment)
            
            # 更新总时长显示
            self.update_duration_display()
            
            return new_text_id
            
        except Exception as e:
            raise Exception(f"创建文本失败: {str(e)}")
                
    def save_file(self):
        """保存文件"""
        if not self.draft_data or not self.draft_file_path:
            from qfluentwidgets import MessageBox
            MessageBox("错误", "没有可保存的文件", self).exec()
            return
            
        try:
            # 保存前自动计算并更新总时长
            self.update_project_duration()
            
            with open(self.draft_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.draft_data, f, ensure_ascii=False, indent=2)
                
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
            from qfluentwidgets import MessageBox
            MessageBox("错误", f"保存文件失败: {str(e)}", self).exec()
            
    def get_text_timeline_data(self):
        """获取文本时间轴数据"""
        if not self.draft_data:
            return []
            
        texts = self.draft_data.get("materials", {}).get("texts", [])
        tracks = self.draft_data.get("tracks", [])
        
        timeline_data = []
        
        for text in texts:
            text_id = text.get("id")
            content_data = json.loads(text.get("content", "{}"))
            text_content = content_data.get("text", "")
            
            # 查找对应的时间轴信息
            for track in tracks:
                if track.get("type") == "text":
                    segments = track.get("segments", [])
                    for segment in segments:
                        if segment.get("material_id") == text_id:
                            timerange = segment.get("target_timerange", {})
                            start_time = timerange.get("start", 0)
                            duration = timerange.get("duration", 3000000)
                            end_time = start_time + duration
                            
                            timeline_data.append({
                                "text": text_content,
                                "start_ms": start_time // 1000,  # 转换为毫秒
                                "end_ms": end_time // 1000,
                                "start_us": start_time,  # 保留微秒用于精确计算
                                "end_us": end_time
                            })
                            break
        
        # 按开始时间排序
        timeline_data.sort(key=lambda x: x["start_ms"])
        return timeline_data
        
    def ms_to_srt_time(self, ms):
        """将毫秒转换为SRT时间格式 (HH:MM:SS,mmm)"""
        hours = ms // 3600000
        minutes = (ms % 3600000) // 60000
        seconds = (ms % 60000) // 1000
        milliseconds = ms % 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
        
    def ms_to_lrc_time(self, ms):
        """将毫秒转换为LRC时间格式 [MM:SS.xx]"""
        minutes = ms // 60000
        seconds = (ms % 60000) // 1000
        centiseconds = (ms % 1000) // 10
        return f"[{minutes:02d}:{seconds:02d}.{centiseconds:02d}]"
        
    def ms_to_ass_time(self, ms):
        """将毫秒转换为ASS时间格式 (H:MM:SS.cc)"""
        hours = ms // 3600000
        minutes = (ms % 3600000) // 60000
        seconds = (ms % 60000) // 1000
        centiseconds = (ms % 1000) // 10
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"
        
    def export_srt(self):
        """导出SRT字幕文件"""
        if not self.draft_data:
            from qfluentwidgets import MessageBox
            MessageBox("错误", "请先加载剪映工程文件", self).exec()
            return
            
        timeline_data = self.get_text_timeline_data()
        if not timeline_data:
            from qfluentwidgets import MessageBox
            MessageBox("提示", "没有找到文本数据", self).exec()
            return
            
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出SRT字幕", 
            os.path.splitext(self.draft_file_path)[0] + ".srt" if self.draft_file_path else "subtitle.srt",
            "SRT字幕文件 (*.srt)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for i, item in enumerate(timeline_data, 1):
                    start_time = self.ms_to_srt_time(item["start_ms"])
                    end_time = self.ms_to_srt_time(item["end_ms"])
                    text = item["text"]  # 保持原始换行符
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")
                    
            InfoBar.success(
                title="导出成功",
                content=f"SRT字幕已导出到: {file_path}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            from qfluentwidgets import MessageBox
            MessageBox("错误", f"导出SRT失败: {str(e)}", self).exec()
            
    def export_lrc(self):
        """导出LRC歌词文件"""
        if not self.draft_data:
            MessageBox("错误", "请先加载剪映工程文件", self).exec()
            return
            
        timeline_data = self.get_text_timeline_data()
        if not timeline_data:
            MessageBox("提示", "没有找到文本数据", self).exec()
            return
            
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出LRC歌词", 
            os.path.splitext(self.draft_file_path)[0] + ".lrc" if self.draft_file_path else "lyrics.lrc",
            "LRC歌词文件 (*.lrc)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 写入LRC头信息
                f.write("[ti:]\n")  # 标题
                f.write("[ar:]\n")  # 艺术家
                f.write("[al:]\n")  # 专辑
                f.write("[by:剪映文本编辑器]\n")  # 制作者
                f.write("[offset:0]\n\n")  # 时间偏移
                
                for item in timeline_data:
                    time_tag = self.ms_to_lrc_time(item["start_ms"])
                    text = item["text"].replace('\n', ' ')  # LRC通常不支持多行，用空格替换换行
                    f.write(f"{time_tag}{text}\n")
                    
            InfoBar.success(
                title="导出成功",
                content=f"LRC歌词已导出到: {file_path}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            MessageBox("错误", f"导出LRC失败: {str(e)}", self).exec()
            
    def export_ass(self):
        """导出ASS字幕文件"""
        if not self.draft_data:
            MessageBox("错误", "请先加载剪映工程文件", self).exec()
            return
            
        timeline_data = self.get_text_timeline_data()
        if not timeline_data:
            MessageBox("提示", "没有找到文本数据", self).exec()
            return
            
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出ASS字幕", 
            os.path.splitext(self.draft_file_path)[0] + ".ass" if self.draft_file_path else "subtitle.ass",
            "ASS字幕文件 (*.ass)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 写入ASS文件头
                f.write("[Script Info]\n")
                f.write("Title: 剪映导出字幕\n")
                f.write("ScriptType: v4.00+\n")
                f.write("WrapStyle: 0\n")
                f.write("ScaledBorderAndShadow: yes\n")
                f.write("YCbCr Matrix: TV.601\n")
                f.write("PlayResX: 1920\n")
                f.write("PlayResY: 1080\n\n")
                
                # 样式定义
                f.write("[V4+ Styles]\n")
                f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                f.write("Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1\n\n")
                
                # 事件
                f.write("[Events]\n")
                f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                
                for item in timeline_data:
                    start_time = self.ms_to_ass_time(item["start_ms"])
                    end_time = self.ms_to_ass_time(item["end_ms"])
                    text = item["text"].replace('\n', '\\N')  # ASS使用\N表示换行
                    
                    f.write(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n")
                    
            InfoBar.success(
                title="导出成功",
                content=f"ASS字幕已导出到: {file_path}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            MessageBox("错误", f"导出ASS失败: {str(e)}", self).exec()
    
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
            print(f"已更新工程文件总时长: {total_duration/1000000:.2f}秒 ({total_duration}微秒)")