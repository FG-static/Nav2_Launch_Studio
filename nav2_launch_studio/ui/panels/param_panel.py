"""参数配置面板组件 - Nav2 节点的可编辑参数配置。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QScrollArea,
    QDoubleSpinBox, QSpinBox, QCheckBox,
    QLineEdit, QPushButton, QLabel,
    QHBoxLayout, QTextEdit,
)
from PySide6.QtCore import Qt, Signal


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

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_node = None
        self._current_params: dict = {}  # 当前节点的参数快照
        self._mode = "basic"
        self._param_widgets: dict[str, QWidget] = {}
        self._param_types: dict[str, str] = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 标题栏
        header_layout = QHBoxLayout()
        self.node_label = QLabel("未选择节点")
        self.node_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.node_label)
        header_layout.addStretch()
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

    def load_params(self, node_name: str, params: dict = None):
        """为节点加载参数控件。"""
        self._clear_params()

        self._current_node = node_name
        self._current_params = dict(params) if params else {}
        self.node_label.setText(node_name)
        self._param_widgets.clear()
        self._param_types.clear()

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

    def _apply_mode(self):
        """根据当前模式切换表单/YAML 编辑器的可见性。"""
        is_basic = self._mode == "basic"
        self.scroll.setVisible(is_basic)
        self.yaml_editor.setVisible(not is_basic)
        self.yaml_apply_btn.setVisible(not is_basic)

        if not is_basic:
            self._update_yaml_editor()
            self._hint_label.setText("专家模式：直接编辑 YAML 文本，点击「应用 YAML 更改」同步到项目")
        else:
            # 切回基础模式：从当前快照刷新表单
            if self._current_node:
                self.load_params(self._current_node, self._current_params)
            self._hint_label.setText("")

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

    def _rebuild_form(self, params: dict):
        """从参数字典重建表单控件。"""
        self._clear_params()
        self._param_widgets.clear()
        self._param_types.clear()

        for key, value in sorted(params.items()):
            dtype = self._detect_type(value)
            widget = self._create_widget_for_type(dtype, value)
            self._param_widgets[key] = widget
            self._param_types[key] = dtype
            self.param_layout.addRow(key, widget)

    def _set_widget_value(self, widget: QWidget, dtype: str, value):
        """设置控件的值。"""
        if isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QSpinBox):
            widget.setValue(int(value) if value is not None else 0)
        elif isinstance(widget, QDoubleSpinBox):
            widget.setValue(float(value) if value is not None else 0.0)
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

    def _read_widget_value(self, widget: QWidget, dtype: str):
        """从控件读取值并转换为对应类型。"""
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QSpinBox):
            return widget.value()
        elif isinstance(widget, QDoubleSpinBox):
            return widget.value()
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
