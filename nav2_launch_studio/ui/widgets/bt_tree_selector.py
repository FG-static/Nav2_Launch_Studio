"""BT 树选择器组件 - 为 Nav2 选择行为树 XML 文件。"""

import subprocess

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QRadioButton, QButtonGroup,
    QPushButton, QFileDialog, QLabel,
)
from PySide6.QtCore import Qt, Signal

from nav2_launch_studio.utils.bt_tree_discovery import BTTreeDiscovery


class BTTreeSelectorWidget(QWidget):
    """Nav2 配置的 BT 树文件选择器。

    对应 PRD 3.6：
    - 卡片/列表展示内置 BT 模板（动态扫描）
    - 自定义 BT 树文件选择
    - 选中模板后自动填写 bt_navigator 的 default_bt_xml_filename
    - Groot2 预览按钮（Groot2 未安装时隐藏）
    """

    # 信号
    bt_tree_changed = Signal(str)  # BT 树文件名或路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self._discovery = BTTreeDiscovery()
        self._templates: list[str] = []
        self._current_tree = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # 标题
        label = QLabel("BT 行为树")
        label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(label)

        # 模板列表
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self._on_template_selected)
        layout.addWidget(self.template_list)

        # 自定义文件选择
        custom_layout = QHBoxLayout()
        self.custom_radio = QRadioButton("自定义 BT 树")
        self.custom_radio.toggled.connect(self._on_custom_toggled)
        self.custom_path_label = QLabel("")
        self.custom_path_label.setStyleSheet("color: #666;")
        self.custom_browse_btn = QPushButton("浏览...")
        self.custom_browse_btn.clicked.connect(self._on_browse_custom)
        custom_layout.addWidget(self.custom_radio)
        custom_layout.addWidget(self.custom_path_label, stretch=1)
        custom_layout.addWidget(self.custom_browse_btn)
        layout.addLayout(custom_layout)

        # Groot2 预览按钮
        self.groot2_btn = QPushButton("在 Groot2 中预览")
        self.groot2_btn.setVisible(False)
        self.groot2_btn.clicked.connect(self._on_groot2_preview)
        layout.addWidget(self.groot2_btn)

    def load_builtin_templates(self):
        """扫描并填充内置 BT 树模板。"""
        self.template_list.clear()
        self._templates.clear()

        template_dir = self._discovery.discover_template_dir()
        if not template_dir:
            item = QListWidgetItem("未找到 BT 树模板目录")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            item.setForeground(Qt.gray)
            self.template_list.addItem(item)
            return

        templates = self._discovery.list_templates()
        self._templates = templates

        if not templates:
            item = QListWidgetItem("模板目录为空")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            item.setForeground(Qt.gray)
            self.template_list.addItem(item)
            return

        for name in templates:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, name)
            self.template_list.addItem(item)

    def detect_groot2(self):
        """检测系统中是否安装了 Groot2。"""
        available = self._discovery.check_groot2_available()
        self.groot2_btn.setVisible(available)

    def set_current_tree(self, bt_tree: str):
        """设置当前选中的 BT 树。

        参数：
            bt_tree: BT 树文件名（如 "navigate_to_pose_w_replanning_and_recovery.xml"）
        """
        self._current_tree = bt_tree

        # 先在内置模板中查找
        for i in range(self.template_list.count()):
            item = self.template_list.item(i)
            name = item.data(Qt.UserRole)
            if name == bt_tree:
                self.template_list.setCurrentItem(item)
                self.custom_radio.setChecked(False)
                return

        # 未找到，设置为自定义
        if bt_tree:
            self.custom_radio.setChecked(True)
            self.custom_path_label.setText(bt_tree)

    def get_current_tree(self) -> str:
        """返回当前选中的 BT 树文件名。"""
        return self._current_tree

    def _on_template_selected(self, current, previous):
        """处理模板选择事件。"""
        if current and not self.custom_radio.isChecked():
            name = current.data(Qt.UserRole)
            if name:
                self._current_tree = name
                self.bt_tree_changed.emit(name)

    def _on_custom_toggled(self, checked):
        """自定义模式切换。"""
        if checked:
            self.template_list.clearSelection()
            path = self.custom_path_label.text()
            if path:
                self._current_tree = path
                self.bt_tree_changed.emit(path)

    def _on_browse_custom(self):
        """打开文件对话框选择自定义 BT 树。"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 BT 树文件", "", "XML 文件 (*.xml)"
        )
        if path:
            self.custom_radio.setChecked(True)
            self.custom_path_label.setText(path)
            self._current_tree = path
            self.bt_tree_changed.emit(path)

    def _on_groot2_preview(self):
        """在 Groot2 中打开当前 BT 树。"""
        if not self._current_tree:
            return

        # 获取 BT 树完整路径
        full_path = self._discovery.get_template_path(self._current_tree)
        if not full_path:
            full_path = self._current_tree  # 可能是自定义路径

        # 获取 Groot2 可执行文件路径（支持 AppImage）
        groot2_cmd = self._discovery.get_groot2_path() or "groot2"

        try:
            subprocess.Popen([groot2_cmd, full_path])
        except FileNotFoundError:
            pass
