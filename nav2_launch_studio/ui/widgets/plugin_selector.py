"""插件选择器组件 - 为各分类选择 Nav2 插件。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QComboBox,
    QListWidget, QListWidgetItem, QCheckBox,
    QPushButton, QDialog, QFormLayout, QLineEdit,
    QTabWidget, QLabel,
)
from PySide6.QtCore import Signal


class PluginSelectorWidget(QWidget):
    """Nav2 组件的插件选择器。

    对应 PRD 3.5：
    - 分组选择：规划器、控制器、平滑器、代价地图层、Recovery
    - 代价地图层分为全局/局部两组
    - 内置插件含描述 + 自定义插件注册
    - 自定义插件：手动键值对参数编辑
    """

    # 信号
    plugin_changed = Signal(str, str)  # 分类, 插件ID

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 标签页界面展示插件分类
        self.tabs = QTabWidget()

        # 全局规划器
        self.planner_group = PluginGroupWidget("全局规划器", multi_select=False)
        self.tabs.addTab(self.planner_group, "规划器")

        # 控制器
        self.controller_group = PluginGroupWidget("控制器", multi_select=False)
        self.tabs.addTab(self.controller_group, "控制器")

        # 路径平滑器
        self.smoother_group = PluginGroupWidget("路径平滑器", multi_select=False)
        self.tabs.addTab(self.smoother_group, "平滑器")

        # 代价地图层（分全局/局部）
        costmap_widget = QWidget()
        costmap_layout = QVBoxLayout(costmap_widget)
        self.global_costmap_group = PluginGroupWidget("全局代价地图层", multi_select=True)
        self.local_costmap_group = PluginGroupWidget("局部代价地图层", multi_select=True)
        costmap_layout.addWidget(self.global_costmap_group)
        costmap_layout.addWidget(self.local_costmap_group)
        self.tabs.addTab(costmap_widget, "代价地图")

        # Recovery 行为
        self.recovery_group = PluginGroupWidget("Recovery", multi_select=True)
        self.tabs.addTab(self.recovery_group, "Recovery")

        layout.addWidget(self.tabs)

    def load_plugins(self, plugin_registry):
        """从注册表填充插件列表。

        参数：
            plugin_registry: 包含内置和自定义插件的 PluginRegistry 实例
        """
        # TODO: 从注册表数据填充各分组
        pass

    def get_selected_plugins(self):
        """返回当前各分类选中的插件字典（detail 格式）。

        返回格式：
        {
            "planner": {"instance_name": ..., "plugin_type": ..., "params": {}},
            "controller": {...},
            "smoother": {...},
            "global_costmap_layers": [{...}, ...],
            "local_costmap_layers": [{...}, ...],
            "recovery_behaviors": [{...}, ...],
        }
        """
        # TODO: 待 load_plugins() 实现后，从选项数据中获取 plugin_type
        return {
            "planner": self.planner_group.get_selected_detail(),
            "controller": self.controller_group.get_selected_detail(),
            "smoother": self.smoother_group.get_selected_detail(),
            "global_costmap_layers": self.global_costmap_group.get_selected_details(),
            "local_costmap_layers": self.local_costmap_group.get_selected_details(),
            "recovery_behaviors": self.recovery_group.get_selected_details(),
        }


class PluginGroupWidget(QGroupBox):
    """一组插件（单选或多选）。"""

    def __init__(self, title, multi_select=False, parent=None):
        super().__init__(title, parent)
        self.multi_select = multi_select
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        if self.multi_select:
            self.list_widget = QListWidget()
            layout.addWidget(self.list_widget)
        else:
            self.combo = QComboBox()
            layout.addWidget(self.combo)

        self.add_custom_btn = QPushButton("✚ 添加自定义插件")
        self.add_custom_btn.clicked.connect(self._on_add_custom)
        layout.addWidget(self.add_custom_btn)

    def add_plugin(self, plugin_id, display_name, description=""):
        """添加一个插件选项。"""
        if self.multi_select:
            item = QListWidgetItem(display_name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, plugin_id)
            self.list_widget.addItem(item)
        else:
            self.combo.addItem(display_name, plugin_id)

    def get_selected(self):
        """返回选中的插件 ID。"""
        if self.multi_select:
            selected = []
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.checkState() == Qt.Checked:
                    selected.append(item.data(Qt.UserRole))
            return selected
        else:
            return self.combo.currentData()

    def get_selected_detail(self):
        """返回单选插件的详情字典。"""
        data = self.combo.currentData()
        if isinstance(data, dict):
            return data
        # 旧格式：仅 ID 字符串，返回占位
        if data:
            return {"instance_name": "", "plugin_type": data, "params": {}}
        return None

    def get_selected_details(self):
        """返回多选插件的详情列表。"""
        result = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                data = item.data(Qt.UserRole)
                if isinstance(data, dict):
                    result.append(data)
                elif data:
                    result.append({"instance_name": "", "plugin_type": data, "params": {}})
        return result

    def _on_add_custom(self):
        """打开自定义插件注册对话框。"""
        dialog = CustomPluginDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # TODO: 通过 PluginRegistry 注册自定义插件
            pass


class CustomPluginDialog(QDialog):
    """自定义插件注册对话框（对应 PRD 3.5.1）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加自定义插件")
        layout = QFormLayout(self)

        self.display_name_edit = QLineEdit()
        self.plugin_type_edit = QLineEdit()
        self.plugin_type_edit.setPlaceholderText("如 my_pkg/MyPlanner")
        self.instance_name_edit = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "规划器", "控制器", "平滑器", "代价地图层", "Recovery"
        ])
        self.description_edit = QLineEdit()

        layout.addRow("显示名称：", self.display_name_edit)
        layout.addRow("插件类型名：", self.plugin_type_edit)
        layout.addRow("实例名：", self.instance_name_edit)
        layout.addRow("分类：", self.category_combo)
        layout.addRow("备注：", self.description_edit)
