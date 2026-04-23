"""Nav2 节点依赖关系定义。

对应 PRD 3.3：节点启用/禁用行为的依赖规则。
"""

# 依赖图：节点 -> 它所依赖的节点列表
NODE_DEPENDENCIES = {
    "bt_navigator": ["controller_server", "planner_server"],
    "controller_server": [],
    "planner_server": [],
    "behavior_server": [],
    "amcl": ["map_server"],
    "map_server": [],
    "lifecycle_manager": ["bt_navigator", "controller_server", "planner_server"],
    "velocity_smoother": ["controller_server"],
    "waypoint_follower": ["bt_navigator"],
}

# 反向依赖：节点 -> 依赖它的节点列表
REVERSE_DEPENDENCIES = {}
for node, deps in NODE_DEPENDENCIES.items():
    for dep in deps:
        REVERSE_DEPENDENCIES.setdefault(dep, []).append(node)

# 节点分类
NODE_TYPES = {
    "bt_navigator": "mandatory",
    "controller_server": "mandatory",
    "planner_server": "mandatory",
    "behavior_server": "recommended",
    "amcl": "recommended",
    "map_server": "recommended",
    "lifecycle_manager": "recommended",
    "velocity_smoother": "optional",
    "waypoint_follower": "optional",
}

MANDATORY_NODES = {n for n, t in NODE_TYPES.items() if t == "mandatory"}


def check_disable_allowed(node_name: str) -> tuple:
    """检查节点是否允许禁用。

    返回：
        (是否允许: bool, 原因: str, 受影响节点: list)
    """
    if node_name in MANDATORY_NODES:
        return False, f"{node_name} 是必选节点，不可禁用", []

    dependents = REVERSE_DEPENDENCIES.get(node_name, [])
    if dependents:
        return (
            True,
            f"以下节点依赖 {node_name}：{', '.join(dependents)}",
            dependents,
        )

    return True, "", []


def get_dependents(node_name: str) -> list:
    """获取依赖指定节点的节点列表。"""
    return REVERSE_DEPENDENCIES.get(node_name, [])
