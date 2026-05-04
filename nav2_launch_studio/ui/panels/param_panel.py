"""参数配置面板组件 - Nav2 节点的可编辑参数配置。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QScrollArea,
    QSlider, QDoubleSpinBox, QSpinBox, QCheckBox,
    QComboBox, QLineEdit, QPushButton, QLabel,
    QGroupBox, QHBoxLayout, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal


class ParamPanelWidget(QWidget):
    """Nav2 节点的参数配置面板。

    对应 PRD 3.4：
    - 点击节点拓扑图中的节点触发
    - 参数 UI 控件根据类型生成（滑块、开关、下拉等）
    - 两种显示模式：基础（5-10个关键参数）/ 专家（全部参数）
    - 帮助气泡显示文档摘要
    - 超出范围显示黄色警告，非法值显示红色错误
    """

    # 信号
    param_changed = Signal(str, str, object)  # 节点名, 参数键, 值
    mode_changed = Signal(str)  # "basic" 或 "expert"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_node = None
        self._mode = "basic"
        self._param_widgets: dict[str, QWidget] = {}
        self._param_types: dict[str, str] = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 标题
        self.node_label = QLabel("未选择节点")
        self.node_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.node_label)

        # 模式切换
        self.mode_btn = QPushButton("专家模式")
        self.mode_btn.setCheckable(True)
        self.mode_btn.toggled.connect(self._toggle_mode)
        layout.addWidget(self.mode_btn)

        # 可滚动参数区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.param_container = QWidget()
        self.param_layout = QFormLayout(self.param_container)
        self.param_layout.setLabelAlignment(Qt.AlignRight)
        self.scroll.setWidget(self.param_container)
        layout.addWidget(self.scroll)

        # 底部提示
        self._hint_label = QLabel("")
        self._hint_label.setStyleSheet("color: #888; font-size: 11px;")
        self._hint_label.setWordWrap(True)
        layout.addWidget(self._hint_label)

    def load_params(self, node_name: str, params: dict = None):
        """为节点加载参数控件。

        参数：
            node_name: Nav2 节点名称
            params: 当前参数值字典 {key: value, ...}
        """
        # 清除已有控件
        self._clear_params()

        self._current_node = node_name
        self.node_label.setText(node_name)
        self._param_widgets.clear()
        self._param_types.clear()

        if not params:
            self._hint_label.setText("该节点暂无自定义参数。\n"
                                     "可通过 YAML 导入或键值编辑器添加参数。")
            return

        self._hint_label.setText("")

        for key, value in sorted(params.items()):
            dtype = self._detect_type(value)
            widget = self._create_widget_for_type(dtype, value)
            self._param_widgets[key] = widget
            self._param_types[key] = dtype
            self.param_layout.addRow(key, widget)

    def get_params(self) -> dict:
        """返回当前参数值字典。"""
        result = {}
        for key, widget in self._param_widgets.items():
            result[key] = self._read_widget_value(widget, self._param_types.get(key, "string"))
        return result

    def _clear_params(self):
        """清除参数布局中的所有控件。"""
        while self.param_layout.rowCount() > 0:
            self.param_layout.removeRow(0)
        self._param_widgets.clear()
        self._param_types.clear()

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
        self.mode_changed.emit(self._mode)
