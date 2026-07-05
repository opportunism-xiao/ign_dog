# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ROS 2 Humble quadruped robot dog simulation using Ignition Gazebo, with a custom AGIBOT D1 upper body (苏研院定制上装). Uses the CHAMP framework for quadruped locomotion control and Nav2 for autonomous navigation.

## Build & Run

```bash
# Build
colcon build --symlink-install
source install/setup.bash

# Offline localization mode (pre-built map + AMCL + Nav2)
ros2 launch sim_ign_dog d1_gazebo_sim_dog_nav2_local.launch.py

# Online SLAM mode (Cartographer + Nav2)
ros2 launch sim_ign_dog d1_gazebo_sim_dog_nav2_online.launch.py

# Simulation only (no navigation)
ros2 launch sim_ign_dog d1_gazebo_sim_dog.launch.py

# Save map after SLAM
ros2 launch local_map map_save.launch.py

# Test: send a navigation goal
ros2 run pub_nav_goal pub_point --ros-args -p goal_x:=7.0 -p goal_y:=-1.0 -p goal_yaw:=0.0

# Manual teleop
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Architecture

### Package Hierarchy (`src/`)

| Directory | Purpose |
|---|---|
| `sim_dog/sim_ign_dog/` | **Main entry point** — top-level launch files, RViz configs, Gazebo worlds |
| `sim_dog/agibot_d1_top_description/` | Custom AGIBOT D1 upper body URDF/XACRO model |
| `sim_dog/edu_description/` | Base EDU quadruped robot description |
| `edu_config/` | Robot-specific config (gait, joints, links) — forked from champ_config |
| `nav2/sim_navigation2/` | Nav2 parameter YAMLs, behavior tree XMLs, navigation launch files |
| `nav2/pub_nav_goal/` | Test node: publishes a single NavigateToPose action goal |
| `slam/pointcloud_to_laserscan/` | Custom C++ node: multi-line PointCloud2 → single LaserScan slice |
| `slam/scan_box_filter/` | LaserScanBoxFilter config + Python marker viz node for RViz |
| `slam/slam_cartographer/` | Cartographer SLAM launch/config |
| `slam/local_map/` | Map server and map saver launch files |
| `champ/` | CHAMP quadruped control framework (vendored C++ library) |
| `FAST_LIO/`, `livox_*/`, `Livox-SDK2/` | Third-party: LiDAR odometry and Livox drivers |

### Robot Model Assembly (XACRO)

The robot model is assembled by `edu_top.urdf.xacro` which composes two URDFs:

```
edu.urdf (base quadruped: 13 links, 12 revolute joints — 3DOF per leg)
    │
    + fixed joint "edu_to_top_bridge" (xyz="-0.009 0 0.0748")
    │
top.urdf (AGIBOT D1 upper body: base_link_top, camera, laser, laser_up, front_camera)
```

The combined model is loaded at runtime by `sim_display_launch.py` via `robot_state_publisher` which calls `xacro` to process `edu_top.urdf.xacro`. The resulting `/robot_description` topic is used by both Gazebo (to spawn the model) and CHAMP (to read URDF for kinematics).

All sensors are defined in `top.urdf` (not in the base `edu.urdf`):
- **Multi-line GPU lidar** (`laser_up` frame): 640×32 beams, 10Hz, 0.08–20m range, publishes `/scan/points` (PointCloud2) and `/scan` (native single-line LaserScan)
- **Depth camera** (`front_camera` frame): 256×256, 10Hz, publishes `/depth_camera` (Image) and `/depth_camera/points` (PointCloud2)
- **RGB camera** (`front_camera` frame): 320×240, 20Hz, publishes `/image_raw` and `/camera_info`
- **IMU** (`base_link_top` frame): 200Hz, publishes `imu` topic — **added 2026-07**; currently bridged only in `d1_gazebo_sim_dog.launch.py` (sim-only), NOT in the nav launch files (missing from `ros_gz_bridge` arguments there)

### Three Main Launch Files: Differences

| Feature | `d1_gazebo_sim_dog` | `_nav2_local` | `_nav2_online` |
|---|---|---|---|
| World | `slam_house.sdf` | `house_add.sdf` | `house_add.sdf` |
| Gazebo + robot model + CHAMP | ✓ | ✓ | ✓ |
| ros_gz_bridge sensors | ✓ (+IMU) | ✓ (no IMU) | ✓ (no IMU) |
| RViz2 | ✓ | ✓ | ✓ |
| PointCloud→LaserScan pipeline | ✗ | ✓ | ✓ |
| Scan box filter | ✗ | ✓ | ✓ |
| Cartographer SLAM | ✗ | ✗ | ✓ |
| Map server + AMCL | ✗ | ✓ | ✗ |
| Nav2 pipeline | ✗ | ✓ | ✓ |

All three use `ros_gz_bridge` for: `/cmd_vel` (ROS→GZ), `/clock` (GZ→ROS), odometry (`/model/d1_dog/odometry`→`/odom/ign`), lidars, depth camera, and camera.

### Custom Nodes (code you own)

- **`pointcloud_to_laserscan`** (`src/slam/pointcloud_to_laserscan/src/pointcloud_to_laserscan_node.cpp`): Subscribes to PointCloud2, extracts points within a Z-height slice, projects to a 2D LaserScan by angle. Configurable via ROS params (input/output topics, height slice, angle range, range limits).

- **`pub_nav_goal`** (`src/nav2/pub_nav_goal/src/pub_point.cpp`): Sends a single Nav2 `NavigateToPose` action goal with configurable x/y/yaw. Monitors feedback and result, then shuts down. Serves as an informal Nav2 smoke test.

- **`scan_box_filter_marker`** (`src/slam/scan_box_filter/scripts/scan_box_filter_marker.py`): Publishes a semi-transparent CUBE Marker to RViz visualizing the box filter region. Parameters must match the `laser_filters/LaserScanBoxFilter` config. The filter box is in the `laser_up` frame, centered around the robot body (x: [-0.25, 0.25], y: [-0.2, 0.2], z: [-0.5, 0.05]).

### Sensor Data Pipeline

```
/scan/points  (Ignition multi-line lidar PointCloud2)
    │
    ▼  pointcloud_to_laserscan
/scan/points_to_scan  (single LaserScan)
    │
    ▼  scan_box_filter (laser_filters/LaserScanBoxFilter)
/scan/filtered  (body-occlusion-filtered LaserScan)
    │
    ├── Nav2 costmaps (local + global)
    ├── Cartographer (SLAM mode)
    └── AMCL (localization mode)
```

Additional sensors bridged from Ignition via `ros_gz_bridge`: `/scan` (native single-line lidar), `/depth_camera`, `/depth_camera/points`, `/image_raw`, `/camera_info`, `/imu` (note: IMU bridge is only in the sim-only launch — the nav launches are missing it).

### TF Tree

```
odom ──► d1_dog/odom ──► d1_dog/base_footprint ──► base_link ──► sensors (laser_up, front_camera, etc.)
                            │
                            └── base_footprint  (identity link, used by Nav2)
```

The `d1_dog/` namespace prefix comes from Ignition's model naming. Static transforms bridge `odom` ↔ `d1_dog/odom` and `d1_dog/base_footprint` ↔ `base_link` (z=0.25 offset). A commented-out `d1_base_footprint_to_base_link_tf` exists in the launch files that would bridge `d1_dog/base_footprint` ↔ `base_footprint`.

### CHAMP Control Stack

CHAMP provides quadruped locomotion (gait generation, leg kinematics, state estimation). Configured via:
- `edu_config/config/gait/gait.yaml` — gait parameters
- `edu_config/config/joints/joints.yaml` — joint name mapping
- `edu_config/config/links/links.yaml` — link name mapping
- `edu_config/config/ros2_control/d1_controllers.yaml` — controller definitions (joint_state_broadcaster, legs_controller)

**CHAMP bringup nodes** (via `champ_bringup/launch/bringup.launch.py`):
1. `quadruped_controller_node` (champ_base) — gait generation, leg IK, publishes joint trajectory commands to `legs_controller/joint_trajectory`. Subscribes to `/cmd_vel` (remapped from `/cmd_vel/smooth`).
2. `state_estimation_node` (champ_base) — odometry from leg kinematics, publishes `/tf` (odom→base_link if `publish_odom_tf` is true, which it isn't in this project).
3. `footprint_to_odom_ekf` (robot_localization) — EKF fusing cmd_vel + IMU, publishes `/odom` TF. **Enabled** in this project.
4. `base_to_footprint_ekf` (robot_localization) — would publish `/base_footprint` TF. **Disabled** in this project.

Controllers are spawned sequentially via `ros2_control`: `joint_state_broadcaster` → `legs_controller`. CHAMP bringup launches after controllers are ready (sequenced via `OnProcessExit` event handlers with timer delays to avoid race conditions).

### Navigation Modes

**Local mode** (`nav2_local_map.launch.py`): `map_server` (loads `map/local_map.yaml`) + `amcl` + full Nav2 pipeline (planner, controller, smoother, velocity_smoother, behavior_server, waypoint_follower, bt_navigator). Uses BT XMLs from `src/nav2/sim_navigation2/bts/`.

**Online mode** (`nav2_online_map.launch.py`): Same Nav2 pipeline but without map_server/amcl; Cartographer provides the map via `/map` topic.

**Behavior tree XMLs:**
- `nav2_pose.xml` — NavigateToPose: replan at 20Hz, recovery fallback (clear costmaps → spin → wait → backup), max 6 retries
- `nav2_poses.xml` — NavigateThroughPoses: same structure with ComputePathThroughPoses and RemovePassedGoals

### Velocity Smoothing Chain

```
controller_server → /raw_cmd_vel → velocity_smoother → /cmd_vel → ros_gz_bridge → Gazebo
                                                              └── quadruped_controller_node (CHAMP)
```

The smoothed `/cmd_vel` goes to **both** Gazebo (for physics) and CHAMP's `quadruped_controller_node` (for gait generation).

## Key Configuration Files

- Offline map: `map/local_map.yaml` (references `map/local_map.pgm`)
- Nav2 params: `src/nav2/sim_navigation2/params/*.yaml`
- Behavior trees: `src/nav2/sim_navigation2/bts/nav2_pose.xml`, `nav2_poses.xml`
- AMCL: `src/nav2/sim_navigation2/params/amcl.yaml`
- Costmaps: `src/nav2/sim_navigation2/params/{local,global}_costmap.yaml`
- PointCloud→LaserScan: `src/slam/pointcloud_to_laserscan/params/pointcloud_to_laserscan.yaml`
- Box filter: `src/slam/scan_box_filter/params/scan_box_filter.yaml`
- Cartographer: `src/slam/slam_cartographer/params/dog.lua` (2D), `dog_3d.lua` (3D)
- Map server/saver: `src/slam/local_map/params/*.yaml`
- Top-level Nav2 params (orphaned, not loaded at runtime): `nav2_params.yaml` (root)
- World files: `src/sim_dog/sim_ign_dog/world/` (`house.sdf` walls only; `house_add.sdf` with furniture; `slam_house.sdf` with furniture for SLAM)

## Important Notes

- Robot model uses `base_link` as the base frame (not `base_footprint`). A static transform publishes `base_link` at z=0.25 above `d1_dog/base_footprint`.
- `IGN_GAZEBO_RESOURCE_PATH` is set in launch files to include `ign_models/`, `edu_description/share`, and `agibot_d1_top_description/share` for model loading.
- Gazebo model is spawned via `ros_gz_sim create` with a 2s delay to avoid race conditions with Gazebo startup.
- `nav2_params.yaml` at the repo root is a standalone reference file — it is ORPHANED and NOT loaded at runtime. Actual Nav2 params are loaded from `sim_navigation2/params/`.
- The `livox_ros_driver2` and `Livox-SDK2` are third-party dependencies for Livox LiDAR support. `FAST_LIO` provides lidar-inertial odometry but is not wired into the main navigation pipeline.
- `champ_gazebo/scripts/imu_sensor.py` is leftover ROS 1 code (imports `rospy`); the actual IMU is bridged from Ignition via `ros_gz_bridge`.
- There are no unit or integration tests. All packages declare only `ament_lint_auto`/`ament_lint_common` as test dependencies (linting-only). `pub_nav_goal` serves as an informal integration smoke test for Nav2.
- Startup is slow (~10s) due to sequential controller spawning with delays. If the simulation fails to start, try reducing the LiDAR beam count in the URDF.
- `edu_config/launch/` files reference old `go2_config`/`go2_description` package names — these are STALE and not the active entry points. Use the launch files in `sim_ign_dog/` instead.
- Compile-time gait config in `edu_config/include/gait_config.h` (ODOM_SCALER 1.25, MAX_LINEAR_VEL_X 0.5) DIFFERS from the runtime YAML in `edu_config/config/gait/gait.yaml` (odom_scaler: 0.9, max_linear_velocity_x: 1.0). The YAML values take precedence at runtime.
