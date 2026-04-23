# Nav2 Launch Studio 项目文件依赖关系

## 项目结构概览

```
nav2_launch_studio/
├── main.py                          # 应用入口
├── core/                            # 核心业务逻辑
│   ├── project_model.py             # 数据模型
│   ├── project_manager.py           # 项目持久化管理
│   ├── plugin_registry.py          # 插件注册表
│   ├── yaml_importer.py            # YAML 导入器
│   ├── yaml_generator.py           # YAML 生成器
│   └── node_dependencies.py        # 节点依赖关系定义
├── utils/                           # 工具模块
│   ├── schema_loader.py             # Schema 加载器
│   └── bt_tree_discovery.py       # BT 树发现
└── ui/                             # UI 模块
    ├── main_window.py              # 主窗口
    ├── start_page.py               # 启动页
    ├── wizard/                    # 向导
    │   └── project_wizard.py      # 项目创建向导
    ├── panels/                    # 面板
    │   ├── param_panel.py        # 参数配置面板
    │   └── yaml_preview.py        # YAML 预览
    └── widgets/                   # UI 组件
        ├── node_graph.py         # 节点拓扑图
        ├── plugin_selector.py     # 插件选择器
        ├── bt_tree_selector.py  # BT 树选择器
        └── key_value_editor.py # 键值对编辑器
```

## 模块依赖关系详情

### 1. main.py (应用入口)

**依赖:**
- `PySide6.QtWidgets` - Qt 框架
- `nav2_launch_studio.ui.main_window` - 主窗口模块

**被依赖:**
- 无 (入口文件)

---

### 2. core/project_model.py (数据模型)

**依赖:**
- `dataclasses` - Python 内置 dataclass
- `datetime` - Python 内置日期时间
- `typing` - Python 类型提示

**被依赖:**
- `core/project_manager.py` - 项目管理器使用数据模型
- (future) 其他需要项目数据的模块

---

### 3. core/project_manager.py (项目持久化管理)

**依赖:**
- `nav2_launch_studio.core.project_model` - `ProjectModel` 类
- `json` - JSON 序列化
- `os` - 操作系统接口
- `shutil` - 文件操作
- `pathlib.Path` - 路径处理

**被依赖:**
- `ui/main_window.py` - TODO (通过 ProjectManager 保存/加载项目)

---

### 4. core/plugin_registry.py (插件注册表)

**依赖:**
- `typing` - 类型提示

**被依赖:**
- `ui/widgets/plugin_selector.py` - TODO (通过 PluginRegistry 获取插件列表)

---

### 5. core/yaml_importer.py (YAML 导入器)

**依赖:**
- `dataclasses` - 导入报告数据结构
- `typing` - 类型提示

**被依赖:**
- `ui/main_window.py` - TODO (导入 YAML 文件)

**特殊:**
- TODO: `schema_loader` 参数 (需从 `utils/schema_loader.py` 注入)

---

### 6. core/yaml_generator.py (YAML 生成器)

**依赖:**
- `typing` - 类型提示
- `jinja2` - 模板引擎 (TODO)

**被依赖:**
- `ui/main_window.py` - TODO (生成 YAML 预览)
- `ui/panels/yaml_preview.py` - TODO (实时预览)

**特殊:**
- TODO: 需要 Jinja2 模板文件 `templates/nav2_params.yaml.jinja2`

---

### 7. core/node_dependencies.py (节点依赖关系定义)

**依赖:**
- 无 (纯数据定义模块)

**被依赖:**
- `ui/widgets/node_graph.py` - TODO (检查节点启用/禁用的依赖关系)

---

### 8. utils/schema_loader.py (Schema 加载器)

**依赖:**
- `json` - JSON 解析
- `os` - 文件系统操作
- `typing` - 类型提示

**被依赖:**
- `core/yaml_importer.py` - TODO (需注入 SchemaLoader 实例)

---

### 9. utils/bt_tree_discovery.py (BT 树发现)

**依���:**
- `os` - 文件系统操作
- `subprocess` - 执行 ros2 命令
- `typing` - 类型提示

**被依赖:**
- `ui/widgets/bt_tree_selector.py` - TODO (扫描 BT 树模板)

---

### 10. ui/main_window.py (主窗口)

**依赖:**
- `PySide6.QtWidgets` - Qt 部件
- `PySide6.QtCore` - Qt 核心

**被依赖:**
- `main.py` - 入口导入主窗口
- (future) 所有 UI 组件的容器

---

### 11. ui/start_page.py (启动页)

**依赖:**
- `PySide6.QtWidgets` - Qt 部件

**被依赖:**
- `ui/main_window.py` - 嵌入启动页

---

### 12. ui/wizard/project_wizard.py (项目创建向导)

**依赖:**
- `PySide6.QtWidgets` - Qt 向导部件
- `PySide6.QtGui` - Qt GUI

**被依赖:**
- `ui/main_window.py` - TODO (打开项目向导)

---

### 13. ui/panels/param_panel.py (参数配置面板)

**依赖:**
- `PySide6.QtWidgets` - Qt 部件
- `PySide6.QtCore` - Qt 信号槽

**被依赖:**
- `ui/main_window.py` - TODO (嵌入参数面板)

---

### 14. ui/panels/yaml_preview.py (YAML 预览)

**依赖:**
- `PySide6.QtWidgets` - Qt 部件
- `PySide6.QtCore` - Qt 信号槽

**被依赖:**
- `ui/main_window.py` - TODO (嵌入 YAML 预览)

---

### 15. ui/widgets/node_graph.py (节点拓扑图)

**依赖:**
- `PySide6.QtWidgets` - Qt 图形部件
- `PySide6.QtCore` - Qt 核心 (Signal)

**被依赖:**
- `ui/main_window.py` - TODO (嵌入节点图)

**特殊:**
- TODO: 从 `core/node_dependencies.py` 获取依赖关系

---

### 16. ui/widgets/plugin_selector.py (插件选择器)

**依赖:**
- `PySide6.QtWidgets` - Qt 部件
- `PySide6.QtCore` - Qt 信号槽

**被依赖:**
- `ui/main_window.py` - TODO (嵌入插件选择器)

**特殊:**
- TODO: 从 `core/plugin_registry.py` 获取插件列表

---

### 17. ui/widgets/bt_tree_selector.py (BT 树选择器)

**依赖:**
- `PySide6.QtWidgets` - Qt 部件
- `PySide6.QtCore` - Qt 信号槽

**被依赖:**
- `ui/main_window.py` - TODO (嵌入 BT 树选择器)

**特殊:**
- TODO: 从 `utils/bt_tree_discovery.py` 扫描 BT 树模板

---

### 18. ui/widgets/key_value_editor.py (键值对编辑器)

**依赖:**
- `PySide6.QtWidgets` - Qt 部件
- `PySide6.QtCore` - Qt 信号槽

**被依赖:**
- `ui/main_window.py` - TODO (用于自定义插件参数编辑)

---

## 外部依赖

### Python 标准库
- `json` - JSON 序列化
- `os` - 操作系统接口
- `shutil` - 文件操作
- `subprocess` - 子进程
- `pathlib` - 路径对象
- `datetime` - 日期时间
- `dataclasses` - 数据类
- `typing` - 类型提示

### PyPI 第三方库
- `PySide6` - Qt 框架 Python 绑定
- `PyYAML` - YAML 解析 (TODO)
- `jinja2` - 模板引擎 (TODO)

### ROS 2 相关
- `ros2 pkg` - 查找 Nav2 包路径

---

## TODO 依赖注入关系

项目中存在多处待实现的依赖注入模式：

```
schema_loader (utils/)  -->  yaml_importer (core/)
plugin_registry (core/)    -->  plugin_selector (ui/widgets/)
node_dependencies (core/) -->  node_graph (ui/widgets/)
bt_tree_discovery (utils/) -->  bt_tree_selector (ui/widgets/)
yaml_generator (core/)  -->  yaml_preview (ui/panels/)
project_manager (core/) -->  main_window (ui/)
```

---

## 文件依赖图

```
main.py
  └─> ui/main_window.py
         ├─> (TODO) core/project_manager.py
         ├─> (TODO) core/yaml_importer.py
         ├─> (TODO) core/yaml_generator.py
         ├─> ui/panels/param_panel.py
         ├─> ui/panels/yaml_preview.py
         ├─> ui/widgets/node_graph.py
         │      └─> core/node_dependencies.py
         ├─> ui/widgets/plugin_selector.py
         │      └─> core/plugin_registry.py
         ├─> ui/widgets/bt_tree_selector.py
         │      └─> utils/bt_tree_discovery.py
         ├─> ui/widgets/key_value_editor.py
         ├��> ui/start_page.py
         └─> ui/wizard/project_wizard.py

core/project_manager.py
  └─> core/project_model.py
```

---

## 生成器/消费者关系

| 模块 | 角色 | 说明 |
|------|------|------|
| `project_model.py` | 消费者 | 数据模型，被其他模块使用 |
| `project_manager.py` | 生成器 | 生成 `.nav2studio.json` 文件 |
| `plugin_registry.py` | 生成器 | 提供插件元数据 |
| `yaml_generator.py` | 生成器 | 生成 `nav2_params.yaml` |
| `yaml_importer.py` | 消费者 | 消费 YAML 文件 |
| `schema_loader.py` | 生产者 | 加载 schema 文件 |
| `bt_tree_discovery.py` | 生产者 | 发现 BT 树模板 |