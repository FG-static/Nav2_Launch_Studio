"""节点依赖关系测试。"""


def test_mandatory_nodes_cannot_disable():
    """必选节点不应允许禁用。"""
    from nav2_launch_studio.core.node_dependencies import check_disable_allowed
    allowed, reason, _ = check_disable_allowed("bt_navigator")
    assert not allowed
    assert "必选" in reason


def test_optional_nodes_can_disable():
    """可选节点应允许禁用。"""
    from nav2_launch_studio.core.node_dependencies import check_disable_allowed
    allowed, _, _ = check_disable_allowed("velocity_smoother")
    assert allowed


def test_dependents_detected():
    """禁用有依赖的节点时应列出受影响节点。"""
    from nav2_launch_studio.core.node_dependencies import get_dependents
    # controller_server 是必选节点但有被依赖关系
    affected = get_dependents("controller_server")
    assert "bt_navigator" in affected

    # velocity_smoother 依赖 controller_server
    from nav2_launch_studio.core.node_dependencies import check_disable_allowed
    allowed, reason, affected2 = check_disable_allowed("velocity_smoother")
    assert allowed
