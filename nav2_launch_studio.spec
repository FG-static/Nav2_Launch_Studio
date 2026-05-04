# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 - Nav2 Launch Studio"""

import os

block_cipher = None

a = Analysis(
    ['nav2_launch_studio/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Jinja2 YAML 生成模板
        ('nav2_launch_studio/templates/*.jinja2', 'nav2_launch_studio/templates'),
    ],
    hiddenimports=[
        'nav2_launch_studio.core.project_model',
        'nav2_launch_studio.core.project_manager',
        'nav2_launch_studio.core.yaml_generator',
        'nav2_launch_studio.core.yaml_importer',
        'nav2_launch_studio.core.plugin_registry',
        'nav2_launch_studio.core.node_dependencies',
        'nav2_launch_studio.ui.main_window',
        'nav2_launch_studio.ui.start_page',
        'nav2_launch_studio.ui.wizard.project_wizard',
        'nav2_launch_studio.ui.panels.param_panel',
        'nav2_launch_studio.ui.panels.yaml_preview',
        'nav2_launch_studio.ui.widgets.node_graph',
        'nav2_launch_studio.ui.widgets.plugin_selector',
        'nav2_launch_studio.ui.widgets.bt_tree_selector',
        'nav2_launch_studio.ui.widgets.key_value_editor',
        'nav2_launch_studio.utils.schema_loader',
        'nav2_launch_studio.utils.bt_tree_discovery',
        'yaml',
        'jinja2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的 ROS2 依赖（GUI 不直接依赖）
        'rclpy',
        'nav2_msgs',
        'nav2_common',
        'nav2_bringup',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Nav2LaunchStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 无控制台窗口
    icon=None,       # 可替换为 .ico/.png 图标
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Nav2LaunchStudio',
)
