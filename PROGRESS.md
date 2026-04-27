# Nav2 Launch Studio 项目进度

**文档版本**：v1.1  
**更新日期**：2026-04-27  
**对应 PRD**：v1.3

---

## 一、已实现功能

### 1.1 项目框架与构建

| 功能 | 位置 | 说明 |
|------|------|------|
| ROS2 ament_python 包结构 | `package.xml`, `setup.py`, `setup.cfg` | 标准 ROS2 包，`ros2 run nav2_launch_studio gui` 启动 |
| colcon 构建 | 根目录 | 构建通过，包可被 `ros2 pkg list` 识别 |
| PySide6 GUI 入口 | `nav2_launch_studio/main.py` | QApplication + MainWindow 启动 |
| 测试框架 | `pytest.ini`, `test/` | 11 个测试全部通过 |

### 1.2 数据模型

| 功能 | 位置 | 说明 |
|------|------|------|
| 项目数据模型 | `core/project_model.py` | `ProjectModel` dataclass，对应 `.nav2studio.json`，含序列化 `to_dict()` + 反序列化 `from_dict()` |
| 传感器配置模型 | `core/project_model.py:SensorConfig` | 激光雷达/深度相机/IMU 话题与坐标系 |
| 向导配置模型 | `core/project_model.py:WizardConfig` | 传感器 + 地图来源 |
| 自定义插件模型 | `core/project_model.py:CustomPlugin` | 显示名/插件类型/实例名/分类/参数列表 |
| 默认节点配置 | `core/project_model.py:_default_nodes()` | 9 个 Nav2 节点默认启用状态与类型 |
| 默认插件配置 | `core/project_model.py:_default_plugins()` | 规划器/控制器/平滑器/代价地图层/Recovery 默认值 |

### 1.2.1 项目持久化与新建/打开项目

| 功能 | 位置 | 说明 |
|------|------|------|
| 项目反序列化 | `core/project_model.py:from_dict()` | 从 `.nav2studio.json` 字典还原 ProjectModel，含嵌套 SensorConfig/WizardConfig |
| 最近项目扫描 | `core/project_manager.py:list_recent_projects()` | 扫描目录下含 `.nav2studio.json` 的子目录，按 `updated_at` 降序排序 |
| 新建项目流程 | `ui/main_window.py:_on_new_project()` | 向导 → ProjectModel → QFileDialog 选位置 → ProjectManager.new_project() → 编辑页 |
| 打开项目流程 | `ui/main_window.py:_on_open_project()` | QFileDialog 选目录 → ProjectManager.load() → 编辑页，含 `.nav2studio.json` 存在性检查 |
| 启动页/编辑页切换 | `ui/main_window.py:_stack` | QStackedWidget 实现启动页与编辑页切换，打开/新建项目后自动跳转 |
| 项目信息栏更新 | `ui/main_window.py:_show_editor_page()` | 打开项目后信息栏显示项目名/ROS2版本/机器人类型 |
| 向导数据转换 | `ui/wizard/project_wizard.py:to_project_model()` | 从向导字段值构建 ProjectModel + SensorConfig + WizardConfig |
| 启动页最近项目加载 | `ui/start_page.py:load_recent_projects()` | 接收项目列表数据填充 QListWidget，双击打开项目 |
| 保存项目 | `ui/main_window.py:_on_save_project()` | 调用 ProjectManager.save()，状态栏提示 |
| 导入项目（YAML） | `ui/main_window.py:_on_import_yaml()` | 选择 .yaml 文件 → YamlImporter 解析 → 创建新项目（导入解析待完善，UI 流程已就绪） |

### 1.3 节点依赖关系

| 功能 | 位置 | 说明 |
|------|------|------|
| 依赖图定义 | `core/node_dependencies.py:NODE_DEPENDENCIES` | 9 个节点的有向依赖关系 |
| 反向依赖计算 | `core/node_dependencies.py:REVERSE_DEPENDENCIES` | 自动从正向依赖生成 |
| 禁用检查 | `core/node_dependencies.py:check_disable_allowed()` | 必选节点不可禁用，被依赖节点弹出警告 |
| 节点分类 | `core/node_dependencies.py:NODE_TYPES` | mandatory/recommended/optional 分类 |

### 1.4 插件注册表

| 功能 | 位置 | 说明 |
|------|------|------|
| 内置规划器元数据 | `core/plugin_registry.py:BUILTIN_PLANNERS` | 5 个规划器（NavFn/Smac2D/SmacLattice/SmacHybrid/Theta*） |
| 内置控制器元数据 | `core/plugin_registry.py:BUILTIN_CONTROLLERS` | 4 个控制器（DWB/MPPI/RPP/Graceful） |
| 内置平滑器元数据 | `core/plugin_registry.py:BUILTIN_SMOOTHERS` | 3 个平滑器（Simple/SG/Constrained） |
| 内置代价地图层元数据 | `core/plugin_registry.py:BUILTIN_COSTMAP_LAYERS` | 5 个层（Static/Obstacle/Inflation/Voxel/Range） |
| 内置 Recovery 元数据 | `core/plugin_registry.py:BUILTIN_RECOVERIES` | 5 个行为（Spin/BackUp/DriveOnHeading/Wait/ClearCostmap） |
| 自定义插件注册/删除 | `core/plugin_registry.py:register_custom_plugin()` | 注册后在对应分类中显示 🔧 标签 |

### 1.5 UI 骨架

| 功能 | 位置 | 说明 |
|------|------|------|
| 主窗口布局 | `ui/main_window.py:MainWindow` | 菜单栏/项目信息栏/QStackedWidget(启动页+编辑页)/底部预览+工具栏，集成新建/打开项目功能 |
| 启动页 | `ui/start_page.py:StartPageWidget` | 项目列表 + 新建/打开/导入按钮 + 双击打开 + 信号通知 MainWindow（导入按钮选择 .yaml 文件，打开按钮选择项目目录） |
| 项目向导 | `ui/wizard/project_wizard.py:ProjectWizard` | 4 步向导，含向导字段注册 + `to_project_model()` 方法 |
| 节点拓扑图骨架 | `ui/widgets/node_graph.py` | QGraphicsView/Scene/Item 骨架，信号定义 |
| 参数面板骨架 | `ui/panels/param_panel.py` | 基础/专家模式切换，按类型创建控件的方法 |
| 插件选择器骨架 | `ui/widgets/plugin_selector.py` | Tab 分组，全局/局部代价地图分离，自定义插件对话框 |
| BT 树选择器骨架 | `ui/widgets/bt_tree_selector.py` | 模板列表 + 自定义文件选择 + Groot2 按钮 |
| YAML 预览骨架 | `ui/panels/yaml_preview.py` | 只读文本区 + 复制/导出按钮 |
| 键值编辑器骨架 | `ui/widgets/key_value_editor.py` | 表格 + 添加/删除/YAML 导入 |

### 1.6 工具类

| 功能 | 位置 | 说明 |
|------|------|------|
| Schema 加载器 | `utils/schema_loader.py:SchemaLoader` | 加载 JSON schema，含缓存和版本覆盖 |
| BT 树发现 | `utils/bt_tree_discovery.py:BTTreeDiscovery` | 通过 `ros2 pkg prefix` 动态扫描，检测 Groot2 |

### 1.7 模板

| 功能 | 位置 | 说明 |
|------|------|------|
| YAML 生成模板 | `templates/nav2_params.yaml.jinja2` | 包含所有 Nav2 节点的 YAML 模板骨架 |

---

## 二、待实现功能

### 2.1 Phase 1 - MVP 核心功能（优先级从高到低）

| 功能 | 位置 | 详细说明 |
|------|------|---------|
| **Jinja2 YAML 生成** | `core/yaml_generator.py:generate()` | 从 ProjectModel 渲染 Jinja2 模板，收集启用节点/插件声明/参数/代价地图层/BT树路径/自定义插件参数 |
| **YAML 导入解析** | `core/yaml_importer.py:import_file()` | PyYAML 解析 → 识别节点命名空间 → 提取插件声明 → 匹配内置插件参数 → 未匹配入 KV 编辑器 → 自动注册自定义插件 → 生成导入报告 |
| **项目持久化完善** | `core/project_manager.py` | `save_as()` 复制项目 |
| **插件选择器填充** | `ui/widgets/plugin_selector.py:load_plugins()` | 从 `PluginRegistry` 读取内置+自定义插件，填充到各分组 UI |
| **参数面板填充** | `ui/panels/param_panel.py:load_params()` | 根据 schema 创建控件、填充当前值、实现基础/专家模式显隐 |
| **参数面板取值** | `ui/panels/param_panel.py:get_params()` | 从各控件读取值返回字典，供 YAML 生成使用 |
| **节点拓扑图渲染** | `ui/widgets/node_graph.py:NodeItem.paint()` | 绘制节点（颜色按类型）、连线、复选框、点击事件 |
| **节点拓扑图交互** | `ui/widgets/node_graph.py:load_nodes()` | 加载节点配置、布局、依赖连线、启用/禁用+依赖检查 |
| **BT 树模板填充** | `ui/widgets/bt_tree_selector.py:load_builtin_templates()` | 调用 `BTTreeDiscovery` 扫描目录，填充列表 |
| **主窗口模块集成** | `ui/main_window.py:_init_ui()` | 将 NodeGraph/PluginSelector/ParamPanel/BTTreeSelector 等组件实例化嵌入布局 |
| **Schema 文件编写** | `schemas/` 各子目录 | 为所有内置插件和节点编写参数 JSON schema 文件（约 20+ 个文件） |
| **YAML 导出写文件** | `core/project_manager.py:export_yaml()` | 生成 YAML 字符串并写入目标路径 |
| **复制到剪贴板** | `ui/panels/yaml_preview.py:copy_btn` | 连接 `QApplication.clipboard()` 实现复制 |

### 2.2 Phase 1 - MVP 次要功能

| 功能 | 位置 | 详细说明 |
|------|------|---------|
| 工作空间浏览按钮 | `ui/wizard/project_wizard.py:BasicInfoPage` | workspace_browse_btn 点击打开 QFileDialog |
| 地图文件浏览按钮 | `ui/wizard/project_wizard.py:MapSourcePage` | map_browse_btn 点击打开 QFileDialog |
| Groot2 检测与预览 | `ui/widgets/bt_tree_selector.py:detect_groot2()` | 启动时检测，显示/隐藏按钮，subprocess 启动 |
| 自定义插件注册提交 | `ui/widgets/plugin_selector.py:CustomPluginDialog` | 对话框 OK 后写入 PluginRegistry，刷新列表 |
| YAML 粘贴导入 | `ui/widgets/key_value_editor.py:_on_yaml_import()` | 解析 YAML 文本为 KV 条目填充表格 |
| 参数校验 | `ui/panels/param_panel.py` | 超范围黄色警告、非法值红色错误、阻止生成 |
| 参数帮助气泡 | `ui/panels/param_panel.py` | 每个参数旁「?」按钮，显示 schema 中的 description |
| 浮点数滑块联动 | `ui/panels/param_panel.py:_create_float_widget()` | slider 与 spinbox 双向绑定，范围与步长配置 |
| 列表参数编辑器 | `ui/panels/param_panel.py:_create_list_widget()` | 可折叠的列表编辑器，替代当前的 QLineEdit 占位 |
| 项目删除/复制/导出zip | `ui/start_page.py` | 项目列表的右键菜单或按钮 |
| 导入报告对话框 | `core/yaml_importer.py` + 新 UI | 导入后显示 ✅/⚠️/❌ 统计，可逐条修正 |

---

## 三、可扩展功能

### 3.1 Phase 2 - 增强体验

| 功能 | 建议位置 | 详细说明 |
|------|---------|---------|
| 实时参数预览 | `ui/main_window.py` 信号连接 | 参数变化 → 重新生成 YAML → 更新预览，需防抖优化 |
| 参数合法性校验 | `core/param_validator.py`（新建） | 基于 schema 的范围/类型校验，插件兼容性矩阵检查 |
| 专家模式 YAML 编辑 | `ui/panels/param_panel.py` | 专家模式下显示 QTextEdit 直接编辑 YAML，带语法高亮 |
| 配置模板库 | `templates/presets/`（新建） | TurtleBot3/AGV 等预设配置 JSON，向导中可选 |
| Groot2 集成 | `ui/widgets/bt_tree_selector.py` | Phase 1 基础上增强：预览缩略图、编辑后自动刷新 |
| ROS2 跨版本参数适配 | `utils/schema_loader.py:apply_version_overrides()` | 已有框架，需填充各版本差异数据到 schema 文件中 |

### 3.2 Phase 3 - 生态扩展

| 功能 | 建议位置 | 详细说明 |
|------|---------|---------|
| 参数对比模式 | `ui/panels/diff_panel.py`（新建） | A/B 两套配置左右对比，高亮差异项 |
| 日志智能分析 | `core/log_analyzer.py`（新建） | 解析 ROS2 日志，识别 TF 报错/代价地图警告，给出修复建议 |
| 配置分享 | `core/share_manager.py`（新建） | 导出为分享链接或 JSON 文件，支持导入他人配置 |
| 多机器人配置 | `core/project_model.py` namespace 字段 | 已有 namespace 字段，需 UI 支持和 YAML 生成适配 |
| launch.py 生成 | `core/launch_generator.py`（新建） | 可选购入，基于配置数据生成 Python launch 文件 |
| 内嵌终端 | `ui/widgets/terminal_widget.py`（新建） | QProcess 嵌入终端，一键 ros2 launch，节点状态监控 |
| 节点状态监控 | `ui/widgets/node_status_panel.py`（新建） | 通过 rclpy 监听节点 lifecycle 状态，颜色指示 |

### 3.3 架构级扩展

| 功能 | 建议位置 | 详细说明 |
|------|---------|---------|
| 插件自动发现 | `utils/plugin_discovery.py`（新建） | 运行时通过 `ros2 pkg executables` 扫描已安装的 Nav2 插件包 |
| 多语言支持 (i18n) | `utils/i18n.py`（新建） | QTranslator 加载 .qm 翻译文件，支持中英文切换 |
| 主题/样式 | `resources/styles/`（新建） | QSS 样式表，支持亮色/暗色主题 |
| 仿真直通 | `core/sim_launcher.py`（新建） | 一键在 Gazebo/Isaac Sim 中测试当前配置 |
| 逆向工程增强 | `core/yaml_importer.py` | 增强 YAML 导入的智能匹配率，支持更多 Nav2 配置模式 |

---

## 四、Schema 文件待编写清单

以下 JSON 文件需要根据 Nav2 源码手动编写：

| 分类 | 文件名 | 对应插件/节点 | 状态 |
|------|--------|-------------|------|
| planners | `navfn_planner.json` | NavFn | ❌ 待编写 |
| planners | `smac_planner_2d.json` | Smac 2D A* | ❌ 待编写 |
| planners | `smac_planner_lattice.json` | Smac Lattice | ❌ 待编写 |
| planners | `smac_planner_hybrid.json` | Smac Hybrid-A* | ❌ 待编写 |
| planners | `theta_star_planner.json` | Theta* | ❌ 待编写 |
| controllers | `dwb_controller.json` | DWB | ❌ 待编写 |
| controllers | `mppi_controller.json` | MPPI | ❌ 待编写 |
| controllers | `regulated_pure_pursuit.json` | RPP | ❌ 待编写 |
| controllers | `graceful_controller.json` | Graceful | ❌ 待编写 |
| smoothers | `simple_smoother.json` | Simple | ❌ 待编写 |
| smoothers | `savitzky_golay_smoother.json` | SG | ❌ 待编写 |
| smoothers | `constrained_smoother.json` | Constrained | ❌ 待编写 |
| costmap_layers | `static_layer.json` | Static | ❌ 待编写 |
| costmap_layers | `obstacle_layer.json` | Obstacle | ❌ 待编写 |
| costmap_layers | `inflation_layer.json` | Inflation | ❌ 待编写 |
| costmap_layers | `voxel_layer.json` | Voxel | ❌ 待编写 |
| costmap_layers | `range_sensor_layer.json` | Range | ❌ 待编写 |
| recoveries | `spin.json` | Spin | ❌ 待编写 |
| recoveries | `backup.json` | BackUp | ❌ 待编写 |
| recoveries | `drive_on_heading.json` | DriveOnHeading | ❌ 待编写 |
| recoveries | `wait.json` | Wait | ❌ 待编写 |
| nodes | `bt_navigator.json` | bt_navigator 节点参数 | ❌ 待编写 |
| nodes | `controller_server.json` | controller_server 节点参数 | ❌ 待编写 |
| nodes | `planner_server.json` | planner_server 节点参数 | ❌ 待编写 |
| nodes | `behavior_server.json` | behavior_server 节点参数 | ❌ 待编写 |
| nodes | `amcl.json` | amcl 节点参数 | ❌ 待编写 |
| nodes | `map_server.json` | map_server 节点参数 | ❌ 待编写 |
