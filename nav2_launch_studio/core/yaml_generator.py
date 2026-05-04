"""YAML 生成器 - 从项目模型生成 nav2_params.yaml。"""

import os
from typing import Optional

import jinja2


def _yaml_value(value):
    """Jinja2 filter：将 Python 标量值格式化为 YAML 值。"""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    # 字符串
    s = str(value)
    if s in ("true", "false", "null", "~"):
        return s
    try:
        float(s)
        return s
    except ValueError:
        pass
    # 含特殊字符则加引号
    if any(c in s for c in " :#{}[],'\"|>&*?!%@`"):
        return f'"{s}"'
    return s


def _yaml_list(items):
    """Jinja2 filter：将列表转为 YAML 行内列表格式。"""
    if not items:
        return "[]"
    parts = []
    for item in items:
        if isinstance(item, str):
            parts.append(f'"{item}"')
        elif isinstance(item, bool):
            parts.append("true" if item else "false")
        elif isinstance(item, (int, float)):
            parts.append(str(item))
        elif isinstance(item, dict):
            inner = ", ".join(f"{k}: {_yaml_value(v)}" for k, v in item.items())
            parts.append("{" + inner + "}")
        else:
            parts.append(str(item))
    return "[" + ", ".join(parts) + "]"


def _remove_plugin_duplicates(node_params: dict, plugins: dict):
    """从 node_params 中移除已作为主插件声明的实例名和列表键，避免重复输出。

    模板会单独输出 controller/FollowPath、planner/GridBased 等插件声明，
    如果 node_params 中也包含这些 key，就会导致重复。
    同时移除插件列表键（如 planner_plugins、controller_plugins、behavior_plugins），
    因为模板也会从插件元数据 _list_key 输出这些键。
    """
    # 单选插件：instance_name + 插件列表键
    for node_name, plugin_key in [
        ("controller_server", "controller"),
        ("planner_server", "planner"),
    ]:
        plugin = plugins.get(plugin_key)
        if not plugin or not isinstance(plugin, dict):
            continue
        if node_name in node_params:
            inst_name = plugin.get("instance_name", "")
            if inst_name:
                node_params[node_name].pop(inst_name, None)
            list_key = plugin.get("_list_key", "")
            if list_key:
                node_params[node_name].pop(list_key, None)

    # 多选插件：recovery_behaviors 的每个实例名 + 列表键
    recovery = plugins.get("recovery_behaviors")
    if isinstance(recovery, list) and recovery:
        if "behavior_server" in node_params:
            for inst_name in _get_instance_names(recovery):
                node_params["behavior_server"].pop(inst_name, None)
            # 移除 behavior_plugins 列表键
            list_key = recovery[0].get("_list_key", "") if recovery else ""
            if list_key:
                node_params["behavior_server"].pop(list_key, None)

    # 代价地图层
    for cm_key, layer_key in [
        ("global_costmap", "global_costmap_layers"),
        ("local_costmap", "local_costmap_layers"),
    ]:
        layers = plugins.get(layer_key)
        if isinstance(layers, list) and layers:
            if cm_key in node_params:
                for inst_name in _get_instance_names(layers):
                    node_params[cm_key].pop(inst_name, None)


def _get_instance_names(plugin_list):
    """从插件列表中提取 instance_name。"""
    if not isinstance(plugin_list, list):
        return []
    return [p.get("instance_name", "") for p in plugin_list if isinstance(p, dict)]


class YamlGenerator:
    """从项目配置生成 nav2_params.yaml。

    设计理念：用户自由，零硬编码参数。
    - 模板只输出结构骨架（节点名、ros__parameters、插件声明）
    - 所有参数值从 model.plugins.*.params 和 model.params 动态渲染
    - 不依赖 PluginRegistry
    """

    def __init__(self, template_dir: Optional[str] = None):
        if template_dir is None:
            template_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "templates"
            )
        self.template_dir = template_dir

    def generate(self, project_model) -> str:
        """从项目模型生成 nav2_params.yaml 内容。

        参数：
            project_model: 包含完整配置的 ProjectModel 实例

        返回：
            YAML 字符串内容
        """
        context = self._build_context(project_model)

        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        env.filters["yaml_value"] = _yaml_value
        env.filters["yaml_list"] = _yaml_list

        template = env.get_template("nav2_params.yaml.jinja2")
        return template.render(**context)

    def generate_preview(self, project_model) -> str:
        """生成轻量级预览（可能跳过注释以提升速度）。"""
        return self.generate(project_model)

    def _build_context(self, model) -> dict:
        """从 ProjectModel 构建 Jinja2 模板上下文。"""
        enabled_nodes = [
            name for name, cfg in model.nodes.items()
            if cfg.get("enabled", True)
        ]

        # 构建 node_params：合并 model.params 和 bt_tree
        node_params = {}
        for key, value in (model.params or {}).items():
            node_params[key] = dict(value) if isinstance(value, dict) else value

        # 将 bt_tree 合并到 bt_navigator 参数中
        bt_nav_params = dict(node_params.get("bt_navigator", {}))
        if "default_bt_xml_filename" not in bt_nav_params and model.bt_tree:
            bt_nav_params["default_bt_xml_filename"] = model.bt_tree
        if bt_nav_params:
            node_params["bt_navigator"] = bt_nav_params

        # 从 node_params 中移除已作为主插件输出的实例名，避免重复
        plugins = model.plugins or {}
        _remove_plugin_duplicates(node_params, plugins)

        return {
            "project_name": model.project_name,
            "ros2_version": model.ros2_version,
            "robot_type": model.robot_type,
            "namespace": model.namespace,
            "enabled_nodes": enabled_nodes,
            "plugins": plugins,
            "node_params": node_params,
        }
