"""变更追踪器 - 追踪项目参数变更，提供 Git 工作树风格的变更状态。

变更类型与 Git 工作树状态字母对应：
- A (Added): 新增的节点或参数
- M (Modified): 修改的参数
- D (Deleted): 删除的参数
- 无标记: 未变更

高亮颜色：
- 新增: 绿色背景
- 修改: 黄色背景
- 删除: 红色背景
"""

import copy
from enum import Enum
from typing import Optional


class ChangeType(Enum):
    """变更类型枚举，对应 Git 工作树状态。"""
    NONE = ""
    ADDED = "A"
    MODIFIED = "M"
    DELETED = "D"


# 变更高亮颜色 (R, G, B)
HIGHLIGHT_ADDED = (200, 240, 200)      # 淡绿色
HIGHLIGHT_MODIFIED = (255, 245, 200)   # 淡黄色
HIGHLIGHT_DELETED = (255, 210, 210)    # 淡红色

# 变更徽标颜色 (R, G, B)
BADGE_ADDED = (40, 167, 69)        # 绿色
BADGE_MODIFIED = (255, 193, 7)     # 黄色
BADGE_DELETED = (220, 53, 69)      # 红色


def get_highlight_color(change_type: ChangeType) -> Optional[tuple]:
    """获取变更类型对应的高亮颜色 (R, G, B)。"""
    return {
        ChangeType.ADDED: HIGHLIGHT_ADDED,
        ChangeType.MODIFIED: HIGHLIGHT_MODIFIED,
        ChangeType.DELETED: HIGHLIGHT_DELETED,
    }.get(change_type)


def get_badge_color(change_type: ChangeType) -> Optional[tuple]:
    """获取变更类型对应的徽标颜色 (R, G, B)。"""
    return {
        ChangeType.ADDED: BADGE_ADDED,
        ChangeType.MODIFIED: BADGE_MODIFIED,
        ChangeType.DELETED: BADGE_DELETED,
    }.get(change_type)


class ChangeTracker:
    """变更追踪器，追踪项目参数的增删改状态。

    工作流程：
    1. 项目加载/创建时调用 save_baseline() 保存初始快照
    2. 参数变更时调用 notify_param_changed() / notify_node_added()
    3. 查询变更状态：get_node_change_type(), get_param_change_type()
    4. 项目保存时调用 clear_changes() 清除所有变更状态并更新基线
    """

    def __init__(self):
        self._baseline: dict = {}          # 初始参数快照 {node: {key: value}}
        self._baseline_nodes: dict = {}    # 初始节点配置快照
        self._current: dict = {}           # 当前参数快照
        self._current_nodes: dict = {}     # 当前节点配置
        self._new_nodes: set = set()       # 新增的节点名

    def save_baseline(self, nodes: dict, params: dict):
        """保存基线快照（项目加载/创建时调用）。

        参数：
            nodes: 项目节点配置 {name: {enabled, node_type}}
            params: 项目参数 {node_name: {key: value}}
        """
        self._baseline_nodes = copy.deepcopy(nodes)
        self._baseline = copy.deepcopy(params)
        self._current = copy.deepcopy(params)
        self._current_nodes = copy.deepcopy(nodes)
        self._new_nodes.clear()

    def clear_changes(self):
        """清除所有变更状态并更新基线（项目保存时调用）。"""
        self._baseline = copy.deepcopy(self._current)
        self._baseline_nodes = copy.deepcopy(self._current_nodes)
        self._new_nodes.clear()

    def notify_param_changed(self, node_name: str, param_key: str, value):
        """通知参数值已变更。

        参数：
            node_name: 节点名称
            param_key: 参数键
            value: 新值
        """
        if node_name not in self._current:
            self._current[node_name] = {}
        self._current[node_name][param_key] = value

    def notify_node_added(self, node_name: str):
        """通知新增了节点。

        参数：
            node_name: 新节点名称
        """
        self._new_nodes.add(node_name)
        if node_name not in self._current:
            self._current[node_name] = {}
        if node_name not in self._current_nodes:
            self._current_nodes[node_name] = {"enabled": True, "node_type": "optional"}

    def notify_params_replaced(self, node_name: str, new_params: dict):
        """通知节点参数被完整替换（专家模式）。

        参数：
            node_name: 节点名称
            new_params: 新的完整参数字典
        """
        self._current[node_name] = copy.deepcopy(new_params)

    def get_node_change_type(self, node_name: str) -> ChangeType:
        """获取节点的整体变更类型。

        返回：
            ChangeType 枚举值
        """
        # 新增节点
        if node_name in self._new_nodes:
            return ChangeType.ADDED

        # 检查参数变更
        baseline_params = self._baseline.get(node_name, {})
        current_params = self._current.get(node_name, {})

        has_added = False
        has_modified = False
        has_deleted = False

        # 检查新增和修改的参数
        for key in current_params:
            if key not in baseline_params:
                has_added = True
            elif current_params[key] != baseline_params[key]:
                has_modified = True

        # 检查删除的参数
        for key in baseline_params:
            if key not in current_params:
                has_deleted = True

        if has_added or has_modified or has_deleted:
            if has_deleted:
                return ChangeType.DELETED
            if has_modified:
                return ChangeType.MODIFIED
            return ChangeType.ADDED

        return ChangeType.NONE

    def get_param_change_type(self, node_name: str, param_key: str) -> ChangeType:
        """获取单个参数的变更类型。

        返回：
            ChangeType 枚举值
        """
        # 新增节点中的参数全部视为新增
        if node_name in self._new_nodes:
            return ChangeType.ADDED

        baseline_params = self._baseline.get(node_name, {})
        current_params = self._current.get(node_name, {})

        if param_key not in baseline_params:
            return ChangeType.ADDED
        if param_key not in current_params:
            return ChangeType.DELETED
        if current_params[param_key] != baseline_params[param_key]:
            return ChangeType.MODIFIED

        return ChangeType.NONE

    def get_changed_nodes(self) -> dict[str, ChangeType]:
        """获取所有有变更的节点及其变更类型。

        返回：
            {node_name: ChangeType} 字典
        """
        result = {}
        all_nodes = set(self._current_nodes.keys()) | set(self._baseline_nodes.keys())
        for node_name in all_nodes:
            change_type = self.get_node_change_type(node_name)
            if change_type != ChangeType.NONE:
                result[node_name] = change_type
        return result

    def get_changed_params(self, node_name: str) -> dict[str, ChangeType]:
        """获取指定节点中所有有变更的参数。

        返回：
            {param_key: ChangeType} 字典
        """
        result = {}
        baseline_params = self._baseline.get(node_name, {})
        current_params = self._current.get(node_name, {})
        all_keys = set(baseline_params.keys()) | set(current_params.keys())

        for key in all_keys:
            change_type = self.get_param_change_type(node_name, key)
            if change_type != ChangeType.NONE:
                result[key] = change_type

        return result

    def has_changes(self) -> bool:
        """是否有任何未保存的变更。"""
        for node_name in self._current_nodes:
            if self.get_node_change_type(node_name) != ChangeType.NONE:
                return True
        return False
