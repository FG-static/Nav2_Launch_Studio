"""项目数据模型 - Nav2 Launch Studio 项目的数据结构。"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SensorConfig:
    """传感器配置（向导第 3 步）。"""
    lidar_topic: str = "/scan"
    lidar_frame: str = "laser_frame"
    depth_camera_enabled: bool = False
    depth_camera_topic: str = ""
    depth_camera_pointcloud: str = ""
    depth_camera_frame: str = ""
    imu_enabled: bool = False
    imu_topic: str = ""
    imu_frame: str = ""


@dataclass
class WizardConfig:
    """向导收集的全部配置。"""
    sensors: SensorConfig = field(default_factory=SensorConfig)
    map_source: str = "existing"  # "existing" | "slam" | "no_map"
    map_path: str = ""


@dataclass
class NodeConfig:
    """单个节点的配置状态。"""
    enabled: bool = True
    node_type: str = "optional"  # "mandatory" | "recommended" | "optional"


@dataclass
class CustomPlugin:
    """用户注册的自定义插件。"""
    display_name: str = ""
    plugin_type: str = ""
    instance_name: str = ""
    category: str = ""
    params: list = field(default_factory=list)
    description: str = ""


@dataclass
class ProjectModel:
    """完整项目数据模型，对应 .nav2studio.json。

    对应 PRD 3.8.1。
    """
    version: str = "1.3"
    project_name: str = ""
    ros2_version: str = "jazzy"
    robot_type: str = "diff_drive"  # "diff_drive" | "omni" | "ackermann"
    namespace: str = ""
    created_at: str = ""
    updated_at: str = ""
    wizard: WizardConfig = field(default_factory=WizardConfig)
    nodes: dict = field(default_factory=dict)
    plugins: dict = field(default_factory=dict)
    custom_plugins: list = field(default_factory=list)
    bt_tree: str = "navigate_to_pose_w_replanning_and_recovery.xml"
    params: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.nodes:
            self.nodes = self._default_nodes()
        if not self.plugins:
            self.plugins = self._default_plugins()

    @staticmethod
    def _default_nodes():
        """默认节点配置。"""
        return {
            "bt_navigator": {"enabled": True, "node_type": "mandatory"},
            "controller_server": {"enabled": True, "node_type": "mandatory"},
            "planner_server": {"enabled": True, "node_type": "mandatory"},
            "behavior_server": {"enabled": True, "node_type": "recommended"},
            "amcl": {"enabled": True, "node_type": "recommended"},
            "map_server": {"enabled": True, "node_type": "recommended"},
            "lifecycle_manager": {"enabled": True, "node_type": "recommended"},
            "velocity_smoother": {"enabled": False, "node_type": "optional"},
            "waypoint_follower": {"enabled": False, "node_type": "optional"},
        }

    @staticmethod
    def _default_plugins():
        """默认插件配置。"""
        return {
            "global_planner": "navfn",
            "local_planner": "dwb",
            "path_smoother": "simple",
            "global_costmap_layers": ["static", "obstacle", "inflation"],
            "local_costmap_layers": ["obstacle", "inflation"],
            "recovery_behaviors": ["spin", "backup", "wait"],
        }

    def to_dict(self):
        """序列化为符合 .nav2studio.json 格式的字典。"""
        # TODO: 完整序列化
        return {
            "version": self.version,
            "project_name": self.project_name,
            "ros2_version": self.ros2_version,
            "robot_type": self.robot_type,
            "namespace": self.namespace,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "wizard": {
                "sensors": {
                    "lidar_topic": self.wizard.sensors.lidar_topic,
                    "lidar_frame": self.wizard.sensors.lidar_frame,
                    "depth_camera_topic": self.wizard.sensors.depth_camera_topic,
                    "depth_camera_pointcloud": self.wizard.sensors.depth_camera_pointcloud,
                    "depth_camera_frame": self.wizard.sensors.depth_camera_frame,
                    "imu_topic": self.wizard.sensors.imu_topic,
                    "imu_frame": self.wizard.sensors.imu_frame,
                },
                "map_source": self.wizard.map_source,
                "map_path": self.wizard.map_path,
            },
            "nodes": self.nodes,
            "plugins": self.plugins,
            "custom_plugins": self.custom_plugins,
            "bt_tree": self.bt_tree,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data):
        """从 .nav2studio.json 字典反序列化。"""
        # TODO: 完整反序列化及版本迁移
        pass

    def touch(self):
        """更新 updated_at 时间戳。"""
        self.updated_at = datetime.now().isoformat()
