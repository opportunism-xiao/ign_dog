# scan_box_filter

存放 Humble 自带 `laser_filters/LaserScanBoxFilter` 的盒子过滤参数和启动文件。

默认订阅 `/scan/points_to_scan`，发布 `/scan/filtered`：

```bash
ros2 launch scan_box_filter scan_box_filter.launch.py
```

盒子范围在 `params/scan_box_filter.yaml` 中调整，`invert: false` 表示剔除盒子内部的点。
`LaserScanBoxFilter` 需要同时设置 `min_z` 和 `max_z`；LaserScan 投影点通常在 z=0
附近，不能把 z 范围设置成 0 到 0。

启动文件会同时发布 RViz marker：

```bash
ros2 launch scan_box_filter scan_box_filter.launch.py
```

在 RViz 中添加 `Marker` 显示，话题选择 `/scan_box_filter/box_marker`。
