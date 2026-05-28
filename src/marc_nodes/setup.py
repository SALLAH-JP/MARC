from setuptools import find_packages, setup

package_name = 'marc_nodes'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'pyserial'],
    zip_safe=True,
    maintainer='Jean-Paul',
    maintainer_email='you@example.com',
    description='Noeuds ROS2 du robot MARC',
    license='MIT',
    entry_points={
        'console_scripts': [
            # ros2 run marc_nodes firmware_node
            'firmware_node = marc_nodes.firmware_node:main',
        ],
    },
)
