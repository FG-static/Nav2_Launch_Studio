from setuptools import find_packages, setup

package_name = 'nav2_launch_studio'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ZhangJiale',
    maintainer_email='zhangjiale@todo.todo',
    description='ROS2 Nav2 visual configuration tool - generate and edit nav2_params.yaml',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gui = nav2_launch_studio.main:main',
        ],
    },
)
