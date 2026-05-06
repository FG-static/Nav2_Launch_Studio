"""项目数据模型 - Nav2 Launch Studio 项目的数据结构。"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SensorConfig:
    """传感器配置（向导第 3 步）。"""
    lidar_enabled: bool = False
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
class ProjectModel:
    """完整项目数据模型，对应 .nav2studio.json。

    plugins 结构（v1.4+）：
    - 单选插件: {"instance_name": str, "plugin_type": str, "params": {}}
    - 多选插件: [{"instance_name": str, "plugin_type": str, "params": {}}, ...]
    所有插件统一存储，不区分内置/自定义，初始 params 为空。
    """
    version: str = "1.4"
    project_name: str = ""
    ros2_version: str = "jazzy"
    robot_type: str = "diff_drive"  # "diff_drive" | "omni" | "ackermann"
    namespace: str = ""
    created_at: str = ""
    updated_at: str = ""
    wizard: WizardConfig = field(default_factory=WizardConfig)
    nodes: dict = field(default_factory=dict)
    plugins: dict = field(default_factory=dict)
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
        """默认插件配置（零参数，所有 params 为空字典）。"""
        return {
            "planner": {
                "instance_name": "GridBased",
                "plugin_type": "nav2_navfn_planner/NavfnPlanner",
                "params": {},
            },
            "controller": {
                "instance_name": "FollowPath",
                "plugin_type": "dwb_core::DWBLocalPlanner",
                "params": {},
            },
            "smoother": {
                "instance_name": "simple_smoother",
                "plugin_type": "nav2_smoother::SimpleSmoother",
                "params": {},
            },
            "global_costmap_layers": [
                {"instance_name": "static_layer", "plugin_type": "nav2_costmap_2d::StaticLayer", "params": {}},
                {"instance_name": "obstacle_layer", "plugin_type": "nav2_costmap_2d::ObstacleLayer", "params": {}},
                {"instance_name": "inflation_layer", "plugin_type": "nav2_costmap_2d::InflationLayer", "params": {}},
            ],
            "local_costmap_layers": [
                {"instance_name": "obstacle_layer", "plugin_type": "nav2_costmap_2d::ObstacleLayer", "params": {}},
                {"instance_name": "inflation_layer", "plugin_type": "nav2_costmap_2d::InflationLayer", "params": {}},
            ],
            "recovery_behaviors": [
                {"instance_name": "spin", "plugin_type": "nav2_behaviors::Spin", "params": {}},
                {"instance_name": "backup", "plugin_type": "nav2_behaviors::BackUp", "params": {}},
                {"instance_name": "wait", "plugin_type": "nav2_behaviors::Wait", "params": {}},
            ],
        }

    def to_dict(self):
        """序列化为符合 .nav2studio.json 格式的字典。"""
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
                    "lidar_enabled": self.wizard.sensors.lidar_enabled,
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
            "bt_tree": self.bt_tree,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data):
        """从 .nav2studio.json 字典反序列化。"""
        wizard_data = data.get("wizard", {})
        sensors_data = wizard_data.get("sensors", {})

        sensors = SensorConfig(
            lidar_enabled=sensors_data.get("lidar_enabled", False),
            lidar_topic=sensors_data.get("lidar_topic", "/scan"),
            lidar_frame=sensors_data.get("lidar_frame", "laser_frame"),
            depth_camera_enabled=sensors_data.get("depth_camera_enabled", False),
            depth_camera_topic=sensors_data.get("depth_camera_topic", ""),
            depth_camera_pointcloud=sensors_data.get("depth_camera_pointcloud", ""),
            depth_camera_frame=sensors_data.get("depth_camera_frame", ""),
            imu_enabled=sensors_data.get("imu_enabled", False),
            imu_topic=sensors_data.get("imu_topic", ""),
            imu_frame=sensors_data.get("imu_frame", ""),
        )

        wizard = WizardConfig(
            sensors=sensors,
            map_source=wizard_data.get("map_source", "existing"),
            map_path=wizard_data.get("map_path", ""),
        )

        plugins = data.get("plugins", None)
        if plugins is not None:
            plugins = cls._migrate_plugins(plugins)

        return cls(
            version=data.get("version", "1.4"),
            project_name=data.get("project_name", ""),
            ros2_version=data.get("ros2_version", "jazzy"),
            robot_type=data.get("robot_type", "diff_drive"),
            namespace=data.get("namespace", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            wizard=wizard,
            nodes=data.get("nodes", None) or None,
            plugins=plugins,
            bt_tree=data.get("bt_tree", "navigate_to_pose_w_replanning_and_recovery.xml"),
            params=data.get("params", {}),
        )

    @staticmethod
    def _migrate_plugins(plugins):
        """将旧格式（v1.3 ID-based）插件配置转换为新格式（v1.4 detail-based）。

        旧格式: {"global_planner": "navfn", "local_planner": "dwb", ...}
        新格式: {"planner": {"instance_name": ..., "plugin_type": ..., "params": {}}, ...}
        """
        # 检测旧格式：单选插件的值是字符串
        has_old_format = any(isinstance(v, str) for v in plugins.values())
        if not has_old_format:
            return plugins

        from nav2_launch_studio.core.plugin_registry import PluginRegistry
        new_plugins = {}

        # 单选插件迁移
        for old_key, new_key, registry, default_inst in [
            ("global_planner", "planner", PluginRegistry.BUILTIN_PLANNERS, "GridBased"),
            ("local_planner", "controller", PluginRegistry.BUILTIN_CONTROLLERS, "FollowPath"),
            ("path_smoother", "smoother", PluginRegistry.BUILTIN_SMOOTHERS, "simple_smoother"),
        ]:
            pid = plugins.get(old_key, "")
            entry = registry.get(pid, {})
            if entry:
                new_plugins[new_key] = {
                    "instance_name": entry.get("instance_name", default_inst),
                    "plugin_type": entry["plugin_type"],
                    "params": {},
                }
            elif pid:
                # 自定义插件：pid 即 plugin_type
                new_plugins[new_key] = {
                    "instance_name": default_inst,
                    "plugin_type": pid,
                    "params": {},
                }

        # 多选插件迁移
        for old_key, registry, suffix in [
            ("global_costmap_layers", PluginRegistry.BUILTIN_COSTMAP_LAYERS, "_layer"),
            ("local_costmap_layers", PluginRegistry.BUILTIN_COSTMAP_LAYERS, "_layer"),
            ("recovery_behaviors", PluginRegistry.BUILTIN_RECOVERIES, ""),
        ]:
            ids = plugins.get(old_key, [])
            items = []
            for pid in ids:
                if isinstance(pid, dict):
                    items.append(pid)
                    continue
                entry = registry.get(pid, {})
                if entry:
                    inst_name = pid + suffix if suffix else pid
                    items.append({
                        "instance_name": inst_name,
                        "plugin_type": entry["plugin_type"],
                        "params": {},
                    })
                else:
                    items.append({
                        "instance_name": pid,
                        "plugin_type": pid,
                        "params": {},
                    })
            new_plugins[old_key] = items

        return new_plugins

    def touch(self):
        """更新 updated_at 时间戳。"""
        self.updated_at = datetime.now().isoformat()
