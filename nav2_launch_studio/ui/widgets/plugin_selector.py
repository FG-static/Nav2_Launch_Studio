"""插件选择器组件 - 为各分类选择 Nav2 插件。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QComboBox,
    QListWidget, QListWidgetItem, QCheckBox,
    QPushButton, QDialog, QFormLayout, QLineEdit,
    QTabWidget, QLabel,
)
from PySide6.QtCore import Qt, Signal


class PluginSelectorWidget(QWidget):
    """Nav2 组件的插件选择器。

    对应 PRD 3.5：
    - 分组选择：规划器、控制器、平滑器、代价地图层、Recovery
    - 代价地图层分为全局/局部两组
    - 内置插件含描述 + 自定义插件注册
    - 自定义插件：手动键值对参数编辑

    tab 管理采用与 node_graph 相同的模式：
    遍历实际项目数据，只为存在的插件类别创建 tab。
    """

    # 信号
    plugin_changed = Signal(str, str)  # 分类, 插件ID

    def __init__(self, parent=None):
        super().__init__(parent)
        self._plugin_registry = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

    def load_plugins(self, plugin_registry, plugins: dict = None):
        """从注册表填充插件列表，并根据项目数据动态创建 tab。

        遍历实际项目插件数据，只为有数据的类别添加 tab。
        与 node_graph.load_nodes 模式一致：数据驱动 UI 创建。

        参数：
            plugin_registry: PluginRegistry 实例
            plugins: ProjectModel.plugins 字典（决定哪些 tab 需要显示）
        """
        self._plugin_registry = plugin_registry

        # 清空所有 tab
        self.tabs.clear()

        # planner（始终显示）
        self.planner_group = PluginGroupWidget("全局规划器", multi_select=False, category="planner")
        self.planner_group.plugin_changed.connect(
            lambda pid: self.plugin_changed.emit("planner", pid))
        self._fill_group(self.planner_group, plugin_registry.BUILTIN_PLANNERS)
        self.tabs.addTab(self.planner_group, "规划器")

        # controller（始终显示）
        self.controller_group = PluginGroupWidget("控制器", multi_select=False, category="controller")
        self.controller_group.plugin_changed.connect(
            lambda pid: self.plugin_changed.emit("controller", pid))
        self._fill_group(self.controller_group, plugin_registry.BUILTIN_CONTROLLERS)
        self.tabs.addTab(self.controller_group, "控制器")

        # smoother（按数据添加）
        smoother_data = plugins.get("smoother") if plugins else None
        if isinstance(smoother_data, dict) and smoother_data.get("plugin_type"):
            self.smoother_group = PluginGroupWidget("路径平滑器", multi_select=False, category="smoother")
            self.smoother_group.plugin_changed.connect(
                lambda pid: self.plugin_changed.emit("smoother", pid))
            self._fill_group(self.smoother_group, plugin_registry.BUILTIN_SMOOTHERS)
            self.tabs.addTab(self.smoother_group, "平滑器")

        # costmap（按数据添加）
        global_layers = plugins.get("global_costmap_layers") if plugins else None
        local_layers = plugins.get("local_costmap_layers") if plugins else None
        has_costmap = (
            (isinstance(global_layers, list) and len(global_layers) > 0)
            or (isinstance(local_layers, list) and len(local_layers) > 0)
        )
        if has_costmap:
            costmap_widget = QWidget()
            costmap_layout = QVBoxLayout(costmap_widget)
            costmap_layout.setContentsMargins(0, 0, 0, 0)
            self.global_costmap_group = PluginGroupWidget("全局代价地图层", multi_select=True, category="costmap_layer")
            self.local_costmap_group = PluginGroupWidget("局部代价地图层", multi_select=True, category="costmap_layer")
            self._fill_costmap_group(self.global_costmap_group, plugin_registry.BUILTIN_COSTMAP_LAYERS)
            self._fill_costmap_group(self.local_costmap_group, plugin_registry.BUILTIN_COSTMAP_LAYERS)
            costmap_layout.addWidget(self.global_costmap_group)
            costmap_layout.addWidget(self.local_costmap_group)
            self.tabs.addTab(costmap_widget, "代价地图")

        # recovery（按数据添加）
        recovery_data = plugins.get("recovery_behaviors") if plugins else None
        if isinstance(recovery_data, list) and len(recovery_data) > 0:
            self.recovery_group = PluginGroupWidget("Recovery", multi_select=True, category="recovery")
            self._fill_group(self.recovery_group, plugin_registry.BUILTIN_RECOVERIES)
            self.tabs.addTab(self.recovery_group, "Recovery")

        # 填充自定义插件到对应分组
        self._fill_custom_plugins(plugin_registry)

    def _fill_group(self, group: 'PluginGroupWidget', registry_dict: dict):
        """从注册表字典填充单选/多选分组。"""
        for pid, info in registry_dict.items():
            group.add_plugin(
                pid, info["display_name"], info.get("description", ""),
                {"instance_name": info.get("instance_name", pid), "plugin_type": info["plugin_type"], "params": {}},
            )

    def _fill_costmap_group(self, group: 'PluginGroupWidget', registry_dict: dict):
        """填充代价地图层分组。"""
        for pid, info in registry_dict.items():
            detail = {"instance_name": pid + "_layer", "plugin_type": info["plugin_type"], "params": {}}
            group.add_plugin(pid, info["display_name"], info.get("description", ""), detail)

    def _fill_custom_plugins(self, plugin_registry):
        """将自定义插件填充到对应分组。"""
        for cp in plugin_registry.get_custom_plugins():
            cat = cp.get("category", "")
            detail = {"instance_name": cp["instance_name"], "plugin_type": cp["plugin_type"], "params": {}}
            display = f"🔧 {cp['display_name']}"
            if cat == "planner" and hasattr(self, 'planner_group'):
                self.planner_group.add_plugin(cp["instance_name"], display, cp.get("description", ""), detail)
            elif cat == "controller" and hasattr(self, 'controller_group'):
                self.controller_group.add_plugin(cp["instance_name"], display, cp.get("description", ""), detail)
            elif cat == "smoother" and hasattr(self, 'smoother_group'):
                self.smoother_group.add_plugin(cp["instance_name"], display, cp.get("description", ""), detail)
            elif cat == "costmap_layer":
                if hasattr(self, 'global_costmap_group'):
                    self.global_costmap_group.add_plugin(cp["instance_name"], display, cp.get("description", ""), detail)
                if hasattr(self, 'local_costmap_group'):
                    self.local_costmap_group.add_plugin(cp["instance_name"], display, cp.get("description", ""), detail)
            elif cat == "recovery" and hasattr(self, 'recovery_group'):
                self.recovery_group.add_plugin(cp["instance_name"], display, cp.get("description", ""), detail)

    def set_selected_plugins(self, plugins: dict):
        """从 ProjectModel.plugins 设置各分组当前选中。"""
        if not plugins:
            return

        planner = plugins.get("planner")
        if isinstance(planner, dict) and planner.get("plugin_type") and hasattr(self, 'planner_group'):
            self.planner_group.set_selected_by_type(planner["plugin_type"], planner)

        controller = plugins.get("controller")
        if isinstance(controller, dict) and controller.get("plugin_type") and hasattr(self, 'controller_group'):
            self.controller_group.set_selected_by_type(controller["plugin_type"], controller)

        smoother = plugins.get("smoother")
        if isinstance(smoother, dict) and smoother.get("plugin_type") and hasattr(self, 'smoother_group'):
            self.smoother_group.set_selected_by_type(smoother["plugin_type"], smoother)

        global_layers = plugins.get("global_costmap_layers")
        if isinstance(global_layers, list) and hasattr(self, 'global_costmap_group'):
            self.global_costmap_group.set_checked_by_instance(global_layers)

        local_layers = plugins.get("local_costmap_layers")
        if isinstance(local_layers, list) and hasattr(self, 'local_costmap_group'):
            self.local_costmap_group.set_checked_by_instance(local_layers)

        recoveries = plugins.get("recovery_behaviors")
        if isinstance(recoveries, list) and hasattr(self, 'recovery_group'):
            self.recovery_group.set_checked_by_instance(recoveries)

    def get_selected_plugins(self) -> dict:
        """返回当前各分类选中的插件字典（detail 格式）。"""
        result = {
            "planner": self.planner_group.get_selected_detail() if hasattr(self, 'planner_group') else None,
            "controller": self.controller_group.get_selected_detail() if hasattr(self, 'controller_group') else None,
            "smoother": self.smoother_group.get_selected_detail() if hasattr(self, 'smoother_group') else None,
            "global_costmap_layers": self.global_costmap_group.get_selected_details() if hasattr(self, 'global_costmap_group') else [],
            "local_costmap_layers": self.local_costmap_group.get_selected_details() if hasattr(self, 'local_costmap_group') else [],
            "recovery_behaviors": self.recovery_group.get_selected_details() if hasattr(self, 'recovery_group') else [],
        }
        return result


class PluginGroupWidget(QGroupBox):
    """一组插件（单选或多选）。"""

    plugin_changed = Signal(str)  # 插件 ID

    def __init__(self, title, multi_select=False, category="", parent=None):
        super().__init__(title, parent)
        self.multi_select = multi_select
        self._category = category
        self._plugins: list[dict] = []
        self._custom_detail: dict = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        if self.multi_select:
            self.list_widget = QListWidget()
            self.list_widget.itemChanged.connect(self._on_item_changed)
            layout.addWidget(self.list_widget)
        else:
            self.combo = QComboBox()
            self.combo.setEditable(True)
            self.combo.setInsertPolicy(QComboBox.NoInsert)
            self.combo.currentIndexChanged.connect(self._on_combo_changed)
            layout.addWidget(self.combo)

        self.add_custom_btn = QPushButton("✚ 添加自定义插件")
        self.add_custom_btn.clicked.connect(self._on_add_custom)
        layout.addWidget(self.add_custom_btn)

    def clear(self):
        """清空所有插件选项。"""
        self._plugins.clear()
        if self.multi_select:
            self.list_widget.clear()
        else:
            self.combo.clear()

    def add_plugin(self, plugin_id, display_name, description="", detail=None):
        """添加一个插件选项。"""
        if detail is None:
            detail = {"instance_name": "", "plugin_type": plugin_id, "params": {}}
        self._plugins.append({"id": plugin_id, "detail": detail})

        if self.multi_select:
            item = QListWidgetItem(display_name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, len(self._plugins) - 1)
            item.setToolTip(description)
            self.list_widget.addItem(item)
        else:
            self.combo.addItem(display_name, len(self._plugins) - 1)
            self.combo.setItemData(self.combo.count() - 1, description, Qt.ToolTipRole)

    def set_selected_by_type(self, plugin_type: str, detail: dict = None):
        """单选模式：按 plugin_type 设置当前选中。

        先在预设中查找匹配项，无匹配则设置为自定义文本。
        参数 detail 可保留原始 instance_name 等信息。
        """
        if self.multi_select:
            return
        for i, p in enumerate(self._plugins):
            if p["detail"].get("plugin_type") == plugin_type:
                idx = self.combo.findData(i)
                if idx >= 0:
                    self.combo.setCurrentIndex(idx)
                return
        # 无匹配预设：设置为自定义文本，保存原始 detail
        self.combo.setEditText(plugin_type)
        if detail:
            self._custom_detail = dict(detail)
        else:
            self._custom_detail = {"instance_name": plugin_type, "plugin_type": plugin_type, "params": {}}

    def set_checked_by_instance(self, details_list: list):
        """多选模式：按 instance_name 列表勾选。"""
        if not self.multi_select:
            return
        instance_names = {d.get("instance_name", "") for d in details_list if isinstance(d, dict)}
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            plugin_idx = item.data(Qt.UserRole)
            if plugin_idx is not None and plugin_idx < len(self._plugins):
                inst = self._plugins[plugin_idx]["detail"].get("instance_name", "")
                item.setCheckState(Qt.Checked if inst in instance_names else Qt.Unchecked)

    def get_selected(self):
        """返回选中的插件 ID。"""
        if self.multi_select:
            selected = []
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.checkState() == Qt.Checked:
                    idx = item.data(Qt.UserRole)
                    if idx is not None and idx < len(self._plugins):
                        selected.append(self._plugins[idx]["id"])
            return selected
        else:
            idx = self.combo.currentData()
            if idx is not None and idx < len(self._plugins):
                return self._plugins[idx]["id"]
            return None

    def get_selected_detail(self):
        """返回单选插件的详情字典。"""
        if self.multi_select:
            return None
        idx = self.combo.currentData()
        if idx is not None and idx < len(self._plugins):
            return dict(self._plugins[idx]["detail"])
        # 自定义文本输入：使用保存的 detail 或从文本构造
        text = self.combo.currentText().strip()
        if text:
            if hasattr(self, '_custom_detail') and self._custom_detail.get("plugin_type") == text:
                return dict(self._custom_detail)
            return {"instance_name": text, "plugin_type": text, "params": {}}
        return None

    def get_selected_details(self):
        """返回多选插件的详情列表。"""
        result = []
        if not self.multi_select:
            return result
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                idx = item.data(Qt.UserRole)
                if idx is not None and idx < len(self._plugins):
                    result.append(dict(self._plugins[idx]["detail"]))
        return result

    def _on_combo_changed(self, index):
        """单选 combo 变化。"""
        idx = self.combo.currentData()
        if idx is not None and idx < len(self._plugins):
            self.plugin_changed.emit(self._plugins[idx]["id"])

    def _on_item_changed(self, item):
        """多选列表勾选变化。"""
        if item.checkState() == Qt.Checked:
            idx = item.data(Qt.UserRole)
            if idx is not None and idx < len(self._plugins):
                self.plugin_changed.emit(self._plugins[idx]["id"])

    def _on_add_custom(self):
        """打开自定义插件注册对话框。"""
        dialog = CustomPluginDialog(self, category=self._category)
        if dialog.exec() == QDialog.Accepted:
            display_name = dialog.display_name_edit.text().strip()
            plugin_type = dialog.plugin_type_edit.text().strip()
            instance_name = dialog.instance_name_edit.text().strip()
            category = dialog.get_category()
            description = dialog.description_edit.text().strip()

            if not display_name or not plugin_type:
                return

            if not instance_name:
                instance_name = display_name.replace(" ", "_")

            if hasattr(self, '_plugin_registry') and self._plugin_registry:
                self._plugin_registry.register_custom_plugin({
                    "display_name": display_name,
                    "plugin_type": plugin_type,
                    "instance_name": instance_name,
                    "category": category,
                    "description": description,
                })

            detail = {"instance_name": instance_name, "plugin_type": plugin_type, "params": {}}
            self.add_plugin(instance_name, f"🔧 {display_name}", description, detail)


class CustomPluginDialog(QDialog):
    """自定义插件注册对话框（对应 PRD 3.5.1）。"""

    CATEGORY_MAP = {
        "planner": "规划器",
        "controller": "控制器",
        "smoother": "平滑器",
        "costmap_layer": "代价地图层",
        "recovery": "Recovery",
    }
    REVERSE_CATEGORY_MAP = {v: k for k, v in CATEGORY_MAP.items()}

    def __init__(self, parent=None, category=""):
        super().__init__(parent)
        self.setWindowTitle("添加自定义插件")
        layout = QFormLayout(self)

        self.display_name_edit = QLineEdit()
        self.plugin_type_edit = QLineEdit()
        self.plugin_type_edit.setPlaceholderText("如 my_pkg/MyPlanner")
        self.instance_name_edit = QLineEdit()
        self.instance_name_edit.setPlaceholderText("留空则自动生成")
        self.category_combo = QComboBox()
        self.category_combo.addItems(list(self.CATEGORY_MAP.values()))
        self.description_edit = QLineEdit()

        if category and category in self.CATEGORY_MAP:
            display_text = self.CATEGORY_MAP[category]
            idx = self.category_combo.findText(display_text)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            self.category_combo.setEnabled(False)

        layout.addRow("显示名称：", self.display_name_edit)
        layout.addRow("插件类型名：", self.plugin_type_edit)
        layout.addRow("实例名：", self.instance_name_edit)
        layout.addRow("分类：", self.category_combo)
        layout.addRow("备注：", self.description_edit)

        btn_layout = QVBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_category(self) -> str:
        """返回选中分类的英文键名。"""
        text = self.category_combo.currentText()
        return self.REVERSE_CATEGORY_MAP.get(text, "planner")
