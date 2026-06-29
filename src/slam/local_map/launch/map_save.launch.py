#install(DIRECTORY config params launch DESTINATION share/${PROJECT_NAME}) #cmake配置
#<exec_depend>ros2launch</exec_depend> <!--package.xml配置-->
#from glob import glob #用于setup.py配置多个launch文件
#('share/' + package_name + '/launch', glob('launch/*launch.py')),
#('share/' + package_name + '/launch', glob('launch/*launch.xml')),
#('share/' + package_name + '/launch', glob('launch/*launch.yaml')),
#(os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),

from launch import LaunchDescription
from launch_ros.actions import Node
import os
# 封装终端指令相关类--------------
# from launch.actions import ExecuteProcess
# from launch.substitutions import FindExecutable   #FindExecutable(name="ros2")
# 参数声明与获取-----------------
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
# from launch.conditions import IfCondition #判断是否执行
# from launch.conditions import UnlessCondition #取反
# from launch.substitutions import PythonExpression #运行时计算表达式
# 文件包含相关-------------------
# from launch.actions import IncludeLaunchDescription
# from launch.launch_description_sources import PythonLaunchDescriptionSource
# 分组相关----------------------
# from launch_ros.actions import PushRosNamespace
# from launch.actions import GroupAction
# 事件相关----------------------
# from launch.event_handlers import OnProcessStart, OnProcessExit
# from launch.actions import ExecuteProcess, RegisterEventHandler,LogInfo
# 获取功能包下share目录路径-------
from ament_index_python.packages import get_package_share_directory
# urdf文件处理相关--------------
# from launch_ros.parameter_descriptions import ParameterValue
# 组件相关-------------
# from launch_ros.actions import ComposableNodeContainer
# from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    ld = LaunchDescription()

    map_file_path = os.path.join(os.getcwd(), 'map')
    map_file_name = 'local_map'
    map_file_prefix = os.path.join(map_file_path, map_file_name)
    os.makedirs(map_file_path, exist_ok=True) # 确认路径是否存在

    # 默认参数文件路径
    default_params_file = os.path.join(
        get_package_share_directory('local_map'),
        'params',
        'map_saver.yaml',
    )

    # 定义参数文件路径的LaunchConfiguration
    ld.add_action(DeclareLaunchArgument(
        'params_file',
        default_value=default_params_file,
        description='地图保存器参数文件的完整路径',
    ))

    params_file = LaunchConfiguration('params_file')

    map_save_node = Node(
        package='nav2_map_server',
        executable='map_saver_cli',
        name='map_saver',
        output='screen',
        arguments=[
            # 要保存的地图话题，通常由 SLAM 或 map_server 发布 nav_msgs/OccupancyGrid。
            '-t', '/map',
            # 输出地图文件名前缀，不带扩展名；会生成 local_map.yaml 和 local_map.pgm。
            '-f', map_file_prefix,
            # 地图图片格式，常用 pgm；也支持 png、bmp;默认为 pgm。
            '--fmt', 'pgm',
            # 地图保存模式：trinary 为黑白灰三值地图，scale/raw 会保留更多概率信息。
            '--mode', 'trinary',
        ],
        parameters=[params_file],
    )
    ld.add_action(map_save_node)

    return ld
