"""项目向导 - 分步引导创建新的 Nav2 配置。"""

from PySide6.QtWidgets import (
    QWizard, QWizardPage, QFormLayout,
    QLineEdit, QComboBox, QRadioButton, QButtonGroup,
    QCheckBox, QLabel, QFileDialog, QPushButton,
)

from nav2_launch_studio.core.project_model import ProjectModel, SensorConfig, WizardConfig


class ProjectWizard(QWizard):
    """新建项目的多步向导。

    步骤（对应 PRD 3.2）：
    1. 基本信息：项目名称、ROS2 版本、工作空间、命名空间
    2. 机器人类型：差速 / 全向 / 阿克曼
    3. 传感器配置：激光雷达、深度相机、IMU 话题与坐标系
    4. 地图来源：已有地图 / SLAM / 无地图
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建项目向导")
        self.addPage(BasicInfoPage())
        self.addPage(RobotTypePage())
        self.addPage(SensorConfigPage())
        self.addPage(MapSourcePage())

    def to_project_model(self) -> ProjectModel:
        """将向导收集的数据转换为 ProjectModel。"""
        sensors = SensorConfig(
            lidar_topic=self.field("lidar_topic") or "/scan",
            lidar_frame=self.field("lidar_frame") or "laser_frame",
            depth_camera_enabled=bool(self.field("depth_enabled")),
            depth_camera_topic=self.field("depth_camera_topic") or "",
            depth_camera_pointcloud=self.field("depth_camera_pointcloud") or "",
            depth_camera_frame=self.field("depth_camera_frame") or "",
            imu_enabled=bool(self.field("imu_enabled")),
            imu_topic=self.field("imu_topic") or "",
            imu_frame=self.field("imu_frame") or "",
        )

        wizard = WizardConfig(
            sensors=sensors,
            map_source=self.field("map_source") or "existing",
            map_path=self.field("map_path") or "",
        )

        return ProjectModel(
            project_name=self.field("project_name") or "",
            ros2_version=self.field("ros_version") or "jazzy",
            robot_type=self.field("robot_type") or "diff_drive",
            namespace=self.field("namespace") or "",
            wizard=wizard,
        )


class BasicInfoPage(QWizardPage):
    """第 1 步：基本信息。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("基本信息")
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.ros_version_combo = QComboBox()
        self.ros_version_combo.addItems(["jazzy", "foxy", "humble"])
        self.workspace_edit = QLineEdit()
        self.workspace_browse_btn = QPushButton("浏览...")
        self.namespace_edit = QLineEdit()
        self.namespace_edit.setPlaceholderText("可选，如 /robot1")

        layout.addRow("项目名称：", self.name_edit)
        layout.addRow("ROS2 版本：", self.ros_version_combo)
        layout.addRow("工作空间：", self.workspace_edit)
        layout.addRow("命名空间：", self.namespace_edit)

        self.registerField("project_name*", self.name_edit)
        self.registerField("ros_version", self.ros_version_combo)
        self.registerField("workspace", self.workspace_edit)
        self.registerField("namespace", self.namespace_edit)


class RobotTypePage(QWizardPage):
    """第 2 步：机器人运动学类型选择。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("机器人类型")
        layout = QFormLayout(self)

        self.btn_group = QButtonGroup(self)
        self.diff_drive_radio = QRadioButton("差速驱动 (DiffDrive)")
        self.omni_radio = QRadioButton("全向轮/麦轮 (Omni)")
        self.ackermann_radio = QRadioButton("阿克曼转向 (Ackermann)")

        self.btn_group.addButton(self.diff_drive_radio, 0)
        self.btn_group.addButton(self.omni_radio, 1)
        self.btn_group.addButton(self.ackermann_radio, 2)
        self.diff_drive_radio.setChecked(True)

        layout.addRow(self.diff_drive_radio)
        layout.addRow(QLabel("  TurtleBot3、轮椅机器人"))
        layout.addRow(self.omni_radio)
        layout.addRow(QLabel("  仓储AGV、竞赛机器人"))
        layout.addRow(self.ackermann_radio)
        layout.addRow(QLabel("  无人车、叉车"))

        self.registerField("robot_type", self, "robotType")

    @property
    def robotType(self):
        mapping = {0: "diff_drive", 1: "omni", 2: "ackermann"}
        return mapping.get(self.btn_group.checkedId(), "diff_drive")


class SensorConfigPage(QWizardPage):
    """第 3 步：传感器配置。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("传感器配置")
        layout = QFormLayout(self)

        # 激光雷达
        self.lidar_topic_edit = QLineEdit("/scan")
        self.lidar_frame_edit = QLineEdit("laser_frame")
        layout.addRow("激光雷达话题：", self.lidar_topic_edit)
        layout.addRow("激光雷达坐标系：", self.lidar_frame_edit)

        # 深度相机（可选）
        self.depth_enabled = QCheckBox("启用深度相机")
        self.depth_topic_edit = QLineEdit()
        self.depth_pointcloud_edit = QLineEdit()
        self.depth_frame_edit = QLineEdit()
        layout.addRow(self.depth_enabled)
        layout.addRow("深度相机话题：", self.depth_topic_edit)
        layout.addRow("点云话题：", self.depth_pointcloud_edit)
        layout.addRow("深度相机坐标系：", self.depth_frame_edit)

        # IMU（可选）
        self.imu_enabled = QCheckBox("启用 IMU")
        self.imu_topic_edit = QLineEdit()
        self.imu_frame_edit = QLineEdit()
        layout.addRow(self.imu_enabled)
        layout.addRow("IMU 话题：", self.imu_topic_edit)
        layout.addRow("IMU 坐标系：", self.imu_frame_edit)

        self.registerField("lidar_topic", self.lidar_topic_edit)
        self.registerField("lidar_frame", self.lidar_frame_edit)
        self.registerField("depth_enabled", self.depth_enabled)
        self.registerField("depth_camera_topic", self.depth_topic_edit)
        self.registerField("depth_camera_pointcloud", self.depth_pointcloud_edit)
        self.registerField("depth_camera_frame", self.depth_frame_edit)
        self.registerField("imu_enabled", self.imu_enabled)
        self.registerField("imu_topic", self.imu_topic_edit)
        self.registerField("imu_frame", self.imu_frame_edit)


class MapSourcePage(QWizardPage):
    """第 4 步：地图来源选择。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("地图来源")
        layout = QFormLayout(self)

        self.btn_group = QButtonGroup(self)
        self.existing_map_radio = QRadioButton("加载已有地图")
        self.slam_radio = QRadioButton("实时 SLAM 建图")
        self.no_map_radio = QRadioButton("无地图模式")

        self.btn_group.addButton(self.existing_map_radio, 0)
        self.btn_group.addButton(self.slam_radio, 1)
        self.btn_group.addButton(self.no_map_radio, 2)
        self.existing_map_radio.setChecked(True)

        layout.addRow(self.existing_map_radio)
        self.map_path_edit = QLineEdit()
        self.map_browse_btn = QPushButton("浏览...")
        layout.addRow("地图文件：", self.map_path_edit)

        layout.addRow(self.slam_radio)
        layout.addRow(self.no_map_radio)

        self.registerField("map_source", self, "mapSource")
        self.registerField("map_path", self.map_path_edit)

    @property
    def mapSource(self):
        mapping = {0: "existing", 1: "slam", 2: "no_map"}
        return mapping.get(self.btn_group.checkedId(), "existing")
