"""自定义插件键值编辑器 - 手动编辑自定义插件的参数。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QComboBox, QPushButton, QHeaderView,
    QDialog, QTextEdit, QMessageBox,
)
from PySide6.QtCore import Signal


class KeyValueEditorWidget(QWidget):
    """自定义插件的键值对参数编辑器。

    对应 PRD 3.5.2：
    - 手动键值对编辑
    - 列：参数名、参数值、类型、备注
    - 添加/删除/排序按钮
    - 粘贴 YAML 导入快捷方式
    """

    # 信号
    params_changed = Signal(list)  # {key, value, dtype, note} 字典列表

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 按钮栏
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("＋ 添加参数")
        self.add_btn.clicked.connect(self._on_add_param)
        self.delete_btn = QPushButton("🗑 删除")
        self.delete_btn.clicked.connect(self._on_delete_param)
        self.yaml_import_btn = QPushButton("粘贴 YAML 导入")
        self.yaml_import_btn.clicked.connect(self._on_yaml_import)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.yaml_import_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 表格
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["参数名", "参数值", "类型", "备注"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def load_params(self, params):
        """将键值对参数加载到表格中。

        参数：
            params: 包含 key、value、dtype、note 的字典列表
        """
        self.table.setRowCount(0)
        for p in params:
            self._add_row(p.get("key", ""), p.get("value", ""),
                          p.get("dtype", "string"), p.get("note", ""))

    def get_params(self):
        """以字典列表形式返回参数。"""
        params = []
        for row in range(self.table.rowCount()):
            params.append({
                "key": self.table.item(row, 0).text() if self.table.item(row, 0) else "",
                "value": self.table.item(row, 1).text() if self.table.item(row, 1) else "",
                "dtype": self.table.cellWidget(row, 2).currentText() if self.table.cellWidget(row, 2) else "string",
                "note": self.table.item(row, 3).text() if self.table.item(row, 3) else "",
            })
        return params

    def _add_row(self, key="", value="", dtype="string", note=""):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(key))
        self.table.setItem(row, 1, QTableWidgetItem(value))
        dtype_combo = QComboBox()
        dtype_combo.addItems(["string", "int", "float", "bool", "list"])
        dtype_combo.setCurrentText(dtype)
        self.table.setCellWidget(row, 2, dtype_combo)
        self.table.setItem(row, 3, QTableWidgetItem(note))

    def _on_add_param(self):
        self._add_row()

    def _on_delete_param(self):
        rows = set(i.row() for i in self.table.selectedItems())
        for row in sorted(rows, reverse=True):
            self.table.removeRow(row)

    def _on_yaml_import(self):
        """打开对话框粘贴 YAML 并导入为键值对。"""
        dialog = QDialog(self)
        dialog.setWindowTitle("粘贴 YAML 导入")
        dlayout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("粘贴插件参数 YAML 片段...")
        dlayout.addWidget(text_edit)
        import_btn = QPushButton("导入")
        import_btn.clicked.connect(dialog.accept)
        dlayout.addWidget(import_btn)

        if dialog.exec() == QDialog.Accepted:
            # TODO: 解析 YAML 文本，填充表格行
            pass
