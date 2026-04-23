"""启动页 / 项目列表 - 应用启动时显示。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel,
)


class StartPageWidget(QWidget):
    """启动页，显示项目列表及新建/导入按钮。

    对应 PRD 4.1：按 updated_at 排序显示最近项目，
    提供"新建项目"和"导入项目"按钮。
    """

    def __init__(self, parent=None):
        super().__init__(parent) # super的意思是调用父类的__init__方法
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
        btn_layout.addWidget(self.new_project_btn)
        btn_layout.addWidget(self.import_project_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 最近项目
        layout.addWidget(QLabel("最近项目："))
        self.project_list = QListWidget()
        layout.addWidget(self.project_list)

    def load_recent_projects(self):
        """加载并显示最近项目列表。"""
        # TODO: 扫描项目目录，按 updated_at 排序，填充列表
        pass

    def add_project_item(self, name, robot_type, ros_version, updated):
        """向列表添加一个项目条目。"""
        item = QListWidgetItem(f"{name}  |  {robot_type}  |  {ros_version}  |  {updated}")
        self.project_list.addItem(item)
