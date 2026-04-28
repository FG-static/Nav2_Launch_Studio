"""主窗口 - 管理所有 UI 模块和布局。"""

import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QStatusBar, QMenuBar,
    QToolBar, QLabel, QStackedWidget, QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt

from nav2_launch_studio.core.project_manager import ProjectManager
from nav2_launch_studio.core.yaml_importer import YamlImporter
from nav2_launch_studio.ui.start_page import StartPageWidget
from nav2_launch_studio.ui.wizard.project_wizard import ProjectWizard


# 启动页 / 编辑页 在 QStackedWidget 中的索引
PAGE_START = 0
PAGE_EDITOR = 1


class MainWindow(QMainWindow):
    """Nav2 Launch Studio 主窗口。

    布局（对应 PRD 4.2）：
    - 菜单栏：文件 | 视图 | 工具 | 帮助
    - 项目信息栏：项目名 | ROS2版本 | 机器人类型
    - 中央区域：启动页 / 编辑页（QStackedWidget 切换）
    - 底部：YAML 预览 + 导出工具栏
    """

    def __init__(self):
        super().__init__()
        self._project_manager = ProjectManager()
        self._projects_base_dir = os.path.expanduser("~/nav2_studio_projects")
        self.setWindowTitle("Nav2 Launch Studio")
        self.resize(1280, 800)
        self._init_ui()

    def _init_ui(self):
        # 菜单栏
        self._create_menu_bar()

        # 项目信息栏
        self._create_project_info_bar()

        # 中央堆叠部件：启动页 + 编辑页
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        # --- 启动页 ---
        self._start_page = StartPageWidget()
        self._start_page.new_project_requested.connect(self._on_new_project)
        self._start_page.open_project_requested.connect(self._open_project)
        self._start_page.project_selected.connect(self._open_project)
        self._start_page.import_yaml_requested.connect(self._on_import_yaml)
        self._start_page.delete_project_requested.connect(self._on_delete_project)
        self._stack.addWidget(self._start_page)  # index = PAGE_START

        # --- 编辑页 ---
        editor_page = QWidget()
        editor_layout = QVBoxLayout(editor_page)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        # 主分割器：节点拓扑图 + BT树（左）| 参数面板 + 插件选择（右）
        self.main_splitter = QSplitter(Qt.Horizontal)

        # 左侧：节点拓扑图 + BT 树选择器
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        # TODO: 添加 NodeGraphWidget
        # TODO: 添加 BTTreeSelectorWidget
        self.main_splitter.addWidget(left_widget)

        # 中右侧：参数面板 + 插件选择器
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        # TODO: 添加 ParamPanelWidget
        # TODO: 添加 PluginSelectorWidget
        self.main_splitter.addWidget(right_widget)

        self.main_splitter.setStretchFactor(0, 2)
        self.main_splitter.setStretchFactor(1, 3)

        editor_layout.addWidget(self.main_splitter, stretch=1)

        # 底部：YAML 预览
        self.yaml_preview = QTabWidget()
        self.yaml_preview.addTab(QWidget(), "nav2_params.yaml")
        self.yaml_preview.setMaximumHeight(250)
        editor_layout.addWidget(self.yaml_preview)

        self._stack.addWidget(editor_page)  # index = PAGE_EDITOR

        # 底部工具栏
        self._create_bottom_toolbar()

        # 状态栏
        self.setStatusBar(QStatusBar())

        # 初始显示启动页，加载最近项目
        self._stack.setCurrentIndex(PAGE_START)
        self._refresh_start_page()

    # ---- 页面切换 ----

    def _show_start_page(self):
        """切换到启动页。"""
        self._refresh_start_page()
        self._stack.setCurrentIndex(PAGE_START)
        self.project_label.setText("未打开项目")

    def _show_editor_page(self):
        """切换到编辑页，更新项目信息栏。"""
        project = self._project_manager.current_project
        if project:
            robot_type_map = {
                "diff_drive": "差速驱动",
                "omni": "全向轮",
                "ackermann": "阿克曼",
            }
            robot_display = robot_type_map.get(project.robot_type, project.robot_type)
            self.project_label.setText(
                f"项目：{project.project_name}  |  "
                f"ROS2：{project.ros2_version}  |  "
                f"机器人：{robot_display}"
            )
        self._stack.setCurrentIndex(PAGE_EDITOR)

    def _refresh_start_page(self):
        """刷新启动页的最近项目列表。"""
        projects = self._project_manager.list_recent_projects(self._projects_base_dir)
        self._start_page.load_recent_projects(projects)

    # ---- 项目操作 ----

    def _on_new_project(self):
        """打开项目向导创建新项目。"""
        wizard = ProjectWizard(self)
        if wizard.exec() != ProjectWizard.Accepted:
            return

        project_model = wizard.to_project_model()

        # 确保基础目录存在
        os.makedirs(self._projects_base_dir, exist_ok=True)

        # 弹出选择父目录对话框，默认使用 _projects_base_dir
        base_dir = QFileDialog.getExistingDirectory(
            self, "选择项目保存位置", self._projects_base_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if not base_dir:
            return

        try:
            project_dir = self._project_manager.new_project(project_model, base_dir)
            self._show_editor_page()
            self.statusBar().showMessage(f"项目已创建：{project_dir}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "创建项目失败", str(e))

    def _on_open_project(self):
        """打开已有的 .nav2studio.json 项目。"""
        proj_dir = QFileDialog.getExistingDirectory(
            self, "选择项目目录", self._projects_base_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if proj_dir:
            self._open_project(proj_dir)

    def _open_project(self, proj_dir: str):
        """加载指定目录的项目并切换到编辑页。"""
        proj_file = os.path.join(proj_dir, ProjectManager.PROJECT_FILE)
        if not os.path.isfile(proj_file):
            QMessageBox.warning(
                self, "无法打开项目",
                f"所选目录中未找到 {ProjectManager.PROJECT_FILE} 文件。\n{proj_dir}",
            )
            return

        try:
            self._project_manager.load(proj_dir)
            self._show_editor_page()
            self.statusBar().showMessage(f"项目已打开：{proj_dir}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "加载项目失败", str(e))

    # ---- 菜单栏 ----

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        # 文件菜单
        file_menu = menu_bar.addMenu("文件(&F)")
        file_menu.addAction("新建项目", self._on_new_project)
        file_menu.addAction("打开项目", self._on_open_project)
        file_menu.addSeparator()
        file_menu.addAction("关闭项目", self._show_start_page)
        file_menu.addAction("删除项目...", self._on_delete_current_project)
        file_menu.addAction("保存", self._on_save_project)
        file_menu.addAction("另存为...", self._on_save_as)
        file_menu.addSeparator()
        file_menu.addAction("导入 nav2_params.yaml", lambda: self._on_import_yaml())
        file_menu.addSeparator()
        file_menu.addAction("退出", self.close)

        # 视图菜单
        view_menu = menu_bar.addMenu("视图(&V)")
        view_menu.addAction("基础模式", self._on_basic_mode)
        view_menu.addAction("专家模式", self._on_expert_mode)

        # 工具菜单
        tools_menu = menu_bar.addMenu("工具(&T)")
        tools_menu.addAction("导出 YAML", self._on_export_yaml)

        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助(&H)")
        help_menu.addAction("关于", self._on_about)

    def _create_project_info_bar(self):
        self.info_bar = QToolBar("项目信息")
        self.info_bar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.info_bar)
        self.project_label = QLabel("未打开项目")
        self.info_bar.addWidget(self.project_label)

    def _create_bottom_toolbar(self):
        self.bottom_toolbar = QToolBar("操作")
        self.bottom_toolbar.setMovable(False)
        self.addToolBar(Qt.BottomToolBarArea, self.bottom_toolbar)
        self.bottom_toolbar.addAction("导出 YAML", self._on_export_yaml)

    # --- 槽函数桩 ---

    def _on_save_project(self):
        """保存当前项目。"""
        if self._project_manager.current_project:
            self._project_manager.save()
            self.statusBar().showMessage("项目已保存", 2000)

    def _on_save_as(self):
        """将当前项目另存到新位置。"""
        # TODO: 文件对话框 + ProjectManager.save_as()
        pass

    def _on_import_yaml(self, yaml_path: str = ""):
        """从 nav2_params.yaml 文件导入配置，创建新项目。

        参数：
            yaml_path: 若由信号传入则为文件路径；为空则弹出文件对话框。
        """
        if not yaml_path:
            yaml_path, _ = QFileDialog.getOpenFileName(
                self, "选择 nav2_params.yaml", "",
                "YAML 文件 (*.yaml *.yml);;所有文件 (*)",
            )
        if not yaml_path:
            return

        importer = YamlImporter()
        project_model, report = importer.import_file(yaml_path)

        if project_model is None:
            QMessageBox.warning(
                self, "导入失败",
                f"无法解析所选 YAML 文件。\n"
                f"未映射项: {report.unmapped_count}\n\n"
                f"请确保文件是有效的 nav2_params.yaml。",
            )
            return

        # 确保基础目录存在
        os.makedirs(self._projects_base_dir, exist_ok=True)

        try:
            project_dir = self._project_manager.new_project(
                project_model, self._projects_base_dir,
            )
            self._show_editor_page()
            summary = (
                f"已从 YAML 导入项目：{project_dir}\n"
                f"映射 {report.mapped_count} 项，"
                f"未映射 {report.unmapped_count} 项"
            )
            self.statusBar().showMessage(summary, 5000)
        except Exception as e:
            QMessageBox.critical(self, "导入项目失败", str(e))

    def _on_delete_project(self, project_dir: str):
        """删除指定目录的项目，带二次确认。

        参数：
            project_dir: 要删除的项目目录路径
        """
        reply = QMessageBox.warning(
            self, "确认删除项目",
            f"即将永久删除项目目录：\n{project_dir}\n\n"
            f"此操作不可恢复，确定要删除吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            # 若删除的是当前打开的项目，先切回启动页并清空
            if (self._project_manager.project_dir and
                    os.path.samefile(self._project_manager.project_dir, project_dir)):
                self._project_manager.current_project = None
                self._project_manager.project_dir = None
                self._stack.setCurrentIndex(PAGE_START)

            ProjectManager.delete_project(project_dir)
            self._refresh_start_page()
            self.statusBar().showMessage(f"项目已删除：{project_dir}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "删除项目失败", str(e))

    def _on_delete_current_project(self):
        """从菜单栏删除当前打开的项目。"""
        if not self._project_manager.project_dir:
            QMessageBox.information(self, "提示", "当前没有打开的项目。")
            return
        self._on_delete_project(self._project_manager.project_dir)

    def _on_export_yaml(self):
        """将当前配置导出为 nav2_params.yaml。"""
        if not self._project_manager.current_project:
            QMessageBox.information(self, "提示", "请先打开或创建项目。")
            return

        project = self._project_manager.current_project
        default_name = f"{project.project_name or 'nav2_params'}.yaml"
        if self._project_manager.project_dir:
            default_path = os.path.join(self._project_manager.project_dir, default_name)
        else:
            default_path = default_name

        save_path, _ = QFileDialog.getSaveFileName(
            self, "导出 nav2_params.yaml", default_path,
            "YAML 文件 (*.yaml *.yml);;所有文件 (*)",
        )
        if not save_path:
            return

        try:
            self._project_manager.export_yaml(save_path)
            self.statusBar().showMessage(f"YAML 已导出：{save_path}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def _on_basic_mode(self):
        """切换到基础参数显示模式。"""
        # TODO: 发送信号到 ParamPanel
        pass

    def _on_expert_mode(self):
        """切换到专家参数显示模式。"""
        # TODO: 发送信号到 ParamPanel
        pass

    def _on_about(self):
        """显示关于对话框。"""
        QMessageBox.about(
            self, "关于 Nav2 Launch Studio",
            "Nav2 Launch Studio v0.1.0\n\n"
            "ROS2 Nav2 可视化配置工具\n"
            "一键生成 nav2_params.yaml",
        )
