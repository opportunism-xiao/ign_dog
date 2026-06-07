基于智元分支的仿真环境,使用苏研院定制AGIBOT上装,实现导航仿真
===
## 使用方式
- 克隆本仓库
```bash
git clone https://github.com/chiway-luo/ign_robot_dog.git -b ign_agibot_d1_SuZhouResearchInstituteUpperClothing
```
- 安装依赖
```
sudo apt install -y \
  ros-humble-ros-gz \
  ros-humble-gz-ros2-control \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-cartographer-ros \
  ros-humble-robot-localization \
  ros-humble-rviz2 \
  ros-humble-tf2-ros \
  ros-humble-robot-state-publisher \
  ros-humble-xacro \
  ros-humble-joint-state-publisher \
  ros-humble-joint-state-publisher-gui \
  ros-humble-ros2launch
```

- ign_gazebo节点 + 导航(包含cartographer)
```
ros2 launch sim_ign_dog d1_gazebo_sim_dog_nav2.launch.py 
```
> 考虑到稳定性启动的问题,按依赖启动耗时较长(预计10s),请耐心等待;如启动失败请调节urdf中的激光雷达线束数量
- [urdf 第1019行](src/sim_dog/edu_description/urdf/edu.urdf)


- 控制节点(没必要,除非需要手动控制机器狗)
```
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
![](.docs/image.png)

如果需要只使用改仿真环境,不使用导航等功能,可以直接运行
```bash
ros2 launch sim_ign_dog d1_gazebo_sim_dog.launch.py 
```
## 参考仓库
- [anujjain-dev/unitree-go2-ros2](https://github.com/anujjain-dev/unitree-go2-ros2.git)

- [chvmp/champ](https://github.com/chvmp/champ.git)

## 开发参考
- 基坐标系 base_link
- 雷达坐标系 laser_up

## 问题描述

> 当前在部分环境下,由于显卡与ign_gazebo的兼容性问题,会导致仿真环境无法正常启动,导致虚拟机崩溃

### 解决方案
参考 [ssh端口转发](https://github.com/chiway-luo/ssh-x11-forwarding-guide.git) , 将仿真环境部署在远程服务器上,通过ssh连接进行仿真环境的使用

## 二次开发建议

简化urdf的碰撞文件,可以极大减小控制器的加载时间,降低因为性能原因的启动失败问题