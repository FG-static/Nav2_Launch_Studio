"""主窗口 - 管理所有 UI 模块和布局。"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QStatusBar, QMenuBar,
    QToolBar, QLabel,
)
from PySide6.QtCore import Qt


class MainWindow(QMainWindow):
    """Nav2 Launch Studio 主窗口。

    布局（对应 PRD 4.2）：
    - 菜单栏：文件 | 视图 | 工具 | 帮助
    - 项目信息栏：项目名 | ROS2版本 | 机器人类型
    - 中央区域：节点拓扑图（左）+ 参数配置面板（中右）+ 插件选择器（右）
    - 节点图下方：BT 树选择区
    - 底部：YAML 预览 + 导出工具栏
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nav2 Launch Studio")
        self.resize(1280, 800)
        self._init_ui()

    def _init_ui(self):
        # 菜单栏
        self._create_menu_bar()

        # 项目信息栏
        self._create_project_info_bar()

        # 中央部件
        central = QWidget() # QWidget是QT的窗口部件，可以用来放置其他部件
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

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

        main_layout.addWidget(self.main_splitter, stretch=1)

        # 底部：YAML 预览
        self.yaml_preview = QTabWidget() # QTabWidget是QT的标签页部件，可以用来放置其他部件
        self.yaml_preview.addTab(QWidget(), "nav2_params.yaml")
        self.yaml_preview.setMaximumHeight(250)
        main_layout.addWidget(self.yaml_preview)

        # 底部工具栏
        self._create_bottom_toolbar()

        # 状态栏
        self.setStatusBar(QStatusBar())

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        # 文件菜单
        file_menu = menu_bar.addMenu("文件(&F)")
        file_menu.addAction("新建项目", self._on_new_project)
        file_menu.addAction("打开项目", self._on_open_project)
        file_menu.addSeparator()
        file_menu.addAction("保存", self._on_save_project)
        file_menu.addAction("另存为...", self._on_save_as)
        file_menu.addSeparator()
        file_menu.addAction("导入 nav2_params.yaml", self._on_import_yaml)
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
        # QToolBar的意思是工具栏，可以将QToolBar添加到主窗口的顶部或底部，也可以将QToolBar添加到其他QToolBar的上方或下方。
        self.info_bar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.info_bar) # 将info_bar添加到主窗口的顶部
        self.project_label = QLabel("未打开项目") # 初始化项目标签
        self.info_bar.addWidget(self.project_label) # 添加项目标签到info_bar

    def _create_bottom_toolbar(self):
        self.bottom_toolbar = QToolBar("操作")
        self.bottom_toolbar.setMovable(False)
        self.addToolBar(Qt.BottomToolBarArea, self.bottom_toolbar)
        self.bottom_toolbar.addAction("导出 YAML", self._on_export_yaml)

    # --- 槽函数桩 ---

    def _on_new_project(self):
        """打开项目向导创建新项目。"""
        # TODO: 完成_on_new_project()函数
        # 启动 ProjectWizard 对话框
        pass

    def _on_open_project(self):
        """打开已有的 .nav2studio.json 项目。"""
        # TODO: 完成_on_open_project()函数
        # 文件对话框 + ProjectManager.load()
        pass

    def _on_save_project(self):
        """保存当前项目。"""
        # TODO: 完成_on_save_project()函数 
        # ProjectManager.save()
        pass

    def _on_save_as(self):
        """将当前项目另存到新位置。"""
        # TODO: 完成_on_save_as()函数 
        # 文件对话框 + ProjectManager.save_as()
        pass

    def _on_import_yaml(self):
        """导入 nav2_params.yaml 文件。"""
        # TODO: 完成_on_import_yaml()函数 
        # 文件对话框 + YamlImporter.import_file()
        pass

    def _on_export_yaml(self):
        """将当前配置导出为 nav2_params.yaml。"""
        # TODO: 完成_on_export_yaml()函数 
        # YamlGenerator.generate() + 保存文件
        pass

    def _on_basic_mode(self):
        """切换到基础参数显示模式。"""
        # TODO: 完成_on_basic_mode()函数
        # 发送信号到 ParamPanel
        pass

    def _on_expert_mode(self):
        """切换到专家参数显示模式。"""
        # TODO: 完成_on_expert_mode()函数
        # 发送信号到 ParamPanel
        pass

    def _on_about(self):
        """显示关于对话框。"""
        # TODO: 完成_on_about()函数
        # 显示 AboutDialog
        pass
