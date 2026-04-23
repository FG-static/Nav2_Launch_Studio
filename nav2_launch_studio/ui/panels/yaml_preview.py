"""YAML 预览组件 - 实时预览生成的 nav2_params.yaml。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QToolBar,
    QPushButton, QFileDialog,
)
from PySide6.QtCore import Signal


class YamlPreviewWidget(QWidget):
    """实时 YAML 预览与导出面板。

    对应 PRD 3.7：
    - 实时 nav2_params.yaml 预览
    - 复制到剪贴板
    - 导出到文件（工作空间包 config/ 或自定义路径）
    """

    # 信号
    export_requested = Signal(str)  # 导出路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 工具栏
        toolbar = QToolBar()
        self.copy_btn = QPushButton("复制")
        self.export_btn = QPushButton("导出 YAML")
        self.export_btn.clicked.connect(self._on_export)
        toolbar.addWidget(self.copy_btn)
        toolbar.addWidget(self.export_btn)
        layout.addWidget(toolbar)

        # YAML 文本显示
        self.yaml_edit = QTextEdit()
        self.yaml_edit.setReadOnly(True)
        self.yaml_edit.setFontFamily("Monospace")
        layout.addWidget(self.yaml_edit)

    def update_preview(self, yaml_text):
        """更新 YAML 预览内容。"""
        self.yaml_edit.setPlainText(yaml_text)

    def _on_export(self):
        """导出 YAML 到文件。"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 nav2_params.yaml",
            "nav2_params.yaml",
            "YAML 文件 (*.yaml *.yml)"
        )
        if path:
            self.export_requested.emit(path)
