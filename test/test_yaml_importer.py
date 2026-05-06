"""YAML 导入器测试。"""

import os
import tempfile

from nav2_launch_studio.core.yaml_importer import YamlImporter
from nav2_launch_studio.core.yaml_generator import YamlGenerator
from nav2_launch_studio.core.project_model import ProjectModel


SAMPLE_YAML = """\
amcl:
  ros__parameters:
    use_sim_time: false
    alpha1: 0.2
    alpha2: 0.2
    alpha3: 0.2
    alpha4: 0.2
    alpha5: 0.2

bt_navigator:
  ros__parameters:
    use_sim_time: false
    global_frame: map
    robot_base_frame: base_link
    odom_topic: /odom
    bt_loop_duration: 10
    default_server_timeout: 20
    default_bt_xml_filename: navigate_to_pose_w_replanning_and_recovery.xml
    navigators: ["navigate_to_pose", "navigate_through_poses"]

controller_server:
  ros__parameters:
    use_sim_time: false
    controller_frequency: 20.0
    controller_plugins: ["FollowPath"]
    FollowPath:
      plugin: "nav2_mppi_controller::MPPIController"
      costmap_update_timeout: 0.3
      failure_tolerance: 0.3

planner_server:
  ros__parameters:
    expected_planner_frequency: 20.0
    use_sim_time: false
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_smac_planner/SmacPlanner2D"

behavior_server:
  ros__parameters:
    costmap_topic: local_costmap/costmap_raw
    footprint_topic: local_costmap/published_footprint
    cycle_frequency: 10.0
    behavior_plugins: ["spin", "backup", "wait"]
    spin:
      plugin: "nav2_behaviors::Spin"
    backup:
      plugin: "nav2_behaviors::BackUp"
    wait:
      plugin: "nav2_behaviors::Wait"

global_costmap:
  global_costmap:
    ros__parameters:
      update_frequency: 1.0
      publish_frequency: 1.0
      global_frame: map
      robot_base_frame: base_link
      use_sim_time: false
      robot_radius: 0.22
      resolution: 0.05
      track_unknown_space: true
      plugins: ["static_layer", "obstacle_layer", "inflation_layer"]
      static_layer:
        plugin: "nav2_costmap_2d::StaticLayer"
      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
      always_send_full_costmap: true

local_costmap:
  local_costmap:
    ros__parameters:
      update_frequency: 5.0
      publish_frequency: 5.0
      global_frame: odom
      robot_base_frame: base_link
      use_sim_time: false
      rolling_window: true
      width: 3
      height: 3
      resolution: 0.05
      robot_radius: 0.22
      plugins: ["obstacle_layer", "inflation_layer"]
      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
      always_send_full_costmap: true
"""


def test_importer_from_text():
    """测试从文本导入 YAML。"""
    importer = YamlImporter()
    model, report = importer.import_text(SAMPLE_YAML, project_name="test_import")

    assert model is not None
    assert model.project_name == "test_import"


def test_importer_nodes():
    """测试导入后节点状态正确。"""
    importer = YamlImporter()
    model, _ = importer.import_text(SAMPLE_YAML)

    assert model.nodes["bt_navigator"]["enabled"] is True
    assert model.nodes["controller_server"]["enabled"] is True
    assert model.nodes["planner_server"]["enabled"] is True
    assert model.nodes["behavior_server"]["enabled"] is True
    assert model.nodes["amcl"]["enabled"] is True


def test_importer_plugins():
    """测试导入后插件配置正确（通用读取，detail 格式）。"""
    importer = YamlImporter()
    model, _ = importer.import_text(SAMPLE_YAML)

    # 规划器
    planner = model.plugins["planner"]
    assert planner["instance_name"] == "GridBased"
    assert planner["plugin_type"] == "nav2_smac_planner/SmacPlanner2D"

    # 控制器
    controller = model.plugins["controller"]
    assert controller["instance_name"] == "FollowPath"
    assert controller["plugin_type"] == "nav2_mppi_controller::MPPIController"
    # 控制器插件参数
    assert controller["params"]["costmap_update_timeout"] == 0.3
    assert controller["params"]["failure_tolerance"] == 0.3

    # Recovery 行为
    recoveries = model.plugins["recovery_behaviors"]
    inst_names = [r["instance_name"] for r in recoveries]
    assert "spin" in inst_names
    assert "backup" in inst_names
    assert "wait" in inst_names


def test_importer_bt_tree():
    """测试导入后 BT 树路径正确。"""
    importer = YamlImporter()
    model, _ = importer.import_text(SAMPLE_YAML)

    assert "navigate_to_pose_w_replanning_and_recovery.xml" in model.bt_tree


def test_importer_report():
    """测试导入报告包含映射信息。"""
    importer = YamlImporter()
    _, report = importer.import_text(SAMPLE_YAML)

    assert report.mapped_count > 0


def test_importer_invalid_yaml():
    """测试导入无效 YAML 返回 None。"""
    importer = YamlImporter()
    model, report = importer.import_text("not: valid: yaml:")

    assert model is None


def test_importer_from_file():
    """测试从文件导入。"""
    importer = YamlImporter()
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8",
    ) as f:
        f.write(SAMPLE_YAML)
        tmp_path = f.name

    try:
        model, report = importer.import_file(tmp_path)
        assert model is not None
        assert model.project_name == os.path.splitext(os.path.basename(tmp_path))[0]
    finally:
        os.unlink(tmp_path)


def test_importer_costmap_layers():
    """测试导入代价地图层。"""
    importer = YamlImporter()
    model, _ = importer.import_text(SAMPLE_YAML)

    global_layers = model.plugins.get("global_costmap_layers", [])
    global_inst_names = [l["instance_name"] for l in global_layers]
    assert "static_layer" in global_inst_names
    assert "obstacle_layer" in global_inst_names
    assert "inflation_layer" in global_inst_names

    local_layers = model.plugins.get("local_costmap_layers", [])
    local_inst_names = [l["instance_name"] for l in local_layers]
    assert "obstacle_layer" in local_inst_names
    assert "inflation_layer" in local_inst_names


def test_importer_node_params():
    """测试非插件参数正确提取到 params。"""
    importer = YamlImporter()
    model, _ = importer.import_text(SAMPLE_YAML)

    # amcl 的参数应该全在 params 中
    amcl_params = model.params.get("amcl", {})
    assert "use_sim_time" in amcl_params
    assert amcl_params["alpha1"] == 0.2

    # controller_server 的参数（含插件实例 dict）
    ctrl_params = model.params.get("controller_server", {})
    assert "controller_frequency" in ctrl_params
    assert "use_sim_time" in ctrl_params
    # controller_plugins 列表键不在 params 中
    assert "controller_plugins" not in ctrl_params
    # FollowPath 实例 dict 在 params 中（含 plugin 和子参数）
    assert "FollowPath" in ctrl_params
    assert isinstance(ctrl_params["FollowPath"], dict)
    assert ctrl_params["FollowPath"]["plugin"] == "nav2_mppi_controller::MPPIController"


def test_roundtrip():
    """测试 生成 → 导入 的 round-trip。"""
    # 1. 创建模型并添加参数
    model = ProjectModel(project_name="roundtrip_test")
    model.plugins["planner"]["params"] = {"tolerance": 0.5}
    model.params["controller_server"] = {
        "controller_frequency": 10.0,
        "use_sim_time": False,
    }
    model.nodes["behavior_server"]["enabled"] = True

    # 2. 生成 YAML
    gen = YamlGenerator()
    yaml_text = gen.generate(model)

    # 3. 导入
    importer = YamlImporter()
    imported, report = importer.import_text(yaml_text, project_name="roundtrip_test")

    assert imported is not None
    # 验证规划器
    assert imported.plugins["planner"]["plugin_type"] == "nav2_navfn_planner/NavfnPlanner"
    assert imported.plugins["planner"]["params"]["tolerance"] == 0.5
    # 验证控制器参数
    assert imported.params["controller_server"]["controller_frequency"] == 10.0
    # 验证节点状态
    assert imported.nodes["behavior_server"]["enabled"] is True


def test_importer_custom_plugin():
    """测试导入自定义插件（非内置）。"""
    custom_yaml = """\
planner_server:
  ros__parameters:
    planner_plugins: ["MyPlanner"]
    MyPlanner:
      plugin: "my_pkg/MyCustomPlanner"
      custom_param: 42
"""
    importer = YamlImporter()
    model, _ = importer.import_text(custom_yaml)

    planner = model.plugins["planner"]
    assert planner["instance_name"] == "MyPlanner"
    assert planner["plugin_type"] == "my_pkg/MyCustomPlanner"
    assert planner["params"]["custom_param"] == 42
