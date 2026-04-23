"""节点拓扑图组件 - Nav2 节点拓扑可视化展示。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsItem,
)
from PySide6.QtCore import Qt, Signal


class NodeGraphWidget(QWidget):
    """Nav2 节点交互式拓扑图。

    对应 PRD 3.3：
    - 有向图展示 Nav2 节点树
    - 节点显示：名称、图标、启用复选框、类型标签
    - 颜色编码：蓝色=必选，绿色=推荐，灰色=可选
    - 点击节点 -> 打开参数面板
    - 切换启用/禁用时检查依赖关系
    """

    # 信号
    node_clicked = Signal(str)  # 节点名称
    node_toggled = Signal(str, bool)  # 节点名称, 是否启用

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = NodeGraphScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(Qt.Antialiasing)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        layout.addWidget(self.view)

    def load_nodes(self, node_config):
        """从节点配置加载拓扑图。

        参数：
            node_config: 节点名称到配置的映射字典
                         (enabled, type, dependencies)
        """
        # TODO: 创建 NodeItem 实例，布局，绘制连线
        pass

    def set_node_enabled(self, node_name, enabled):
        """切换节点的启用状态，并进行依赖检查。"""
        # TODO: 检查依赖关系，必要时弹出警告，更新视觉
        pass


class NodeGraphScene(QGraphicsScene):
    """节点拓扑图的图形场景。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 600, 400)


class NodeItem(QGraphicsItem):
    """拓扑图中的单个节点。

    显示：名称、图标、复选框、类型标签。
    颜色：蓝色=必选，绿色=推荐，灰色=可选。
    """

    # 节点类型分类
    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"

    def __init__(self, name, node_type=OPTIONAL, enabled=True):
        super().__init__()
        self.name = name
        self.node_type = node_type
        self.enabled = enabled

    def paint(self, painter, option, widget):
        # TODO: 绘制节点视觉元素
        pass

    def boundingRect(self):
        # TODO: 返回边界矩形
        from PySide6.QtCore import QRectF
        return QRectF(0, 0, 120, 60)
