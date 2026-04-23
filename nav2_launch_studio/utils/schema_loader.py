"""Schema 加载器 - 加载和管理插件参数 schema 文件。"""

import json
import os
from typing import Optional


class SchemaLoader:
    """为内置 Nav2 插件加载参数 schema JSON 文件。

    对应 PRD 附录 C：
    - schema 文件位于 schemas/ 目录，按分类组织
    - 每个文件定义参数的类型、默认值、范围、描述
    - 支持 version_overrides 处理 ROS2 版本差异
    """

    def __init__(self, schema_dir: Optional[str] = None):
        if schema_dir is None:
            # 默认使用包内的 schemas/ 目录
            schema_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "schemas"
            )
        self.schema_dir = schema_dir
        self._cache = {}

    def load_schema(self, category: str, plugin_id: str) -> Optional[dict]:
        """加载插件的参数 schema。

        参数：
            category: planner/controller/smoother/costmap_layer/recovery/node
            plugin_id: 不含扩展名的 schema 文件名（如 "mppi_controller"）

        返回：
            schema 字典，未找到则返回 None
        """
        cache_key = f"{category}/{plugin_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        path = os.path.join(self.schema_dir, category, f"{plugin_id}.json")
        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        self._cache[cache_key] = schema
        return schema

    def load_node_schema(self, node_name: str) -> Optional[dict]:
        """加载 Nav2 节点的参数 schema。

        参数：
            node_name: 如 "controller_server"、"planner_server"
        """
        return self.load_schema("nodes", node_name)

    def apply_version_overrides(self, schema: dict, ros2_version: str) -> dict:
        """将版本特定的覆盖应用到 schema。

        参数：
            schema: 基础 schema 字典
            ros2_version: 目标 ROS2 版本（humble/iron/jazzy）

        返回：
            应用了版本覆盖的 schema
        """
        if "params" not in schema:
            return schema

        result = dict(schema)
        result["params"] = dict(schema["params"])

        for param_name, param_def in schema["params"].items():
            overrides = param_def.get("version_overrides", {}).get(ros2_version)
            if overrides:
                merged = dict(param_def)
                merged.update(overrides)
                result["params"][param_name] = merged

        return result

    def list_available_schemas(self, category: str) -> list:
        """列出某分类下所有可用的 schema ID。"""
        cat_dir = os.path.join(self.schema_dir, category)
        if not os.path.isdir(cat_dir):
            return []
        return [
            os.path.splitext(f)[0]
            for f in os.listdir(cat_dir)
            if f.endswith(".json")
        ]
