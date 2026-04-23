"""YAML 生成器 - 从项目模型生成 nav2_params.yaml。"""

from typing import Optional


class YamlGenerator:
    """从项目配置生成 nav2_params.yaml。

    对应 PRD 3.7：
    - 使用 Jinja2 模板生成 YAML
    - 根据以下内容生成：选中的插件、节点参数、代价地图层、BT 树
    - 支持实时预览
    """

    def __init__(self, template_dir: Optional[str] = None):
        self.template_dir = template_dir

    def generate(self, project_model) -> str:
        """从项目模型生成 nav2_params.yaml 内容。

        参数：
            project_model: 包含完整配置的 ProjectModel 实例

        返回：
            YAML 字符串内容
        """
        # TODO: 使用 Jinja2 模板渲染 YAML
        # - 收集所有启用节点及其参数
        # - 插入插件声明
        # - 插入代价地图层配置（全局/局部分开）
        # - 插入 BT 树路径
        # - 插入自定义插件参数为键值对段落
        # - 添加描述性注释
        return "# nav2_params.yaml - 由 Nav2 Launch Studio 生成\n"

    def generate_preview(self, project_model) -> str:
        """生成轻量级预览（可能跳过注释以提升速度）。"""
        # TODO: 优化实时预览性能
        return self.generate(project_model)
