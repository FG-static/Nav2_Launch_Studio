"""模版管理器测试。"""

import json
import os
import tempfile

import pytest


@pytest.fixture
def project_dir(tmp_path):
    """创建临时项目目录。"""
    return str(tmp_path / "test_project")


@pytest.fixture
def manager(project_dir):
    """创建 TemplateManager 实例。"""
    from nav2_launch_studio.core.template_manager import TemplateManager
    return TemplateManager(project_dir)


def test_save_template(manager):
    """测试保存模版。"""
    params = {"FollowPath": {"min_velocity": 0.0, "max_velocity": 0.5}}
    path = manager.save_template("DWB 高精度", "controller_server", params)
    assert os.path.isfile(path)
    # 验证文件内容
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["name"] == "DWB 高精度"
    assert data["node_name"] == "controller_server"
    assert data["params"] == params
    assert "created_at" in data


def test_save_template_empty_name(manager):
    """测试空名称抛出异常。"""
    with pytest.raises(ValueError, match="不能为空"):
        manager.save_template("", "controller_server", {})


def test_list_templates(manager, project_dir):
    """测试列出模版。"""
    # 无模版时返回空列表
    assert manager.list_templates() == []
    # 保存两个模版
    manager.save_template("tpl_a", "planner_server", {"key": 1})
    manager.save_template("tpl_b", "controller_server", {"key": 2})
    templates = manager.list_templates()
    assert len(templates) == 2
    assert templates[0]["name"] == "tpl_a"  # 按名称排序
    assert templates[1]["name"] == "tpl_b"
    assert templates[0]["node_name"] == "planner_server"


def test_list_templates_skips_invalid(manager, project_dir):
    """测试列出模版时跳过无效文件。"""
    manager.save_template("good", "node", {"k": "v"})
    # 写入一个损坏的 JSON
    bad_path = os.path.join(project_dir, "templates", "bad.json")
    with open(bad_path, "w") as f:
        f.write("not json {{{")
    # 写入一个非 JSON 文件
    other_path = os.path.join(project_dir, "templates", "readme.txt")
    with open(other_path, "w") as f:
        f.write("hello")
    templates = manager.list_templates()
    assert len(templates) == 1
    assert templates[0]["name"] == "good"


def test_load_template(manager):
    """测试加载模版。"""
    params = {"smoother_server": {"tolerance": 0.25}}
    path = manager.save_template("my_tpl", "smoother_server", params)
    tmpl = manager.load_template(path)
    assert tmpl["name"] == "my_tpl"
    assert tmpl["node_name"] == "smoother_server"
    assert tmpl["params"] == params


def test_load_template_not_found(manager):
    """测试加载不存在的模版。"""
    with pytest.raises(FileNotFoundError):
        manager.load_template("/nonexistent/path.json")


def test_load_template_invalid(manager, project_dir):
    """测试加载格式错误的模版。"""
    bad_path = os.path.join(project_dir, "templates", "bad.json")
    with open(bad_path, "w") as f:
        json.dump({"name": "no_params"}, f)
    with pytest.raises(ValueError, match="缺少 params"):
        manager.load_template(bad_path)


def test_delete_template(manager):
    """测试删除模版。"""
    path = manager.save_template("to_delete", "node", {"k": "v"})
    assert os.path.isfile(path)
    manager.delete_template(path)
    assert not os.path.isfile(path)


def test_delete_template_not_found(manager):
    """测试删除不存在的模版。"""
    with pytest.raises(FileNotFoundError):
        manager.delete_template("/nonexistent/path.json")


def test_overwrite_template(manager):
    """测试同名模版覆盖保存。"""
    manager.save_template("same_name", "node", {"ver": 1})
    manager.save_template("same_name", "node", {"ver": 2})
    templates = manager.list_templates()
    assert len(templates) == 1
    tmpl = manager.load_template(templates[0]["file"])
    assert tmpl["params"]["ver"] == 2


def test_nested_params(manager):
    """测试嵌套参数的完整 round-trip。"""
    params = {
        "FollowPath": {
            "plugin": "dwb_core::DWBLocalPlanner",
            "min_velocity": 0.0,
            "critics": {"GoalDist": {"scale": 32.0}, "PathAlign": {"scale": 10.0}},
        }
    }
    path = manager.save_template("nested", "controller_server", params)
    tmpl = manager.load_template(path)
    assert tmpl["params"]["FollowPath"]["critics"]["GoalDist"]["scale"] == 32.0


def test_special_chars_in_name(manager):
    """测试名称中含特殊字符时的文件名清理。"""
    path = manager.save_template("DWB/高精度 config", "node", {"k": "v"})
    filename = os.path.basename(path)
    assert "/" not in filename
    assert os.path.isfile(path)
