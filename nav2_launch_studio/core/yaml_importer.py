"""YAML 导入器 - 解析 nav2_params.yaml 并反向映射到 UI 状态。"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ImportReport:
    """YAML 导入结果报告。"""
    mapped_count: int = 0       # 成功映射的配置项数量
    partially_mapped_count: int = 0  # 部分映射的配置项数量
    unmapped_count: int = 0     # 未映射的配置项数量
    mapped_items: list = None           # 成功映射项列表
    partially_mapped_items: list = None # 部分映射项列表
    unmapped_items: list = None         # 未映射项列表

    def __post_init__(self):
        if self.mapped_items is None:
            self.mapped_items = []
        if self.partially_mapped_items is None:
            self.partially_mapped_items = []
        if self.unmapped_items is None:
            self.unmapped_items = []


class YamlImporter:
    """解析已有的 nav2_params.yaml 并映射到项目模型。

    对应 PRD 3.8.2：
    - 尽力反向映射 YAML 到 UI 状态
    - 识别节点命名空间、插件声明、参数
    - 将内置插件参数映射到 UI 控件
    - 未映射参数归入"未识别"区域
    - 自动注册自定义插件
    - 生成导入报告
    """

    def __init__(self, schema_loader=None):
        self.schema_loader = schema_loader

    def import_file(self, yaml_path: str) -> tuple:
        """导入 nav2_params.yaml 文件。

        参数：
            yaml_path: YAML 文件路径

        返回：
            (ProjectModel, ImportReport) 元组
        """
        # TODO:
        # 1. 用 PyYAML 解析 YAML
        # 2. 识别顶层节点命名空间
        # 3. 提取插件声明
        # 4. 匹配内置插件 -> 将参数映射到 schema
        # 5. 未匹配的参数 -> Key-Value 编辑器
        # 6. 自动注册自定义插件
        # 7. 生成导入报告
        report = ImportReport()
        return None, report

    def import_text(self, yaml_text: str) -> tuple:
        """从文本字符串导入 YAML。

        返回：
            (ProjectModel, ImportReport) 元组
        """
        # TODO: 与 import_file 相同逻辑，但输入为字符串
        report = ImportReport()
        return None, report

    def _identify_node_namespaces(self, yaml_data: dict) -> list:
        """识别 YAML 数据中的 Nav2 节点命名空间。"""
        known_nodes = {
            "bt_navigator", "controller_server", "planner_server",
            "behavior_server", "amcl", "map_server",
            "velocity_smoother", "waypoint_follower",
            "lifecycle_manager",
        }
        return [k for k in yaml_data.keys() if k in known_nodes]

    def _extract_plugins(self, node_data: dict) -> list:
        """从节点的 ros__parameters 中提取插件声明。"""
        # TODO: 查找 'plugin' 字段、controller_plugins、planner_plugins 等
        return []
