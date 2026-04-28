"""YAML 生成器测试。"""

from nav2_launch_studio.core.project_model import ProjectModel
from nav2_launch_studio.core.yaml_generator import YamlGenerator


def test_generator_import():
    """测试 YamlGenerator 可正常导入。"""
    gen = YamlGenerator()
    assert gen is not None


def test_generator_produces_string():
    """测试 generate() 返回字符串。"""
    gen = YamlGenerator()
    model = ProjectModel(project_name="test_project")
    result = gen.generate(model)
    assert isinstance(result, str)


def test_generator_includes_project_name():
    """测试生成的 YAML 包含项目名。"""
    gen = YamlGenerator()
    model = ProjectModel(project_name="my_robot")
    result = gen.generate(model)
    assert "my_robot" in result


def test_generator_includes_enabled_nodes():
    """测试生成的 YAML 包含启用的节点。"""
    gen = YamlGenerator()
    model = ProjectModel(project_name="test")
    result = gen.generate(model)
    assert "bt_navigator:" in result
    assert "controller_server:" in result
    assert "planner_server:" in result


def test_generator_includes_plugins():
    """测试生成的 YAML 包含插件声明（零参数）。"""
    gen = YamlGenerator()
    model = ProjectModel(project_name="test")
    result = gen.generate(model)
    # 默认规划器 NavFn
    assert "nav2_navfn_planner/NavfnPlanner" in result
    # 默认控制器 DWB
    assert "dwb_core::DWBLocalPlanner" in result
    # 零参数：不应包含 use_sim_time 等硬编码参数
    assert "use_sim_time" not in result


def test_generator_includes_costmap():
    """测试生成的 YAML 包含代价地图配置。"""
    gen = YamlGenerator()
    model = ProjectModel(project_name="test")
    result = gen.generate(model)
    assert "global_costmap:" in result
    assert "local_costmap:" in result
    assert "static_layer" in result


def test_generator_includes_bt_tree():
    """测试生成的 YAML 包含 BT 树路径。"""
    gen = YamlGenerator()
    model = ProjectModel(project_name="test")
    result = gen.generate(model)
    assert "navigate_to_pose_w_replanning_and_recovery.xml" in result


def test_generator_disabled_node_not_in_output():
    """测试禁用的节点不出现在输出中。"""
    gen = YamlGenerator()
    model = ProjectModel(project_name="test")
    model.nodes["velocity_smoother"]["enabled"] = False
    result = gen.generate(model)
    assert "velocity_smoother:" not in result


def test_generator_renders_plugin_params():
    """测试插件参数被正确渲染。"""
    gen = YamlGenerator()
    model = ProjectModel(project_name="test")
    model.plugins["controller"]["params"] = {
        "costmap_update_timeout": 0.3,
        "failure_tolerance": 0.3,
    }
    result = gen.generate(model)
    assert "costmap_update_timeout: 0.3" in result
    assert "failure_tolerance: 0.3" in result


def test_generator_renders_node_params():
    """测试节点参数被正确渲染。"""
    gen = YamlGenerator()
    model = ProjectModel(project_name="test")
    model.params["amcl"] = {
        "use_sim_time": False,
        "alpha1": 0.2,
    }
    result = gen.generate(model)
    assert "use_sim_time: false" in result
    assert "alpha1: 0.2" in result


def test_generator_renders_nested_params():
    """测试嵌套参数被正确渲染。"""
    gen = YamlGenerator()
    model = ProjectModel(project_name="test")
    model.params["controller_server"] = {
        "progress_checker_plugins": ["progress_checker"],
        "progress_checker": {
            "plugin": "nav2_controller::SimpleProgressChecker",
            "required_movement_radius": 0.5,
        },
    }
    result = gen.generate(model)
    assert "progress_checker_plugins:" in result
    assert "progress_checker:" in result
    assert "required_movement_radius: 0.5" in result


def test_generator_custom_plugin():
    """测试自定义插件（非内置）正确渲染。"""
    gen = YamlGenerator()
    model = ProjectModel(project_name="test")
    model.plugins["planner"] = {
        "instance_name": "MyPlanner",
        "plugin_type": "my_pkg/MyCustomPlanner",
        "params": {"custom_param": 42},
    }
    result = gen.generate(model)
    assert "MyPlanner:" in result
    assert "my_pkg/MyCustomPlanner" in result
    assert "custom_param: 42" in result
