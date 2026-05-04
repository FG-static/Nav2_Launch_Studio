"""YAML 导入器 - 通用解析 nav2_params.yaml 并映射到项目模型。

设计理念：用户自由，一般化读取。
- 不识别具体插件类型，只用通用方式读取所有插件
- 每个插件声明 → {instance_name, plugin_type, params}
- 天然支持自定义插件
- 分离：插件实例 → model.plugins，其余参数 → model.params
"""

import os
from dataclasses import dataclass, field
from typing import Optional

import yaml

from nav2_launch_studio.core.project_model import ProjectModel, SensorConfig, WizardConfig


@dataclass
class ImportReport:
    """YAML 导入结果报告。"""
    mapped_count: int = 0
    unmapped_count: int = 0
    mapped_items: list = None
    unmapped_items: list = None

    def __post_init__(self):
        if self.mapped_items is None:
            self.mapped_items = []
        if self.unmapped_items is None:
            self.unmapped_items = []


class YamlImporter:
    """解析已有的 nav2_params.yaml 并映射到项目模型。

    通用读取策略：
    - 识别节点命名空间 → 标记启用状态
    - 识别 *_plugins 列表声明 → 提取插件实例
    - 每个 plugin 实例：instance_name、plugin_type、其余为 params
    - 非插件的参数 → model.params
    - 代价地图双层嵌套 → 特殊处理
    """

    KNOWN_NODES = {
        "bt_navigator", "controller_server", "planner_server",
        "behavior_server", "amcl", "map_server",
        "velocity_smoother", "waypoint_follower",
        "lifecycle_manager", "smoother_server",
    }

    # 不应识别为节点的顶层键（代价地图等特殊结构）
    NON_NODE_KEYS = {
        "global_costmap", "local_costmap",
    }

    # 已知的插件列表键名 → 对应 model.plugins 中的键
    # 支持别名：同一个 model_key 可对应多个 (node, key) 组合
    PLUGIN_LIST_MAP = {
        ("planner_server", "planner_plugins"): "planner",
        ("planner_server", "planner_plugin_ids"): "planner",
        ("controller_server", "controller_plugins"): "controller",
        ("smoother_server", "smoother_plugins"): "smoother",
        ("behavior_server", "behavior_plugins"): "recovery_behaviors",
    }

    def __init__(self):
        pass

    def import_file(self, yaml_path: str) -> tuple:
        """导入 nav2_params.yaml 文件。

        返回：
            (ProjectModel, ImportReport) 元组
        """
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_text = f.read()
        project_name = os.path.splitext(os.path.basename(yaml_path))[0]
        return self.import_text(yaml_text, project_name=project_name)

    def import_text(self, yaml_text: str, project_name: str = "imported") -> tuple:
        """从文本字符串导入 YAML。

        返回：
            (ProjectModel, ImportReport) 元组
        """
        report = ImportReport()

        try:
            data = yaml.safe_load(yaml_text)
        except yaml.YAMLError as e:
            report.unmapped_count = 1
            report.unmapped_items.append(f"YAML 解析失败: {e}")
            return None, report

        if not isinstance(data, dict):
            report.unmapped_count = 1
            report.unmapped_items.append("YAML 内容不是字典结构")
            return None, report

        # 1. 识别节点
        nodes = self._import_nodes(data, report)

        # 2. 提取插件（通用方式）
        plugins, plugin_keys_per_node, imported_categories = self._import_plugins(data, report)

        # 3. 提取非插件参数
        params = self._import_params(data, plugin_keys_per_node, report, nodes)

        # 4. 提取代价地图层和参数
        self._import_costmap_plugins(data, plugins, imported_categories, report)
        self._import_costmap_params(data, plugins, params, plugin_keys_per_node, report)

        # 5. 清理：导入的 YAML 中不存在的插件类别设为 None
        for cat in ("planner", "controller", "smoother"):
            if cat not in imported_categories:
                plugins[cat] = None
        for cat in ("global_costmap_layers", "local_costmap_layers"):
            if cat not in imported_categories:
                plugins[cat] = None
        if "recovery_behaviors" not in imported_categories:
            plugins["recovery_behaviors"] = None

        # 5. 提取 BT 树路径
        bt_tree = self._extract_bt_tree(params)

        # 6. 传感器推断
        sensors = self._infer_sensors(plugins)

        model = ProjectModel(
            project_name=project_name,
            nodes=nodes,
            plugins=plugins,
            bt_tree=bt_tree,
            params=params,
            wizard=WizardConfig(sensors=sensors),
        )
        return model, report

    def _import_nodes(self, data: dict, report: ImportReport) -> dict:
        """从 YAML 顶层键识别节点并标记启用状态。

        已知节点使用默认类型，未知节点（如 collision_monitor, docking_server）
        自动识别为 optional 类型。
        """
        nodes = ProjectModel._default_nodes()
        for key in data:
            if key in self.NON_NODE_KEYS:
                continue
            # 判断是否为节点：包含 ros__parameters 或为已知节点
            node_data = data[key]
            has_ros_params = (
                isinstance(node_data, dict) and "ros__parameters" in node_data
            )
            if key in self.KNOWN_NODES:
                if key not in nodes:
                    nodes[key] = {"enabled": True, "node_type": "optional"}
                else:
                    nodes[key]["enabled"] = True
                report.mapped_count += 1
                report.mapped_items.append(f"节点: {key}")
            elif has_ros_params:
                # 未知节点（如 collision_monitor, docking_server）自动识别
                nodes[key] = {"enabled": True, "node_type": "optional"}
                report.mapped_count += 1
                report.mapped_items.append(f"节点(自动): {key}")
        return nodes

    def _import_plugins(self, data: dict, report: ImportReport) -> tuple:
        """从各节点中通用提取插件声明。

        返回：
            (plugins_dict, plugin_keys_per_node, imported_categories) 元组
            plugin_keys_per_node: {node_name: set_of_keys_to_exclude_from_params}
            imported_categories: 实际在 YAML 中找到的插件类别集合
        """
        plugins = ProjectModel._default_plugins()
        plugin_keys_per_node = {}
        imported_categories = set()

        for (node_name, list_key), model_key in self.PLUGIN_LIST_MAP.items():
            node_data = data.get(node_name, {})
            node_params = _get_ros_params(node_data)
            if not node_params:
                continue

            plugin_list = node_params.get(list_key, [])
            if not isinstance(plugin_list, list):
                continue

            exclude_keys = {list_key}
            is_multi = model_key == "recovery_behaviors"

            if is_multi:
                items = []
                for inst_name in plugin_list:
                    inst_data = node_params.get(inst_name, {})
                    if not isinstance(inst_data, dict):
                        items.append({
                            "instance_name": inst_name,
                            "plugin_type": "",
                            "params": {},
                        })
                        exclude_keys.add(inst_name)
                        continue
                    ptype = inst_data.get("plugin", "")
                    inst_params = {k: v for k, v in inst_data.items() if k != "plugin"}
                    items.append({
                        "instance_name": inst_name,
                        "plugin_type": ptype,
                        "params": inst_params,
                        "_list_key": list_key,
                    })
                    exclude_keys.add(inst_name)
                    report.mapped_count += 1
                    report.mapped_items.append(f"Recovery: {ptype} ({inst_name})")
                if items:
                    plugins[model_key] = items
                    imported_categories.add(model_key)
            else:
                # 单选：取第一个
                for inst_name in plugin_list:
                    inst_data = node_params.get(inst_name, {})
                    if isinstance(inst_data, dict):
                        ptype = inst_data.get("plugin", "")
                        inst_params = {k: v for k, v in inst_data.items() if k != "plugin"}
                        plugins[model_key] = {
                            "instance_name": inst_name,
                            "plugin_type": ptype,
                            "params": inst_params,
                            "_list_key": list_key,
                        }
                        exclude_keys.add(inst_name)
                        imported_categories.add(model_key)
                        report.mapped_count += 1
                        report.mapped_items.append(
                            f"{model_key}: {ptype} ({inst_name})"
                        )
                    break  # 单选只取第一个

            # 主插件列表键已在 exclude_keys 中（模板会硬编码输出）。
            # 其他 *_plugins 列表键（如 progress_checker_plugins）不排除，
            # 它们及其声明的子插件实例将作为普通参数保留，确保 round-trip 一致。

            plugin_keys_per_node[node_name] = exclude_keys

        return plugins, plugin_keys_per_node, imported_categories

    def _import_costmap_plugins(
        self, data: dict, plugins: dict, imported_categories: set, report: ImportReport,
    ):
        """从代价地图配置中提取层列表。"""
        for cm_key, model_key in [
            ("global_costmap", "global_costmap_layers"),
            ("local_costmap", "local_costmap_layers"),
        ]:
            cm_data = data.get(cm_key, {})
            inner = cm_data.get(cm_key, {})
            cm_params = _get_ros_params(inner) if isinstance(inner, dict) else _get_ros_params(cm_data)
            if not cm_params:
                continue

            layer_names = cm_params.get("plugins", [])
            if not isinstance(layer_names, list):
                continue

            items = []
            for lname in layer_names:
                layer_data = cm_params.get(lname, {})
                if isinstance(layer_data, dict):
                    ptype = layer_data.get("plugin", "")
                    layer_params = {k: v for k, v in layer_data.items() if k != "plugin"}
                    items.append({
                        "instance_name": lname,
                        "plugin_type": ptype,
                        "params": layer_params,
                    })
                    report.mapped_count += 1
                    report.mapped_items.append(f"代价地图层({cm_key}): {ptype} ({lname})")
                else:
                    items.append({
                        "instance_name": lname,
                        "plugin_type": "",
                        "params": {},
                    })

            if items:
                plugins[model_key] = items
                imported_categories.add(model_key)

    def _import_costmap_params(
        self, data: dict, plugins: dict, params: dict,
        plugin_keys_per_node: dict, report: ImportReport,
    ):
        """提取代价地图的非层参数。"""
        for cm_key in ("global_costmap", "local_costmap"):
            cm_data = data.get(cm_key, {})
            inner = cm_data.get(cm_key, {})
            cm_params = _get_ros_params(inner) if isinstance(inner, dict) else _get_ros_params(cm_data)
            if not cm_params:
                continue

            # 排除 plugins 列表键和各层实例名
            exclude = {"plugins"}
            layer_names = cm_params.get("plugins", [])
            if isinstance(layer_names, list):
                exclude.update(layer_names)

            extra = {}
            for key, value in cm_params.items():
                if key not in exclude:
                    extra[key] = value

            if extra:
                params[cm_key] = extra
                report.mapped_count += len(extra)
                for k in extra:
                    report.mapped_items.append(f"参数: {cm_key}.{k}")

    def _import_params(
        self, data: dict, plugin_keys_per_node: dict, report: ImportReport,
        nodes: dict,
    ) -> dict:
        """提取各节点 ros__parameters 中的非插件参数。"""
        params = {}

        for node_name in nodes:
            if node_name not in data:
                continue
            if node_name in self.NON_NODE_KEYS:
                continue
            node_params = _get_ros_params(data[node_name])
            if not node_params:
                continue

            exclude_keys = plugin_keys_per_node.get(node_name, set())
            extra = {}
            for key, value in node_params.items():
                if key in exclude_keys:
                    continue
                extra[key] = value

            if extra:
                params[node_name] = extra
                report.mapped_count += len(extra)
                for k in extra:
                    report.mapped_items.append(f"参数: {node_name}.{k}")

        return params

    def _extract_bt_tree(self, params: dict) -> str:
        """从 bt_navigator 参数中提取 BT 树文件名。"""
        bt_params = params.get("bt_navigator", {})
        bt_xml = bt_params.get("default_bt_xml_filename", "")
        if bt_xml:
            return os.path.basename(str(bt_xml))
        return "navigate_to_pose_w_replanning_and_recovery.xml"

    def _infer_sensors(self, plugins: dict) -> SensorConfig:
        """从代价地图层配置推断传感器设置。"""
        sensors = SensorConfig()

        for layer_list_key in ("global_costmap_layers", "local_costmap_layers"):
            for layer in (plugins.get(layer_list_key) or []):
                ptype = layer.get("plugin_type", "")
                if "Voxel" in ptype:
                    sensors.depth_camera_enabled = True
                    sensors.depth_camera_pointcloud = "/camera/depth/points"
                if "Obstacle" in ptype:
                    # 从层参数中推断 lidar 话题
                    for k, v in layer.get("params", {}).items():
                        if "topic" in k.lower() and isinstance(v, str) and "scan" in v:
                            sensors.lidar_topic = v

        return sensors


def _get_ros_params(node_data: dict) -> dict:
    """从节点数据中提取 ros__parameters 字典。"""
    if not isinstance(node_data, dict):
        return {}
    params = node_data.get("ros__parameters", {})
    return params if isinstance(params, dict) else {}
