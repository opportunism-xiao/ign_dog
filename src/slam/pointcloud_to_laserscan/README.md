# pointcloud_to_laserscan

将多线激光雷达 `sensor_msgs/msg/PointCloud2` 按高度切片投影为单线
`sensor_msgs/msg/LaserScan`。

默认订阅 `/scan/points`，发布 `/scan/points_to_scan`：

```bash
ros2 launch pointcloud_to_laserscan pointcloud_to_laserscan.launch.py
```

常用参数：

```bash
ros2 launch pointcloud_to_laserscan pointcloud_to_laserscan.launch.py
```

如果要让只订阅 `/scan` 的建图或导航节点直接使用转换结果，可以启动时设置
参数文件中的 `output_topic: /scan`，并关闭原来的 `/scan` 发布者，避免同一话题出现两个不同来源。

盒子过滤参数和启动文件放在 `scan_box_filter` 功能包中。
