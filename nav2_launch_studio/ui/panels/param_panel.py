"""参数配置面板组件 - Nav2 节点的可编辑参数配置。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QScrollArea,
    QSlider, QDoubleSpinBox, QSpinBox, QCheckBox,
    QComboBox, QLineEdit, QPushButton, QLabel,
    QToolButton, QGroupBox, QStackedWidget, QHBoxLayout,
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
        self.scroll.setWidget(self.param_container)
        layout.addWidget(self.scroll)

    def load_params(self, node_name, params_schema, current_values=None):
        """为节点加载参数控件。

        参数：
            node_name: Nav2 节点名称
            params_schema: 从 schema 文件读取的参数定义字典
            current_values: 当前参数值字典（来自项目）
        """
        # TODO: 清除已有控件，根据 schema 创建控件，填充值
        self._current_node = node_name
        self.node_label.setText(node_name)

    def get_params(self):
        """返回当前参数值字典。"""
        # TODO: 从所有控件读取值
        return {}

    def _toggle_mode(self, checked):
        """在基础和专家显示模式之间切换。"""
        self._mode = "expert" if checked else "basic"
        self.mode_btn.setText("基础模式" if checked else "专家模式")
        self.mode_changed.emit(self._mode)
        # TODO: 根据 level 显示/隐藏参数

    def _create_param_widget(self, param_def):
        """根据参数 schema 创建对应的控件。

        参数：
            param_def: 包含 type、default、min、max 等字段的字典
        返回：
            参数对应的 QWidget
        """
        ptype = param_def.get("type", "string")
        if ptype == "float":
            return self._create_float_widget(param_def)
        elif ptype == "int":
            return self._create_int_widget(param_def)
        elif ptype == "bool":
            return self._create_bool_widget(param_def)
        elif ptype == "enum":
            return self._create_enum_widget(param_def)
        elif ptype == "string":
            return self._create_string_widget(param_def)
        elif ptype == "list":
            return self._create_list_widget(param_def)
        return QLineEdit()

    def _create_float_widget(self, param_def):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        slider = QSlider(Qt.Horizontal)
        spinbox = QDoubleSpinBox()
        # TODO: 配置范围、默认值、单位
        layout.addWidget(slider, stretch=2)
        layout.addWidget(spinbox, stretch=1)
        return widget

    def _create_int_widget(self, param_def):
        return QSpinBox()

    def _create_bool_widget(self, param_def):
        return QCheckBox()

    def _create_enum_widget(self, param_def):
        combo = QComboBox()
        combo.addItems(param_def.get("enum_values", []))
        return combo

    def _create_string_widget(self, param_def):
        return QLineEdit()

    def _create_list_widget(self, param_def):
        # TODO: 可折叠的列表编辑器
        return QLineEdit("[list]")
