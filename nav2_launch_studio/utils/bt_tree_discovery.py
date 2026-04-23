"""BT 树发现 - 扫描 Nav2 安装获取可用的 BT 模板。"""

import os
import subprocess
from typing import Optional


class BTTreeDiscovery:
    """从 Nav2 安装中发现可用的 BT 树 XML 模板。

    对应 PRD 3.6：动态扫描 nav2_bt_navigator/behavior_trees/ 目录。
    """

    def __init__(self):
        self._template_dir: Optional[str] = None

    def discover_template_dir(self) -> Optional[str]:
        """查找 Nav2 BT 树模板目录。

        使用 `ros2 pkg prefix nav2_bt_navigator` 定位安装路径。
        """
        try:
            result = subprocess.run(
                ["ros2", "pkg", "prefix", "nav2_bt_navigator"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                prefix = result.stdout.strip()
                bt_dir = os.path.join(
                    prefix, "share", "nav2_bt_navigator", "behavior_trees"
                )
                if os.path.isdir(bt_dir):
                    self._template_dir = bt_dir
                    return bt_dir
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def list_templates(self) -> list:
        """列出可用的 BT 树模板文件名。

        返回：
            模板目录中找到的 .xml 文件名列表
        """
        if not self._template_dir:
            self.discover_template_dir()

        if not self._template_dir or not os.path.isdir(self._template_dir):
            return []

        return sorted([
            f for f in os.listdir(self._template_dir)
            if f.endswith(".xml")
        ])

    def get_template_path(self, filename: str) -> Optional[str]:
        """获取 BT 树模板文件的完整路径。"""
        if not self._template_dir:
            self.discover_template_dir()

        if self._template_dir:
            path = os.path.join(self._template_dir, filename)
            if os.path.isfile(path):
                return path
        return None

    def check_groot2_available(self) -> bool:
        """检测系统中是否安装了 Groot2。"""
        try:
            result = subprocess.run(
                ["which", "groot2"],
                capture_output=True, text=True, timeout=3,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
