"""项目持久化 - 保存、加载、迁移 .nav2studio.json 项目。"""

import json
import os
import shutil
from pathlib import Path
from typing import Optional

from nav2_launch_studio.core.project_model import ProjectModel


# 版本迁移注册表
MIGRATIONS = {
    # "1.2": migrate_v12_to_v13,
}


class ProjectManager:
    """管理项目持久化：保存、加载、导入、导出。

    对应 PRD 3.8：
    - 项目目录结构含 .nav2studio.json
    - 自动保存支持
    - 加载时执行版本迁移
    - 从 nav2_params.yaml 导入
    """

    PROJECT_FILE = ".nav2studio.json"

    def __init__(self):
        self.current_project: Optional[ProjectModel] = None
        self.project_dir: Optional[str] = None

    def new_project(self, project_model: ProjectModel, base_dir: str) -> str:
        """创建新项目目录并保存初始状态。

        参数：
            project_model: 从向导填充的 ProjectModel
            base_dir: 项目文件夹的父目录

        返回：
            创建的项目目录路径
        """
        project_dir = os.path.join(base_dir, project_model.project_name)
        os.makedirs(os.path.join(project_dir, "config"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "behavior_trees"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "maps"), exist_ok=True)

        self.current_project = project_model
        self.project_dir = project_dir
        self.save()
        return project_dir

    def save(self):
        """保存当前项目到 .nav2studio.json。"""
        if not self.current_project or not self.project_dir:
            return

        self.current_project.touch()
        path = os.path.join(self.project_dir, self.PROJECT_FILE)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.current_project.to_dict(), f, indent=2, ensure_ascii=False)

    def save_as(self, new_dir: str):
        """将项目另存到新目录。"""
        # TODO: 复制项目到新位置
        pass

    def load(self, project_dir: str) -> ProjectModel:
        """从包含 .nav2studio.json 的目录加载项目。

        需要时执行版本迁移。
        """
        path = os.path.join(project_dir, self.PROJECT_FILE)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 执行版本迁移
        data = self._migrate(data)

        self.current_project = ProjectModel.from_dict(data)
        self.project_dir = project_dir
        return self.current_project

    def export_yaml(self, output_path: str):
        """导出 nav2_params.yaml 到指定路径。

        参数：
            output_path: YAML 文件的目标路径
        """
        # TODO: 调用 YamlGenerator 生成 YAML，写入文件
        pass

    def list_recent_projects(self, base_dir: str, limit=10):
        """列出按 updated_at 排序的最近项目。

        参数：
            base_dir: 扫描项目的目录
            limit: 最大返回数量

        返回：
            (项目名, 项目目录, 更新时间) 元组列表
        """
        # TODO: 扫描含 .nav2studio.json 的目录，按 updated_at 排序
        return []

    def _migrate(self, data: dict) -> dict:
        """对项目数据执行版本迁移。"""
        version = data.get("version", "1.3")
        while version in MIGRATIONS:
            data = MIGRATIONS[version](data)
            version = data.get("version", "1.3")
        return data

    @staticmethod
    def delete_project(project_dir: str):
        """删除项目目录。"""
        shutil.rmtree(project_dir)

    @staticmethod
    def export_zip(project_dir: str, output_path: str):
        """将项目导出为 .zip 用于分享。"""
        # TODO: shutil.make_archive
        pass
