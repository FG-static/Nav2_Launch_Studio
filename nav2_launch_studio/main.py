"""Nav2 Launch Studio - ROS2 Nav2 可视化配置工具。"""

import sys
from PySide6.QtWidgets import QApplication
from nav2_launch_studio.ui.main_window import MainWindow


def main(args=None):
    """应用程序入口。"""
    app = QApplication(sys.argv)
    app.setApplicationName("Nav2 Launch Studio")
    app.setOrganizationName("Nav2LaunchStudio")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
