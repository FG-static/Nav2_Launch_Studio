"""插件注册表 - 管理内置和自定义 Nav2 插件元数据。"""

from typing import Optional


class PluginRegistry:
    """所有可用 Nav2 插件的注册表，包含内置和自定义。

    管理：
    - 内置插件定义，来自 schemas/
    - 用户注册的自定义插件
    - 按分类和 ID 查找插件
    """

    # 内置插件分类及其 ID
    BUILTIN_PLANNERS = {
        "navfn": {
            "display_name": "NavFn (Dijkstra/A*)",
            "plugin_type": "nav2_navfn_planner/NavfnPlanner",
            "instance_name": "GridBased",
            "description": "经典、稳定，速度快",
        },
        "smac_2d": {
            "display_name": "Smac Planner 2D (A*)",
            "plugin_type": "nav2_smac_planner/SmacPlanner2D",
            "instance_name": "GridBased",
            "description": "纯 A*，适合简单场景",
        },
        "smac_lattice": {
            "display_name": "Smac Planner Lattice",
            "plugin_type": "nav2_smac_planner/SmacPlannerLattice",
            "instance_name": "LatticeGenerator",
            "description": "支持阿克曼，考虑运动学约束",
        },
        "smac_hybrid": {
            "display_name": "Smac Planner Hybrid-A*",
            "plugin_type": "nav2_smac_planner/SmacPlannerHybrid",
            "instance_name": "FollowPath",
            "description": "平滑路径，质量高",
        },
        "theta_star": {
            "display_name": "Theta*",
            "plugin_type": "nav2_theta_star_planner/ThetaStarPlanner",
            "instance_name": "ThetaStar",
            "description": "任意角度路径，更自然",
        },
    }

    BUILTIN_CONTROLLERS = {
        "dwb": {
            "display_name": "DWB Controller",
            "plugin_type": "dwb_core::DWBLocalPlanner",
            "instance_name": "FollowPath",
            "description": "经典DWA升级版，稳定",
        },
        "mppi": {
            "display_name": "MPPI Controller",
            "plugin_type": "nav2_mppi_controller::MPPIController",
            "instance_name": "FollowPath",
            "description": "模型预测控制，动态避障强",
        },
        "regulated_pure_pursuit": {
            "display_name": "Regulated Pure Pursuit",
            "plugin_type": "nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController",
            "instance_name": "FollowPath",
            "description": "路径追踪，适合车型机器人",
        },
        "graceful": {
            "display_name": "Graceful Controller",
            "plugin_type": "nav2_graceful_controller::GracefulController",
            "instance_name": "FollowPath",
            "description": "优雅运动控制，适合对接/停靠",
        },
    }

    BUILTIN_SMOOTHERS = {
        "simple": {
            "display_name": "SimpleSmoother",
            "plugin_type": "nav2_smoother::SimpleSmoother",
            "instance_name": "simple_smoother",
            "description": "轻量级，移除冗余点",
        },
        "savitzky_golay": {
            "display_name": "SavitzkyGolaySmoother",
            "plugin_type": "nav2_smoother::SavitzkyGolaySmoother",
            "instance_name": "smooth",
            "description": "多项式平滑，轨迹更自然",
        },
        "constrained": {
            "display_name": "ConstrainedSmoother",
            "plugin_type": "nav2_constrained_smoother::ConstrainedSmoother",
            "instance_name": "smooth",
            "description": "保持运动学可行性",
        },
    }

    BUILTIN_COSTMAP_LAYERS = {
        "static": {
            "display_name": "StaticLayer",
            "plugin_type": "nav2_costmap_2d::StaticLayer",
            "description": "静态地图层",
        },
        "obstacle": {
            "display_name": "ObstacleLayer",
            "plugin_type": "nav2_costmap_2d::ObstacleLayer",
            "description": "激光雷达障碍物",
        },
        "inflation": {
            "display_name": "InflationLayer",
            "plugin_type": "nav2_costmap_2d::InflationLayer",
            "description": "障碍物膨胀",
        },
        "voxel": {
            "display_name": "VoxelLayer",
            "plugin_type": "nav2_costmap_2d::VoxelLayer",
            "description": "3D 障碍物，支持点云",
        },
        "range": {
            "display_name": "RangeSensorLayer",
            "plugin_type": "nav2_costmap_2d::RangeSensorLayer",
            "description": "超声波传感器",
        },
    }

    BUILTIN_RECOVERIES = {
        "spin": {
            "display_name": "Spin",
            "plugin_type": "nav2_behaviors::Spin",
            "description": "原地旋转清除局部代价地图",
        },
        "backup": {
            "display_name": "BackUp",
            "plugin_type": "nav2_behaviors::BackUp",
            "description": "后退",
        },
        "drive_on_heading": {
            "display_name": "DriveOnHeading",
            "plugin_type": "nav2_behaviors::DriveOnHeading",
            "description": "沿朝向行驶",
        },
        "wait": {
            "display_name": "Wait",
            "plugin_type": "nav2_behaviors::Wait",
            "description": "等待",
        },
        "clear_costmap": {
            "display_name": "ClearCostmapService",
            "plugin_type": "nav2_behaviors::ClearCostmapService",
            "description": "清除代价地图服务",
        },
    }

    def __init__(self):
        self._custom_plugins = []

    def get_plugins_by_category(self, category: str) -> dict:
        """获取某分类的所有插件，包含内置和自定义。"""
        category_map = {
            "planner": self.BUILTIN_PLANNERS,
            "controller": self.BUILTIN_CONTROLLERS,
            "smoother": self.BUILTIN_SMOOTHERS,
            "costmap_layer": self.BUILTIN_COSTMAP_LAYERS,
            "recovery": self.BUILTIN_RECOVERIES,
        }
        builtins = dict(category_map.get(category, {}))
        # 添加该分类的自定义插件
        for cp in self._custom_plugins:
            if cp.get("category") == category:
                builtins[f"custom_{cp['instance_name']}"] = {
                    "display_name": f"🔧 {cp['display_name']}",
                    "plugin_type": cp["plugin_type"],
                    "instance_name": cp["instance_name"],
                    "description": cp.get("description", ""),
                    "is_custom": True,
                }
        return builtins

    def register_custom_plugin(self, plugin_data: dict):
        """注册一个自定义插件。"""
        self._custom_plugins.append(plugin_data)

    def remove_custom_plugin(self, instance_name: str):
        """按实例名移除自定义插件。"""
        self._custom_plugins = [
            p for p in self._custom_plugins
            if p.get("instance_name") != instance_name
        ]

    def get_custom_plugins(self) -> list:
        """返回所有自定义插件。"""
        return list(self._custom_plugins)
