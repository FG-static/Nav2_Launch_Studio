"""模版管理器 - 项目内参数模版的保存、加载和删除。"""

import json
import os
from datetime import datetime
from typing import Optional


class TemplateManager:
    """管理项目内的参数模版。

    模版存储在项目目录下的 templates/ 子目录中，每个模版一个 JSON 文件。
    模版仅供当前项目使用，切换项目后不可见。
    """

    TEMPLATES_DIR = "templates"

    def __init__(self, project_dir: str):
        """初始化模版管理器。

        Args:
            project_dir: 项目根目录路径。
        """
        self._project_dir = project_dir
        self._templates_dir = os.path.join(project_dir, self.TEMPLATES_DIR)
        os.makedirs(self._templates_dir, exist_ok=True)

    @property
    def templates_dir(self) -> str:
        """返回模版目录路径。"""
        return self._templates_dir

    def save_template(self, name: str, node_name: str, params: dict) -> str:
        """保存当前参数为模版。

        Args:
            name: 模版名称（用于文件名，会自动清理非法字符）。
            node_name: 来源节点名。
            params: 节点的完整参数字典。

        Returns:
            保存后的模版文件绝对路径。

        Raises:
            ValueError: 名称为空时抛出。
        """
        name = name.strip()
        if not name:
            raise ValueError("模版名称不能为空")

        # 清理文件名中的非法字符
        safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
        safe_name = safe_name.strip().replace(" ", "_")
        if not safe_name:
            safe_name = "template"

        filename = f"{safe_name}.json"
        filepath = os.path.join(self._templates_dir, filename)

        # 同名文件覆盖保存
        template_data = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "node_name": node_name,
            "params": params,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)

        return filepath

    def list_templates(self) -> list[dict]:
        """列出项目内所有模版。

        Returns:
            模版信息列表，按名称排序。每个元素包含 name, file, node_name, created_at。
        """
        templates = []
        if not os.path.isdir(self._templates_dir):
            return templates

        for filename in sorted(os.listdir(self._templates_dir)):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(self._templates_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                templates.append({
                    "name": data.get("name", filename),
                    "file": filepath,
                    "node_name": data.get("node_name", ""),
                    "created_at": data.get("created_at", ""),
                })
            except (json.JSONDecodeError, OSError):
                continue

        return templates

    def load_template(self, filepath: str) -> dict:
        """加载指定模版文件。

        Args:
            filepath: 模版文件路径。

        Returns:
            包含 name, node_name, params 的字典。

        Raises:
            FileNotFoundError: 文件不存在时抛出。
            ValueError: 文件格式错误时抛出。
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"模版文件不存在: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"模版文件格式错误: {e}") from e

        if "params" not in data:
            raise ValueError("模版文件缺少 params 字段")

        return {
            "name": data.get("name", os.path.basename(filepath)),
            "node_name": data.get("node_name", ""),
            "params": data["params"],
        }

    def delete_template(self, filepath: str):
        """删除指定模版文件。

        Args:
            filepath: 模版文件路径。

        Raises:
            FileNotFoundError: 文件不存在时抛出。
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"模版文件不存在: {filepath}")
        os.remove(filepath)
