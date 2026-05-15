"""参数配置面板组件 - Nav2 节点的可编辑参数配置。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QScrollArea,
    QDoubleSpinBox, QSpinBox, QCheckBox,
    QLineEdit, QPushButton, QLabel,
    QHBoxLayout, QTextEdit, QToolButton, QFrame,
)
from PySide6.QtCore import Qt, Signal
from nav2_launch_studio.core.change_tracker import ChangeType, get_highlight_color as _get_highlight_color


class ParamPanelWidget(QWidget):
    """Nav2 节点的参数配置面板。

    对应 PRD 3.4：
    - 点击节点拓扑图中的节点触发
    - 参数 UI 控件根据类型生成
    - 两种显示模式：
      - 基础模式：全部参数用表单控件编辑
      - 专家模式：直接编辑原始 YAML 文本
    """

    # 信号
    param_changed = Signal(str, str, object)  # 节点名, 参数键, 值
    params_replaced = Signal(str, dict)       # 节点名, 完整新参数字典（专家模式批量替换）
    mode_changed = Signal(str)  # "basic" 或 "expert"
    save_template_requested = Signal()         # 请求保存为模版
    load_template_requested = Signal()         # 请求从模版加载

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_node = None
        self._current_params: dict = {}  # 当前节点的参数快照
        self._mode = "basic"
        self._param_widgets: dict[str, QWidget] = {}
        self._param_types: dict[str, str] = {}
        self._highlight_wrappers: dict[str, QWidget] = {}  # 高亮包装控件
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 标题栏
        header_layout = QHBoxLayout()
        self.node_label = QLabel("未选择节点")
        self.node_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.node_label)
        header_layout.addStretch()
        self.save_template_btn = QPushButton("保存为模版")
        self.save_template_btn.clicked.connect(self.save_template_requested.emit)
        header_layout.addWidget(self.save_template_btn)
        self.load_template_btn = QPushButton("从模版加载")
        self.load_template_btn.clicked.connect(self.load_template_requested.emit)
        header_layout.addWidget(self.load_template_btn)
        self.mode_btn = QPushButton("专家模式")
        self.mode_btn.setCheckable(True)
        self.mode_btn.toggled.connect(self._toggle_mode)
        header_layout.addWidget(self.mode_btn)
        layout.addLayout(header_layout)

        # 基础模式：可滚动参数表单
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.param_container = QWidget()
        self.param_layout = QFormLayout(self.param_container)
        self.param_layout.setLabelAlignment(Qt.AlignRight)
        self.scroll.setWidget(self.param_container)
        layout.addWidget(self.scroll)

        # 专家模式：YAML 文本编辑器（默认隐藏）
        self.yaml_editor = QTextEdit()
        self.yaml_editor.setPlaceholderText("在此直接编辑 YAML 参数...")
        self.yaml_editor.setFontFamily("monospace")
        self.yaml_editor.setVisible(False)
        layout.addWidget(self.yaml_editor)

        # 专家模式应用按钮（默认隐藏）
        self.yaml_apply_btn = QPushButton("应用 YAML 更改")
        self.yaml_apply_btn.clicked.connect(self._apply_yaml_changes)
        self.yaml_apply_btn.setVisible(False)
        layout.addWidget(self.yaml_apply_btn)

        # 底部提示
        self._hint_label = QLabel("")
        self._hint_label.setStyleSheet("color: #888; font-size: 11px;")
        self._hint_label.setWordWrap(True)
        layout.addWidget(self._hint_label)

    def load_params(self, node_name: str, params: dict = None, changes: dict = None):
        """为节点加载参数控件。

        参数：
            node_name: 节点名称
            params: 参数字典

            changes: 变更字典 {param_key: ChangeType}
        """
        self._clear_params()

        self._current_node = node_name
        self._current_params = dict(params) if params else {}
        self.node_label.setText(node_name)
        self._param_widgets.clear()
        self._param_types.clear()
        self._highlight_wrappers.clear()

        if not params:
            self._hint_label.setText("该节点暂无自定义参数。\n"
                                     "可通过 YAML 导入或键值编辑器添加参数。")
            self.yaml_editor.setPlainText("")
            return

        self._hint_label.setText("")

        for key, value in sorted(params.items()):
            dtype = self._detect_type(value)
            widget = self._create_widget_for_type(dtype, value)
            self._param_widgets[key] = widget
            self._param_types[key] = dtype

            # 检查是否有变更，创建带高亮的行
            change_type = changes.get(key, ChangeType.NONE) if changes else ChangeType.NONE
            if change_type != ChangeType.NONE:
                wrapper = self._create_highlight_wrapper(widget, change_type)
                self._highlight_wrappers[key] = wrapper
                self.param_layout.addRow(key, wrapper)
            else:
                self.param_layout.addRow(key, widget)

        self._update_yaml_editor()

    def get_params(self) -> dict:
        """返回当前参数值字典。"""
        result = {}
        for key, widget in self._param_widgets.items():
            result[key] = self._read_widget_value(widget, self._param_types.get(key, "string"))
        return result

    def set_mode(self, mode: str):
        """外部设置显示模式。"""
        self._mode = mode
        self.mode_btn.setChecked(mode == "expert")
        self.mode_btn.setText("基础模式" if mode == "expert" else "专家模式")
        self._apply_mode()
        self.mode_changed.emit(mode)

    def _clear_params(self):
        """清除参数布局中的所有控件。"""
        while self.param_layout.rowCount() > 0:
            self.param_layout.removeRow(0)
        self._param_widgets.clear()
        self._param_types.clear()
        self._highlight_wrappers.clear()

    def _apply_mode(self):
        """根据当前模式切换表单/YAML 编辑器的可见性。"""
        is_basic = self._mode == "basic"
        self.scroll.setVisible(is_basic)
        self.yaml_editor.setVisible(not is_basic)
        self.yaml_apply_btn.setVisible(not is_basic)

        if not is_basic:
            # 切到专家模式：先同步表单控件值到快照，再更新 YAML 编辑器
            self._sync_params_from_form()
            self._update_yaml_editor()
            self._hint_label.setText("专家模式：直接编辑 YAML 文本，点击「应用 YAML 更改」同步到项目")
        else:
            # 切回基础模式：先尝试从 YAML 编辑器同步未保存的修改
            self._sync_params_from_yaml_editor()
            if self._current_node:
                self.load_params(self._current_node, self._current_params)
            self._hint_label.setText("")

    def _sync_params_from_yaml_editor(self):
        """将 YAML 编辑器内容解析并同步到快照（不触发 model 更新）。"""
        if not self._current_node or not self.yaml_editor.isVisible():
            return
        text = self.yaml_editor.toPlainText().strip()
        if not text or text == "# 无参数":
            self._current_params = {}
            return
        import yaml
        try:
            new_params = yaml.safe_load(text)
            if isinstance(new_params, dict):
                self._current_params = new_params
        except yaml.YAMLError:
            pass  # YAML 有误，保留原快照

    def _sync_params_from_form(self):
        """将当前表单控件的值同步到 _current_params 快照。"""
        if not self._current_node:
            return
        self._current_params = self.get_params()

    def _update_yaml_editor(self):
        """将当前参数同步到 YAML 编辑器。"""
        params = self.get_params()
        if params:
            import yaml
            text = yaml.dump(params, default_flow_style=False, allow_unicode=True)
            self.yaml_editor.setPlainText(text)
        else:
            self.yaml_editor.setPlainText("# 无参数")

    def _apply_yaml_changes(self):
        """将 YAML 编辑器内容完整替换节点参数。"""
        text = self.yaml_editor.toPlainText().strip()
        if not text or text == "# 无参数":
            new_params = {}
        else:
            import yaml
            try:
                new_params = yaml.safe_load(text)
            except yaml.YAMLError as e:
                self._hint_label.setText(f"YAML 解析错误: {e}")
                return

            if not isinstance(new_params, dict):
                self._hint_label.setText("YAML 内容必须是字典格式")
                return

        if not self._current_node:
            return

        # 完整替换：发射信号让 model 更新整个节点参数
        self.params_replaced.emit(self._current_node, new_params)

        # 更新本地快照和表单控件
        self._current_params = dict(new_params)
        self._rebuild_form(new_params)

        self._hint_label.setText(f"YAML 更改已应用（{len(new_params)} 个参数）")

    def _rebuild_form(self, params: dict, changes: dict = None):
        """从参数字典重建表单控件。"""
        self._clear_params()
        self._param_widgets.clear()
        self._param_types.clear()
        self._highlight_wrappers.clear()

        for key, value in sorted(params.items()):
            dtype = self._detect_type(value)
            widget = self._create_widget_for_type(dtype, value)
            self._param_widgets[key] = widget
            self._param_types[key] = dtype

            change_type = changes.get(key, ChangeType.NONE) if changes else ChangeType.NONE
            if change_type != ChangeType.NONE:
                wrapper = self._create_highlight_wrapper(widget, change_type)
                self._highlight_wrappers[key] = wrapper
                self.param_layout.addRow(key, wrapper)
            else:
                self.param_layout.addRow(key, widget)

    def _set_widget_value(self, widget: QWidget, dtype: str, value):
        """设置控件的值。"""
        if isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QSpinBox):
            widget.setValue(int(value) if value is not None else 0)
        elif isinstance(widget, QDoubleSpinBox):
            widget.setValue(float(value) if value is not None else 0.0)
        elif isinstance(widget, CollapsibleDictWidget):
            widget.set_value(value if isinstance(value, dict) else {})
        elif isinstance(widget, QLineEdit):
            if dtype == "list":
                import yaml
                widget.setText(yaml.dump(value, default_flow_style=True).strip())
            else:
                widget.setText(str(value) if value is not None else "")

    def _detect_type(self, value) -> str:
        """根据 Python 值自动检测参数类型。"""
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, dict):
            return "dict"
        if isinstance(value, list):
            return "list"
        return "string"

    def _create_widget_for_type(self, dtype: str, value) -> QWidget:
        """根据类型创建对应控件。"""
        if dtype == "bool":
            return self._create_bool_widget(value)
        elif dtype == "int":
            return self._create_int_widget(value)
        elif dtype == "float":
            return self._create_float_widget(value)
        elif dtype == "dict":
            return self._create_dict_widget(value)
        elif dtype == "list":
            return self._create_list_widget(value)
        else:
            return self._create_string_widget(value)

    def _create_bool_widget(self, value: bool) -> QCheckBox:
        widget = QCheckBox()
        widget.setChecked(bool(value))
        widget.stateChanged.connect(lambda _: self._on_value_changed())
        return widget

    def _create_int_widget(self, value: int) -> QSpinBox:
        widget = QSpinBox()
        widget.setRange(-999999, 999999)
        widget.setValue(int(value) if value is not None else 0)
        widget.valueChanged.connect(lambda _: self._on_value_changed())
        return widget

    def _create_float_widget(self, value: float) -> QDoubleSpinBox:
        widget = QDoubleSpinBox()
        widget.setRange(-999999.0, 999999.0)
        widget.setDecimals(4)
        widget.setSingleStep(0.1)
        widget.setValue(float(value) if value is not None else 0.0)
        widget.valueChanged.connect(lambda _: self._on_value_changed())
        return widget

    def _create_string_widget(self, value) -> QLineEdit:
        widget = QLineEdit(str(value) if value is not None else "")
        widget.editingFinished.connect(self._on_value_changed)
        return widget

    def _create_list_widget(self, value: list) -> QLineEdit:
        """列表参数暂用 QLineEdit 显示 YAML 格式。"""
        import yaml
        text = yaml.dump(value, default_flow_style=True).strip() if value else "[]"
        widget = QLineEdit(text)
        widget.editingFinished.connect(self._on_value_changed)
        return widget

    def _create_dict_widget(self, value: dict) -> 'CollapsibleDictWidget':
        """创建可展开/折叠的嵌套字典参数控件。"""
        widget = CollapsibleDictWidget(value, parent_panel=self)
        widget.value_changed.connect(self._on_value_changed)
        return widget

    def _read_widget_value(self, widget: QWidget, dtype: str):
        """从控件读取值并转换为对应类型。"""
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QSpinBox):
            return widget.value()
        elif isinstance(widget, QDoubleSpinBox):
            return widget.value()
        elif isinstance(widget, CollapsibleDictWidget):
            return widget.get_value()
        elif isinstance(widget, QLineEdit):
            text = widget.text()
            if dtype == "list":
                import yaml
                try:
                    return yaml.safe_load(text) or []
                except Exception:
                    return text
            return text
        return None

    def _on_value_changed(self):
        """参数值变化时发射信号。"""
        if self._current_node:
            params = self.get_params()
            for key, value in params.items():
                self.param_changed.emit(self._current_node, key, value)

    def _toggle_mode(self, checked):
        """在基础和专家显示模式之间切换。"""
        self._mode = "expert" if checked else "basic"
        self.mode_btn.setText("基础模式" if checked else "专家模式")
        self._apply_mode()
        self.mode_changed.emit(self._mode)

    def set_param_highlights(self, node_name: str, changed_params: dict):
        """为指定节点的参数设置变更高亮。

        参数：
            node_name: 节点名称（需与当前显示的节点一致）
            changed_params: {param_key: ChangeType} 变更字典
        """
        if node_name != self._current_node:
            return

        # 先清除现有高亮
        self._clear_highlights()

        # 为每个变更的参数添加高亮
        for param_key, change_type in changed_params.items():
            widget = self._param_widgets.get(param_key)
            if not widget:
                continue

            # 创建高亮包装
            wrapper = self._create_highlight_wrapper(widget, change_type)
            self._highlight_wrappers[param_key] = wrapper

            # 替换表单布局中的行
            self._replace_form_row(param_key, wrapper)

    def _create_highlight_wrapper(self, widget: QWidget, change_type: ChangeType) -> QWidget:
        """创建带高亮背景的包装控件。"""
        color_tuple = _get_highlight_color(change_type)
        wrapper = QWidget()
        wrapper.setProperty("change_type", change_type.value)
        if color_tuple:
            r, g, b = color_tuple
            wrapper.setStyleSheet(
                f"background-color: rgb({r}, {g}, {b}); "
                f"border-radius: 3px; padding: 2px;"
            )
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.addWidget(widget)
        return wrapper

    def _replace_form_row(self, param_key: str, new_widget: QWidget):
        """替换表单布局中指定参数键的行。"""
        for i in range(self.param_layout.rowCount()):
            label_item = self.param_layout.itemAt(i, QFormLayout.LabelRole)
            if label_item and label_item.widget():
                label_text = label_item.widget().text()
                if label_text == param_key:
                    # 移除旧行并插入新行
                    field_item = self.param_layout.itemAt(i, QFormLayout.FieldRole)
                    old_widget = field_item.widget() if field_item else None
                    self.param_layout.removeRow(i)
                    self.param_layout.insertRow(i, param_key, new_widget)
                    # 如果旧控件是包装器，需要把原始控件取出来
                    # 但这里 new_widget 已经包含原始控件，所以直接替换即可
                    return

    def _clear_highlights(self):
        """清除所有参数行的高亮。"""
        for key, wrapper in self._highlight_wrappers.items():
            # 从包装器中取出原始控件
            layout = wrapper.layout()
            if layout and layout.count() > 0:
                original_widget = layout.itemAt(0).widget()
                if original_widget:
                    self._replace_form_row(key, original_widget)
        self._highlight_wrappers.clear()


class CollapsibleDictWidget(QWidget):
    """可展开/折叠的嵌套字典参数控件。

    点击标题栏切换展开/折叠状态，展开时显示子参数表单。
    支持递归嵌套：子值为 dict 时自动创建子 CollapsibleDictWidget。
    """

    value_changed = Signal()

    def __init__(self, data: dict = None, parent_panel=None, parent=None):
        super().__init__(parent)
        self._parent_panel = parent_panel
        self._child_widgets: dict[str, QWidget] = {}
        self._child_types: dict[str, str] = {}
        self._expanded = True
        self._init_ui()
        if data:
            self._populate_children(data)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(2)

        # 折叠/展开按钮
        self._toggle_btn = QToolButton()
        self._toggle_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._toggle_btn.setArrowType(Qt.DownArrow)
        self._toggle_btn.clicked.connect(self._toggle)
        self._toggle_btn.setStyleSheet(
            "QToolButton { border: none; padding: 2px; font-weight: bold; }"
        )
        layout.addWidget(self._toggle_btn)

        # 子参数容器（带左边缩进线）
        self._content_frame = QFrame()
        self._content_frame.setFrameShape(QFrame.StyledPanel)
        self._content_frame.setStyleSheet(
            "QFrame { border-left: 2px solid #bbb; margin-left: 8px; padding-left: 4px; }"
        )
        content_layout = QVBoxLayout(self._content_frame)
        content_layout.setContentsMargins(4, 2, 2, 2)

        self._form_layout = QFormLayout()
        self._form_layout.setLabelAlignment(Qt.AlignRight)
        content_layout.addLayout(self._form_layout)

        layout.addWidget(self._content_frame)

    def set_title(self, title: str):
        """设置分组标题。"""
        self._toggle_btn.setText(title)

    def _toggle(self):
        """切换展开/折叠状态。"""
        self._expanded = not self._expanded
        self._content_frame.setVisible(self._expanded)
        self._toggle_btn.setArrowType(
            Qt.DownArrow if self._expanded else Qt.RightArrow
        )

    def _populate_children(self, data: dict):
        """根据字典数据创建子参数控件。"""
        self._clear_children()
        for key, value in sorted(data.items()):
            dtype = self._detect_type(value)
            if dtype == "dict":
                widget = CollapsibleDictWidget(value, self._parent_panel, self)
                widget.set_title(key)
                widget.value_changed.connect(self.value_changed)
                self._form_layout.addRow(widget)
            else:
                widget = self._create_widget(dtype, value)
                self._form_layout.addRow(key, widget)
            self._child_widgets[key] = widget
            self._child_types[key] = dtype

    def _clear_children(self):
        """清除所有子控件。"""
        while self._form_layout.rowCount() > 0:
            self._form_layout.removeRow(0)
        self._child_widgets.clear()
        self._child_types.clear()

    def _detect_type(self, value) -> str:
        """检测参数类型。"""
        if self._parent_panel:
            return self._parent_panel._detect_type(value)
        # 回退：无父面板时的独立检测
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, dict):
            return "dict"
        if isinstance(value, list):
            return "list"
        return "string"

    def _create_widget(self, dtype: str, value) -> QWidget:
        """创建子参数控件。"""
        if self._parent_panel:
            return self._parent_panel._create_widget_for_type(dtype, value)
        # 回退：无父面板时创建基本控件
        widget = QLineEdit(str(value) if value is not None else "")
        widget.editingFinished.connect(self.value_changed)
        return widget

    def get_value(self) -> dict:
        """读取所有子参数值，返回嵌套字典。"""
        result = {}
        for key, widget in self._child_widgets.items():
            dtype = self._child_types.get(key, "string")
            if isinstance(widget, CollapsibleDictWidget):
                result[key] = widget.get_value()
            elif self._parent_panel:
                result[key] = self._parent_panel._read_widget_value(widget, dtype)
            else:
                result[key] = self._read_fallback(widget)
        return result

    def set_value(self, data: dict):
        """从字典设置子参数值。"""
        if not isinstance(data, dict):
            return
        for key, widget in self._child_widgets.items():
            if key in data:
                dtype = self._child_types.get(key, "string")
                value = data[key]
                if isinstance(widget, CollapsibleDictWidget):
                    widget.set_value(value if isinstance(value, dict) else {})
                elif self._parent_panel:
                    self._parent_panel._set_widget_value(widget, dtype, value)

    def _read_fallback(self, widget: QWidget):
        """无父面板时的值读取回退。"""
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QSpinBox):
            return widget.value()
        if isinstance(widget, QDoubleSpinBox):
            return widget.value()
        if isinstance(widget, QLineEdit):
            return widget.text()
        return None
