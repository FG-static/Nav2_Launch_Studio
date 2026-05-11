"""节点拓扑图组件 - Nav2 节点拓扑可视化展示。"""

import math
from collections import deque

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGraphicsView, QGraphicsScene,
    QGraphicsObject, QGraphicsItem, QGraphicsLineItem, QMessageBox,
    QInputDialog, QLineEdit,
)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPolygonF

from nav2_launch_studio.core.node_dependencies import (
    NODE_DEPENDENCIES, NODE_TYPES, MANDATORY_NODES, check_disable_allowed,
)


# ---- 颜色常量 ----

COLOR_MANDATORY = QColor(66, 133, 244)     # 蓝色
COLOR_RECOMMENDED = QColor(52, 168, 83)    # 绿色
COLOR_OPTIONAL = QColor(158, 158, 158)     # 灰色
COLOR_DISABLED = QColor(200, 200, 200)     # 禁用灰色
COLOR_DISABLED_TEXT = QColor(140, 140, 140)
COLOR_EDGE = QColor(120, 120, 120)
COLOR_EDGE_DISABLED = QColor(200, 200, 200)
COLOR_CHECKBOX_BORDER = QColor(80, 80, 80)
COLOR_CHECKBOX_CHECK = QColor(33, 150, 243)

NODE_WIDTH = 150
NODE_HEIGHT = 56
LAYER_V_SPACING = 100
LAYER_H_SPACING = 30


def _type_color(node_type: str) -> QColor:
    if node_type == "mandatory":
        return COLOR_MANDATORY
    if node_type == "recommended":
        return COLOR_RECOMMENDED
    return COLOR_OPTIONAL


def _type_label(node_type: str) -> str:
    if node_type == "mandatory":
        return "必选"
    if node_type == "recommended":
        return "推荐"
    return "可选"


class PannableGraphicsView(QGraphicsView):
    """支持鼠标中键拖拽平移和滚轮缩放的 QGraphicsView。"""

    def __init__(self, scene=None, parent=None):
        super().__init__(scene, parent)
        self._panning = False
        self._pan_start = QPointF()

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = False
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)


class NodeGraphWidget(QWidget):
    """Nav2 节点交互式拓扑图。

    对应 PRD 3.3：
    - 有向图展示 Nav2 节点树
    - 节点显示：名称、启用复选框、类型标签
    - 颜色编码：蓝色=必选，绿色=推荐，灰色=可选
    - 点击节点 -> 打开参数面板
    - 切换启用/禁用时检查依赖关系
    """

    # 信号
    node_clicked = Signal(str)       # 节点名称
    node_toggled = Signal(str, bool)  # 节点名称, 是否启用
    custom_node_added = Signal(str)  # 新节点名称

    def __init__(self, parent=None):
        super().__init__(parent)
        self._node_items: dict[str, NodeItem] = {}
        self._edges: list[EdgeItem] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = NodeGraphScene()
        self.view = PannableGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing) # 抗锯齿渲染
        self.view.setDragMode(QGraphicsView.RubberBandDrag) # 拖拽选择
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate) # 全量更新
        layout.addWidget(self.view)

        # 添加自定义节点按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.add_node_btn = QPushButton("✚ 添加自定义节点")
        self.add_node_btn.clicked.connect(self._on_add_custom_node)
        btn_layout.addWidget(self.add_node_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def load_nodes(self, node_config: dict):
        """从节点配置加载拓扑图。

        参数：
            node_config: {node_name: {enabled: bool, node_type: str}, ...}
        """
        self.scene.clear()
        self._node_items.clear()
        self._edges.clear()

        if not node_config:
            return

        # 创建节点
        for name, cfg in node_config.items():
            node_type = cfg.get("node_type", "optional")
            enabled = cfg.get("enabled", True)
            item = NodeItem(name, node_type, enabled)
            item.node_clicked.connect(self._on_node_clicked)
            item.node_toggled.connect(self._on_node_toggled)
            self._node_items[name] = item
            self.scene.addItem(item)

        # 层次布局
        self._layout_nodes()

        # 创建连线
        self._create_edges()

        # 调整场景尺寸
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20))

    def _layout_nodes(self):
        """拓扑排序分层布局。"""
        # 拓扑排序分层
        layers = self._topological_layers()
        if not layers:
            return

        total_width = max(len(layer) for layer in layers) * (NODE_WIDTH + LAYER_H_SPACING) - LAYER_H_SPACING
        start_x = 0

        for row, layer in enumerate(layers):
            row_width = len(layer) * NODE_WIDTH + (len(layer) - 1) * LAYER_H_SPACING
            x_offset = start_x + (total_width - row_width) / 2
            y = row * (NODE_HEIGHT + LAYER_V_SPACING)

            for col, name in enumerate(layer):
                item = self._node_items.get(name)
                if item:
                    item.setPos(x_offset + col * (NODE_WIDTH + LAYER_H_SPACING), y)

    def _topological_layers(self) -> list[list[str]]:
        """拓扑排序，返回分层列表。"""
        nodes = set(self._node_items.keys())
        # 计算入度（只计算本图内节点的依赖）
        in_degree: dict[str, int] = {n: 0 for n in nodes}
        for n in nodes:
            for dep in NODE_DEPENDENCIES.get(n, []):
                if dep in nodes:
                    in_degree[n] += 1

        # BFS 分层
        layers: list[list[str]] = []
        queue = deque(sorted(n for n, d in in_degree.items() if d == 0))
        visited = set()

        while queue:
            layer = []
            for _ in range(len(queue)):
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                layer.append(node)
            if layer:
                layers.append(sorted(layer))

            # 更新入度
            for node in layer:
                for dependent in nodes:
                    if node in NODE_DEPENDENCIES.get(dependent, []):
                        in_degree[dependent] -= 1
                        if in_degree[dependent] == 0 and dependent not in visited:
                            queue.append(dependent)

        # 处理未访问的节点（不应发生，但防御性处理）
        remaining = nodes - visited
        if remaining:
            layers.append(sorted(remaining))

        return layers

    def _create_edges(self):
        """创建依赖连线。"""
        for child_name, deps in NODE_DEPENDENCIES.items():
            child_item = self._node_items.get(child_name)
            if not child_item:
                continue
            for parent_name in deps:
                parent_item = self._node_items.get(parent_name)
                if not parent_item:
                    continue
                edge = EdgeItem(parent_item, child_item)
                self._edges.append(edge)
                self.scene.addItem(edge)

    def set_node_enabled(self, node_name: str, enabled: bool) -> bool:
        """切换节点的启用状态，并进行依赖检查。

        返回 True 表示状态已变更，False 表示被拒绝。
        """
        item = self._node_items.get(node_name)
        if not item:
            return False

        # mandatory 节点不允许禁用
        if not enabled and node_name in MANDATORY_NODES:
            return False

        # 禁用时检查依赖
        if not enabled:
            allowed, reason, dependents = check_disable_allowed(node_name)
            if not allowed:
                return False
            if dependents:
                reply = QMessageBox.warning(
                    self, "依赖警告",
                    f"以下节点依赖 {node_name}：\n{', '.join(dependents)}\n\n"
                    f"禁用后这些节点可能无法正常工作，确定要禁用吗？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return False

        item.enabled = enabled
        item.update()

        # 更新连线视觉
        self._update_edge_visuals()

        self.node_toggled.emit(node_name, enabled)
        return True

    def get_node_config(self) -> dict:
        """返回当前所有节点的配置字典。"""
        config = {}
        for name, item in self._node_items.items():
            config[name] = {
                "enabled": item.enabled,
                "node_type": item.node_type,
            }
        return config

    def _update_edge_visuals(self):
        """根据节点启用状态更新连线视觉。"""
        for edge in self._edges:
            edge.update_visual()

    def _on_add_custom_node(self):
        """弹出对话框添加自定义节点。"""
        name, ok = QInputDialog.getText(
            self, "添加自定义节点", "节点名称：",
            QLineEdit.Normal, "",
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self._node_items:
            QMessageBox.warning(self, "节点已存在", f"节点「{name}」已存在。")
            return
        self.custom_node_added.emit(name)

    def _on_node_clicked(self, name: str):
        self.node_clicked.emit(name)

    def _on_node_toggled(self, name: str, enabled: bool):
        self.set_node_enabled(name, enabled)


class NodeGraphScene(QGraphicsScene):
    """节点拓扑图的图形场景。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 800, 600)


class NodeItem(QGraphicsObject):
    """拓扑图中的单个节点。

    显示：名称、复选框、类型标签。
    颜色：蓝色=必选，绿色=推荐，灰色=可选。
    继承 QGraphicsObject 以支持信号。
    """

    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"

    node_clicked = Signal(str)
    node_toggled = Signal(str, bool)

    # 复选框相关常量
    CHECKBOX_SIZE = 14
    CHECKBOX_MARGIN = 8

    def __init__(self, name: str, node_type: str = OPTIONAL, enabled: bool = True):
        super().__init__()
        self.name = name
        self.node_type = node_type
        self.enabled = enabled
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setCursor(Qt.PointingHandCursor)
        # 预计算复选框位置，避免每次绘制都计算
        self._checkbox_rect = QRectF(
            NODE_WIDTH - self.CHECKBOX_SIZE - self.CHECKBOX_MARGIN,
            (NODE_HEIGHT - self.CHECKBOX_SIZE) / 2,
            self.CHECKBOX_SIZE,
            self.CHECKBOX_SIZE,
        )

    def boundingRect(self) -> QRectF:
        '''返回节点占用的矩形区域。'''
        return QRectF(0, 0, NODE_WIDTH, NODE_HEIGHT)

    def paint(self, painter: QPainter, option, widget):
        '''根据节点类型和启用状态绘制节点外观。'''
        rect = self.boundingRect()
        color = _type_color(self.node_type)
        border_color = color.darker(120)

        # ---- 背景 ----
        if not self.enabled:
            bg_color = COLOR_DISABLED
            border_pen = QPen(COLOR_DISABLED.darker(110), 1.5)
        else:
            bg_color = color.lighter(145)
            border_pen = QPen(border_color, 2)

        painter.setPen(border_pen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, 8, 8)

        # ---- 左侧类型色块 ----
        color_block = QRectF(0, 0, 6, NODE_HEIGHT)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color if self.enabled else COLOR_DISABLED))
        painter.drawRoundedRect(color_block.adjusted(0, 2, 0, -2), 3, 3)

        # ---- 节点名称 ----
        text_color = Qt.black if self.enabled else COLOR_DISABLED_TEXT
        painter.setPen(text_color)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        name_rect = QRectF(12, 6, NODE_WIDTH - 30 - self.CHECKBOX_SIZE - self.CHECKBOX_MARGIN, 22)
        painter.drawText(name_rect, Qt.AlignLeft | Qt.AlignVCenter, self.name)

        # ---- 类型标签 ----
        font.setPointSize(8)
        font.setBold(False)
        painter.setFont(font)
        label = _type_label(self.node_type)
        label_rect = QRectF(12, 30, 60, 18)
        painter.setPen(color if self.enabled else COLOR_DISABLED_TEXT)
        painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignVCenter, label)

        # ---- 复选框 ----
        self._paint_checkbox(painter)

    def _paint_checkbox(self, painter: QPainter):
        """绘制复选框。"""
        cb = self._checkbox_rect
        # 边框
        painter.setPen(QPen(COLOR_CHECKBOX_BORDER, 1.5))
        painter.setBrush(QBrush(Qt.white if self.enabled else QColor(240, 240, 240)))
        painter.drawRoundedRect(cb, 3, 3)

        # 勾选标记
        if self.enabled and self.node_type != self.MANDATORY:
            # 可禁用节点：显示勾
            painter.setPen(QPen(COLOR_CHECKBOX_CHECK, 2))
            painter.drawLine(
                QPointF(cb.left() + 3, cb.center().y()),
                QPointF(cb.center().x() - 1, cb.bottom() - 3),
            )
            painter.drawLine(
                QPointF(cb.center().x() - 1, cb.bottom() - 3),
                QPointF(cb.right() - 3, cb.top() + 3),
            )
        elif self.node_type == self.MANDATORY:
            # mandatory：锁图标（用小矩形表示不可操作）
            painter.setPen(QPen(QColor(180, 180, 180), 1))
            painter.setBrush(QBrush(QColor(220, 220, 220)))
            lock_rect = cb.adjusted(3, 3, -3, -3)
            painter.drawRoundedRect(lock_rect, 2, 2)

    def mousePressEvent(self, event):
        if self._checkbox_rect.contains(event.pos()):
            if self.node_type != self.MANDATORY:
                self.node_toggled.emit(self.name, not self.enabled)
        else:
            self.node_clicked.emit(self.name)
        super().mousePressEvent(event)


class EdgeItem(QGraphicsLineItem):
    """有向依赖连线，带箭头。"""

    ARROW_SIZE = 8

    def __init__(self, parent_item: NodeItem, child_item: NodeItem):
        super().__init__()
        self.parent_item = parent_item
        self.child_item = child_item
        self.setZValue(-1)  # 连线在节点下方
        self.update_visual()

    def update_visual(self):
        """根据节点状态更新连线样式。"""
        enabled = self.parent_item.enabled and self.child_item.enabled
        if enabled:
            pen = QPen(COLOR_EDGE, 1.5, Qt.SolidLine)
        else:
            pen = QPen(COLOR_EDGE_DISABLED, 1, Qt.DashLine)
        self.setPen(pen)

        # 更新位置
        p_center = self.parent_item.pos() + QPointF(NODE_WIDTH / 2, NODE_HEIGHT)
        c_center = self.child_item.pos() + QPointF(NODE_WIDTH / 2, 0)
        self.setLine(p_center.x(), p_center.y(), c_center.x(), c_center.y())

    def paint(self, painter, option, widget):
        line = self.line()
        if line.length() < 1:
            return

        painter.setPen(self.pen())
        painter.drawLine(line)

        # 箭头
        dx = line.p2().x() - line.p1().x()
        dy = line.p2().y() - line.p1().y()
        line_angle = math.atan2(dy, dx)

        tip = line.p2()
        p1 = QPointF(
            tip.x() - self.ARROW_SIZE * math.cos(line_angle - math.pi / 6),
            tip.y() - self.ARROW_SIZE * math.sin(line_angle - math.pi / 6),
        )
        p2 = QPointF(
            tip.x() - self.ARROW_SIZE * math.cos(line_angle + math.pi / 6),
            tip.y() - self.ARROW_SIZE * math.sin(line_angle + math.pi / 6),
        )

        arrow = QPolygonF([tip, p1, p2])
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.pen().color()))
        painter.drawPolygon(arrow)
