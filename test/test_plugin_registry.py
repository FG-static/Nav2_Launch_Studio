"""插件注册表测试。"""


def test_registry_import():
    """测试 PluginRegistry 可正常导入。"""
    from nav2_launch_studio.core.plugin_registry import PluginRegistry
    reg = PluginRegistry()
    assert reg is not None


def test_builtin_planners():
    """测试内置规划器可用。"""
    from nav2_launch_studio.core.plugin_registry import PluginRegistry
    reg = PluginRegistry()
    planners = reg.get_plugins_by_category("planner")
    assert "navfn" in planners
    assert "smac_hybrid" in planners


def test_custom_plugin_registration():
    """测试自定义插件注册与检索。"""
    from nav2_launch_studio.core.plugin_registry import PluginRegistry
    reg = PluginRegistry()
    reg.register_custom_plugin({
        "display_name": "TestPlanner",
        "plugin_type": "test_pkg/TestPlanner",
        "instance_name": "TestPlanner",
        "category": "planner",
    })
    planners = reg.get_plugins_by_category("planner")
    custom_key = "custom_TestPlanner"
    assert custom_key in planners
    assert planners[custom_key]["is_custom"] is True
