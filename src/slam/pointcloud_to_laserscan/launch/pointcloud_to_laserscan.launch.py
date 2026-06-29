from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    params_file = LaunchConfiguration('params_file')
    use_sim_time = LaunchConfiguration('use_sim_time')

    default_params_file = os.path.join(
        get_package_share_directory('pointcloud_to_laserscan'),
        'params',
        'pointcloud_to_laserscan.yaml',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=default_params_file,
            description='pointcloud_to_laserscan 参数文件路径',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='是否使用仿真时间',
        ),
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pointcloud_to_laserscan',
            output='screen',
            parameters=[
                params_file,
                {
                    'use_sim_time': ParameterValue(use_sim_time, value_type=bool),
                },
            ],
        ),
    ])
