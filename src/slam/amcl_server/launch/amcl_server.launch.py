from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    default_params_file = os.path.join(
        get_package_share_directory('amcl_server'),
        'params',
        'amcl.yaml',
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')
    scan_topic = LaunchConfiguration('scan_topic')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock if true',
        ),
        DeclareLaunchArgument(
            'autostart',
            default_value='true',
            description='Automatically configure and activate AMCL',
        ),
        DeclareLaunchArgument(
            'params_file',
            default_value=default_params_file,
            description='Full path to the AMCL parameters file',
        ),
        DeclareLaunchArgument(
            'scan_topic',
            default_value='/scan',
            description='LaserScan topic used by AMCL',
        ),
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[
                params_file,
                {'use_sim_time': use_sim_time},
            ],
            remappings=[
                ('scan', scan_topic),
            ],
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='amcl_lifecycle_manager',
            output='screen',
            parameters=[
                {'use_sim_time': use_sim_time},
                {'autostart': autostart},
                {'node_names': ['amcl']},
            ],
        ),
    ])
