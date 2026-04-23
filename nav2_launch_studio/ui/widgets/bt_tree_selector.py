"""BT 树选择器组件 - 为 Nav2 选择行为树 XML 文件。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QRadioButton, QButtonGroup,
    QPushButton, QFileDialog, QLabel,
)
from PySide6.QtCore import Signal


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
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # 模板列表
        label = QLabel("BT 行为树")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self._on_template_selected)
        layout.addWidget(self.template_list)

        # 自定义文件选择
        custom_layout = QHBoxLayout()
        self.custom_radio = QRadioButton("自定义 BT 树")
        self.custom_path_label = QLabel("")
        self.custom_browse_btn = QPushButton("浏览...")
        self.custom_browse_btn.clicked.connect(self._on_browse_custom)
        custom_layout.addWidget(self.custom_radio)
        custom_layout.addWidget(self.custom_path_label, stretch=1)
        custom_layout.addWidget(self.custom_browse_btn)
        layout.addLayout(custom_layout)

        # Groot2 预览按钮
        self.groot2_btn = QPushButton("在 Groot2 中预览")
        self.groot2_btn.setVisible(False)  # 检测到 Groot2 后才显示
        self.groot2_btn.clicked.connect(self._on_groot2_preview)
        layout.addWidget(self.groot2_btn)

    def load_builtin_templates(self, template_dir):
        """扫描并填充内置 BT 树模板。

        参数：
            template_dir: nav2_bt_navigator/behavior_trees/ 的路径
        """
        # TODO: 扫描目录中的 .xml 文件，填充 template_list
        pass

    def detect_groot2(self):
        """检测系统中是否安装了 Groot2。"""
        # TODO: 检查 groot2 可执行文件，显示/隐藏按钮
        pass

    def _on_template_selected(self, current, previous):
        """处理模板选择事件。"""
        if current and not self.custom_radio.isChecked():
            self.custom_radio.setChecked(False)
            self.bt_tree_changed.emit(current.data())

    def _on_browse_custom(self):
        """打开文件对话框选择自定义 BT 树。"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 BT 树文件", "", "XML 文件 (*.xml)"
        )
        if path:
            self.custom_radio.setChecked(True)
            self.custom_path_label.setText(path)
            self.bt_tree_changed.emit(path)

    def _on_groot2_preview(self):
        """在 Groot2 中打开当前 BT 树。"""
        # TODO: 调用 subprocess 启动 groot2
        pass
