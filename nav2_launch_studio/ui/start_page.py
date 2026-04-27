"""启动页 / 项目列表 - 应用启动时显示。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QFileDialog,
)
from PySide6.QtCore import Qt, Signal


class StartPageWidget(QWidget):
    """启动页，显示项目列表及新建/导入按钮。

    对应 PRD 4.1：按 updated_at 排序显示最近项目，
    提供"新建项目"和"导入项目"按钮。
    """

    # 信号
    new_project_requested = Signal()
    open_project_requested = Signal(str)  # 项目目录路径
    project_selected = Signal(str)        # 双击选中项目目录路径
    import_yaml_requested = Signal(str)   # YAML 文件路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("Nav2 Launch Studio")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.new_project_btn = QPushButton("新建项目")
        self.import_project_btn = QPushButton("导入项目")
        self.open_project_btn = QPushButton("打开项目")
        self.new_project_btn.clicked.connect(self.new_project_requested.emit)
        self.import_project_btn.clicked.connect(self._on_import_project)
        self.open_project_btn.clicked.connect(self._on_open_project)
        btn_layout.addWidget(self.new_project_btn)
        btn_layout.addWidget(self.import_project_btn)
        btn_layout.addWidget(self.open_project_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 最近项目
        layout.addWidget(QLabel("最近项目："))
        self.project_list = QListWidget()
        self.project_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.project_list)

    def load_recent_projects(self, projects):
        """加载并显示最近项目列表。

        参数：
            projects: (项目名, 项目目录, 更新时间) 元组列表
        """
        self.project_list.clear()
        for name, proj_dir, updated in projects:
            self.add_project_item(name, proj_dir, updated)

    def add_project_item(self, name, proj_dir, updated):
        """向列表添加一个项目条目。"""
        item = QListWidgetItem(f"{name}  |  {updated}")
        item.setData(Qt.UserRole, proj_dir)  # 存储项目目录路径
        self.project_list.addItem(item)

    def _on_item_double_clicked(self, item):
        """双击项目条目时发出 project_selected 信号。"""
        proj_dir = item.data(Qt.UserRole)
        if proj_dir:
            self.project_selected.emit(proj_dir)

    def _on_open_project(self):
        """点击"打开项目"按钮时弹出目录选择对话框。"""
        proj_dir = QFileDialog.getExistingDirectory(
            self, "选择项目目录", "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if proj_dir:
            self.open_project_requested.emit(proj_dir)

    def _on_import_project(self):
        """点击"导入项目"按钮时弹出 YAML 文件选择对话框。"""
        yaml_path, _ = QFileDialog.getOpenFileName(
            self, "选择 nav2_params.yaml", "",
            "YAML 文件 (*.yaml *.yml);;所有文件 (*)",
        )
        if yaml_path:
            self.import_yaml_requested.emit(yaml_path)
