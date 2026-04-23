"""项目模型测试。"""


def test_model_import():
    """测试 ProjectModel 可正常导入。"""
    from nav2_launch_studio.core.project_model import ProjectModel
    model = ProjectModel()
    assert model.version == "1.3"


def test_model_defaults():
    """测试默认节点和插件已填充。"""
    from nav2_launch_studio.core.project_model import ProjectModel
    model = ProjectModel(project_name="test_project")
    assert "bt_navigator" in model.nodes
    assert "global_planner" in model.plugins


def test_model_to_dict():
    """测试序列化为字典。"""
    from nav2_launch_studio.core.project_model import ProjectModel
    model = ProjectModel(project_name="test")
    d = model.to_dict()
    assert d["project_name"] == "test"
    assert d["version"] == "1.3"
