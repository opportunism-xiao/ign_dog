#install(DIRECTORY config params launch DESTINATION share/${PROJECT_NAME}) #cmake配置
#<exec_depend>ros2launch</exec_depend> <!--package.xml配置-->
#from glob import glob #用于setup.py配置多个launch文件
#('share/' + package_name + '/launch', glob('launch/*launch.py')),
#('share/' + package_name + '/launch', glob('launch/*launch.xml')),
#('share/' + package_name + '/launch', glob('launch/*launch.yaml')),
#(os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
# 封装终端指令相关类--------------
# from launch.actions import ExecuteProcess
# from launch.substitutions import FindExecutable   #FindExecutable(name="ros2")
# 参数声明与获取-----------------
# from launch.actions import DeclareLaunchArgument
# from launch.substitutions import LaunchConfiguration
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
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import Command
# 组件相关-------------
# from launch_ros.actions import ComposableNodeContainer
# from launch_ros.descriptions import ComposableNode

"""
    用于拍摄照片展示用
"""

def generate_launch_description():
    ld = LaunchDescription()

    use_joint_state_gui_arg = DeclareLaunchArgument(
        'use_joint_state_gui',
        default_value='true',
        description='Use joint_state_publisher_gui instead of joint_state_publisher'
    )
    use_joint_state_gui = LaunchConfiguration('use_joint_state_gui')

    default_hip_joint_position_arg = DeclareLaunchArgument(
        'default_hip_joint_position',
        default_value='0.363',
        description='Default position for all hip joints when publishing joint states'
    )
    default_hip_joint_position = ParameterValue(
        LaunchConfiguration('default_hip_joint_position'),
        value_type=float
    )

    p_value = ParameterValue(value=Command(["xacro ",get_package_share_directory('agibot_d1_top_description') + '/urdf/edu_top.urdf.xacro']),value_type=str)
    robot_state_pub = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': p_value}]
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        parameters=[{
            'zeros.FL_HIP_JOINT': default_hip_joint_position,
            'zeros.FR_HIP_JOINT': default_hip_joint_position,
            'zeros.RR_HIP_JOINT': default_hip_joint_position,
            'zeros.RL_HIP_JOINT': default_hip_joint_position,
        }],
        condition=UnlessCondition(use_joint_state_gui)
    )

    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        parameters=[{
            'zeros.FL_HIP_JOINT': default_hip_joint_position,
            'zeros.FR_HIP_JOINT': default_hip_joint_position,
            'zeros.RR_HIP_JOINT': default_hip_joint_position,
            'zeros.RL_HIP_JOINT': default_hip_joint_position,
        }],
        condition=IfCondition(use_joint_state_gui)
    )

    ld.add_action(use_joint_state_gui_arg)
    ld.add_action(default_hip_joint_position_arg)
    ld.add_action(robot_state_pub)
    ld.add_action(joint_state_publisher)
    ld.add_action(joint_state_publisher_gui)

    return ld



