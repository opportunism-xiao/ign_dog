from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    params_file = LaunchConfiguration('filter_params_file')
    input_topic = LaunchConfiguration('filter_input_topic')
    output_topic = LaunchConfiguration('filter_output_topic')
    marker_topic = LaunchConfiguration('marker_topic')
    use_sim_time = LaunchConfiguration('use_sim_time')

    default_params_file = os.path.join(
        get_package_share_directory('scan_box_filter'),
        'params',
        'scan_box_filter.yaml',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'filter_params_file',
            default_value=default_params_file,
            description='LaserScan box filter 参数文件路径',
        ),
        DeclareLaunchArgument(
            'filter_input_topic',
            default_value='/scan/points_to_scan',
            description='输入 LaserScan 话题',
        ),
        DeclareLaunchArgument(
            'filter_output_topic',
            default_value='/scan/filtered',
            description='过滤后的 LaserScan 话题',
        ),
        DeclareLaunchArgument(
            'marker_topic',
            default_value='/scan_box_filter/box_marker',
            description='RViz 过滤盒子 Marker 话题',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='是否使用仿真时间',
        ),
        Node(
            package='laser_filters',
            executable='scan_to_scan_filter_chain',
            name='scan_to_scan_filter_chain',
            output='screen',
            parameters=[
                params_file,
                {'use_sim_time': ParameterValue(use_sim_time, value_type=bool)},
            ],
            remappings=[
                ('/scan', input_topic),
                ('/scan_filtered', output_topic),
            ],
        ),
        Node(
            package='scan_box_filter',
            executable='scan_box_filter_marker.py',
            name='scan_box_filter_marker',
            output='screen',
            parameters=[
                params_file,
                {
                    'marker_topic': marker_topic,
                    'use_sim_time': ParameterValue(use_sim_time, value_type=bool),
                },
            ],
        ),
    ])
