"""变更追踪器测试。"""

import pytest
from nav2_launch_studio.core.change_tracker import ChangeTracker, ChangeType


class TestChangeTracker:
    """ChangeTracker 单元测试。"""

    def _make_tracker(self):
        """创建带基线的追踪器。"""
        tracker = ChangeTracker()
        nodes = {
            "bt_navigator": {"enabled": True, "node_type": "mandatory"},
            "controller_server": {"enabled": True, "node_type": "mandatory"},
        }
        params = {
            "bt_navigator": {"plugin": "nav2_bt_navigator/BTNavigator", "default_nav_to_pose_bt_xml": "<root/>"},
            "controller_server": {"plugin": "dwb_core::DWBLocalPlanner", "min_vel_x": 0.0},
        }
        tracker.save_baseline(nodes, params)
        return tracker

    def test_no_changes_initially(self):
        """初始状态下无变更。"""
        tracker = self._make_tracker()
        assert tracker.get_node_change_type("bt_navigator") == ChangeType.NONE
        assert tracker.get_param_change_type("bt_navigator", "plugin") == ChangeType.NONE
        assert not tracker.has_changes()

    def test_param_modified(self):
        """修改参数应返回 MODIFIED。"""
        tracker = self._make_tracker()
        tracker.notify_param_changed("controller_server", "min_vel_x", 0.5)
        assert tracker.get_node_change_type("controller_server") == ChangeType.MODIFIED
        assert tracker.get_param_change_type("controller_server", "min_vel_x") == ChangeType.MODIFIED
        assert tracker.has_changes()

    def test_param_added(self):
        """新增参数应返回 ADDED。"""
        tracker = self._make_tracker()
        tracker.notify_param_changed("bt_navigator", "new_param", "value")
        assert tracker.get_node_change_type("bt_navigator") == ChangeType.ADDED
        assert tracker.get_param_change_type("bt_navigator", "new_param") == ChangeType.ADDED

    def test_param_deleted(self):
        """删除参数应返回 DELETED。"""
        tracker = self._make_tracker()
        # 模拟删除：从当前快照中移除
        del tracker._current["bt_navigator"]["plugin"]
        assert tracker.get_node_change_type("bt_navigator") == ChangeType.DELETED
        assert tracker.get_param_change_type("bt_navigator", "plugin") == ChangeType.DELETED

    def test_node_added(self):
        """新增节点应返回 ADDED。"""
        tracker = self._make_tracker()
        tracker.notify_node_added("custom_node")
        assert tracker.get_node_change_type("custom_node") == ChangeType.ADDED
        # 新增节点中的参数也应是 ADDED
        tracker.notify_param_changed("custom_node", "some_param", 123)
        assert tracker.get_param_change_type("custom_node", "some_param") == ChangeType.ADDED

    def test_clear_changes(self):
        """清除变更后应恢复到无变更状态。"""
        tracker = self._make_tracker()
        tracker.notify_param_changed("bt_navigator", "plugin", "new_plugin")
        assert tracker.has_changes()
        tracker.clear_changes()
        assert not tracker.has_changes()
        assert tracker.get_node_change_type("bt_navigator") == ChangeType.NONE
        # 清除后新值成为基线
        assert tracker.get_param_change_type("bt_navigator", "plugin") == ChangeType.NONE

    def test_get_changed_nodes(self):
        """get_changed_nodes 应返回所有有变更的节点。"""
        tracker = self._make_tracker()
        tracker.notify_param_changed("bt_navigator", "plugin", "changed")
        tracker.notify_param_changed("controller_server", "min_vel_x", 1.0)
        changed = tracker.get_changed_nodes()
        assert "bt_navigator" in changed
        assert "controller_server" in changed

    def test_get_changed_params(self):
        """get_changed_params 应返回指定节点的所有变更参数。"""
        tracker = self._make_tracker()
        tracker.notify_param_changed("bt_navigator", "plugin", "changed")
        tracker.notify_param_changed("bt_navigator", "new_key", "new_val")
        changed = tracker.get_changed_params("bt_navigator")
        assert "plugin" in changed
        assert "new_key" in changed
        assert changed["plugin"] == ChangeType.MODIFIED
        assert changed["new_key"] == ChangeType.ADDED

    def test_params_replaced(self):
        """批量替换参数应正确追踪。"""
        tracker = self._make_tracker()
        new_params = {"plugin": "new_plugin", "extra_param": 42}
        tracker.notify_params_replaced("bt_navigator", new_params)
        assert tracker.get_node_change_type("bt_navigator") == ChangeType.DELETED  # has deleted
        assert tracker.get_param_change_type("bt_navigator", "plugin") == ChangeType.MODIFIED
        assert tracker.get_param_change_type("bt_navigator", "extra_param") == ChangeType.ADDED
        assert tracker.get_param_change_type("bt_navigator", "default_nav_to_pose_bt_xml") == ChangeType.DELETED
