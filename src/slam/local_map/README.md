# local_map

本包提供两个 launch：

- `map_save.launch.py`：启动 `nav2_map_server/map_saver_cli`，将 `/map` 保存到工作空间 `map/local_map`。
- `map_server.launch.py`：启动 `nav2_map_server/map_server`，加载工作空间 `map/local_map.yaml`。

默认地图路径：

```bash
/home/chiway/work_temp/ign_Agibot_d1_SuzhouResearchInstituteUpperClothing/map/local_map.yaml
/home/chiway/work_temp/ign_Agibot_d1_SuzhouResearchInstituteUpperClothing/map/local_map.pgm
```

## 直接使用 map_saver_cli 保存地图

在工作空间根目录执行：

```bash
mkdir -p map
source install/setup.bash

ros2 run nav2_map_server map_saver_cli \
  -t /map \
  -f "$(pwd)/map/local_map" \
  --occ 0.65 \
  --free 0.25 \
  --fmt pgm \
  --mode trinary \
  --ros-args -p use_sim_time:=true
```

执行成功后会生成：

```bash
map/local_map.yaml
map/local_map.pgm
```

## 使用 launch 保存地图

在工作空间根目录执行：

```bash
mkdir -p map
source install/setup.bash
ros2 launch local_map map_save.launch.py
```

## 加载保存后的地图

```bash
source install/setup.bash
ros2 launch local_map map_server.launch.py
```

如需修改加载路径，直接改 `params/map_server.yaml` 中的 `yaml_filename`。
