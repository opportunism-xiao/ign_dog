cmake_minimum_required(VERSION 3.8)
project(pointcloud_to_laserscan)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)

add_executable(pointcloud_to_laserscan_node src/pointcloud_to_laserscan_node.cpp)
target_compile_features(pointcloud_to_laserscan_node PUBLIC cxx_std_17)
ament_target_dependencies(pointcloud_to_laserscan_node
  rclcpp
  sensor_msgs
)

install(TARGETS pointcloud_to_laserscan_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY launch params
  DESTINATION share/${PROJECT_NAME}
)

install(FILES README.md
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
