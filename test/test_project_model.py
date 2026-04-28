"""项目模型测试。"""


def test_model_import():
    """测试 ProjectModel 可正常导入。"""
    from nav2_launch_studio.core.project_model import ProjectModel
    model = ProjectModel()
    assert model.version == "1.4"


def test_model_defaults():
    """测试默认节点和插件已填充（v1.4 detail 格式）。"""
    from nav2_launch_studio.core.project_model import ProjectModel
    model = ProjectModel(project_name="test_project")
    assert "bt_navigator" in model.nodes
    # 新格式：planner/controller/smoother 为 detail dict
    assert "planner" in model.plugins
    assert "instance_name" in model.plugins["planner"]
    assert "plugin_type" in model.plugins["planner"]
    assert "params" in model.plugins["planner"]
    # 多选插件为列表
    assert isinstance(model.plugins["global_costmap_layers"], list)
    assert isinstance(model.plugins["recovery_behaviors"], list)


def test_model_to_dict():
    """测试序列化为字典。"""
    from nav2_launch_studio.core.project_model import ProjectModel
    model = ProjectModel(project_name="test")
    d = model.to_dict()
    assert d["project_name"] == "test"
    assert d["version"] == "1.4"


def test_model_migrate_old_plugins():
    """测试从旧格式（v1.3）插件迁移到新格式（v1.4）。"""
    from nav2_launch_studio.core.project_model import ProjectModel
    old_data = {
        "version": "1.3",
        "project_name": "migrate_test",
        "plugins": {
            "global_planner": "navfn",
            "local_planner": "dwb",
            "path_smoother": "simple",
            "global_costmap_layers": ["static", "obstacle", "inflation"],
            "local_costmap_layers": ["obstacle", "inflation"],
            "recovery_behaviors": ["spin", "backup", "wait"],
        },
    }
    model = ProjectModel.from_dict(old_data)
    # 验证新格式
    assert "planner" in model.plugins
    assert model.plugins["planner"]["plugin_type"] == "nav2_navfn_planner/NavfnPlanner"
    assert "controller" in model.plugins
    assert model.plugins["controller"]["plugin_type"] == "dwb_core::DWBLocalPlanner"
    # 代价地图层
    assert isinstance(model.plugins["global_costmap_layers"], list)
    assert model.plugins["global_costmap_layers"][0]["instance_name"] == "static_layer"
