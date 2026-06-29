#include <algorithm>
#include <cmath>
#include <functional>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"
#include "sensor_msgs/msg/point_cloud2.hpp"
#include "sensor_msgs/point_cloud2_iterator.hpp"

namespace
{
constexpr double kPi = 3.14159265358979323846;

double require_positive(
  const rclcpp::Logger & logger, const std::string & name, double value,
  double fallback)
{
  if (value > 0.0) {
    return value;
  }

  RCLCPP_WARN(
    logger,
    "Parameter '%s' must be positive, got %.6f. Falling back to %.6f.",
    name.c_str(),
    value,
    fallback);
  return fallback;
}
}  // namespace

class PointCloudToLaserScanNode : public rclcpp::Node
{
public:
  PointCloudToLaserScanNode()
  : Node("pointcloud_to_laserscan")
  {
    input_topic_ = declare_parameter<std::string>("input_topic", "/scan/points");
    output_topic_ = declare_parameter<std::string>("output_topic", "/scan/points_to_scan");
    output_frame_id_ = declare_parameter<std::string>("output_frame_id", "");

    min_height_ = declare_parameter<double>("min_height", -0.10);
    max_height_ = declare_parameter<double>("max_height", 0.10);
    angle_min_ = declare_parameter<double>("angle_min", -kPi);
    angle_max_ = declare_parameter<double>("angle_max", kPi);
    angle_increment_ = require_positive(
      get_logger(),
      "angle_increment",
      declare_parameter<double>("angle_increment", 0.0087),
      0.0087);
    scan_time_ = require_positive(
      get_logger(),
      "scan_time",
      declare_parameter<double>("scan_time", 0.10),
      0.10);
    range_min_ = declare_parameter<double>("range_min", 0.20);
    range_max_ = declare_parameter<double>("range_max", 30.0);
    use_inf_ = declare_parameter<bool>("use_inf", true);
    inf_epsilon_ = declare_parameter<double>("inf_epsilon", 1.0);

    if (max_height_ < min_height_) {
      RCLCPP_WARN(
        get_logger(),
        "Parameter 'max_height' is smaller than 'min_height'. Swapping them.");
      std::swap(max_height_, min_height_);
    }
    if (angle_max_ <= angle_min_) {
      RCLCPP_WARN(
        get_logger(),
        "Parameter 'angle_max' must be greater than 'angle_min'. Falling back to [-pi, pi].");
      angle_min_ = -kPi;
      angle_max_ = kPi;
    }
    if (range_max_ <= range_min_) {
      RCLCPP_WARN(
        get_logger(),
        "Parameter 'range_max' must be greater than 'range_min'. Falling back to [0.20, 30.0].");
      range_min_ = 0.20;
      range_max_ = 30.0;
    }

    const auto qos = rclcpp::SensorDataQoS();
    scan_pub_ = create_publisher<sensor_msgs::msg::LaserScan>(output_topic_, qos);
    cloud_sub_ = create_subscription<sensor_msgs::msg::PointCloud2>(
      input_topic_,
      qos,
      std::bind(&PointCloudToLaserScanNode::cloud_callback, this, std::placeholders::_1));

    RCLCPP_INFO(
      get_logger(),
      "Converting PointCloud2 '%s' to LaserScan '%s' with height slice [%.3f, %.3f].",
      input_topic_.c_str(),
      output_topic_.c_str(),
      min_height_,
      max_height_);
  }

private:
  void cloud_callback(const sensor_msgs::msg::PointCloud2::SharedPtr cloud_msg)
  {
    sensor_msgs::msg::LaserScan scan_msg;
    scan_msg.header = cloud_msg->header;
    if (!output_frame_id_.empty()) {
      scan_msg.header.frame_id = output_frame_id_;
    }

    scan_msg.angle_min = static_cast<float>(angle_min_);
    scan_msg.angle_max = static_cast<float>(angle_max_);
    scan_msg.angle_increment = static_cast<float>(angle_increment_);
    scan_msg.time_increment = 0.0F;
    scan_msg.scan_time = static_cast<float>(scan_time_);
    scan_msg.range_min = static_cast<float>(range_min_);
    scan_msg.range_max = static_cast<float>(range_max_);

    const auto range_count =
      static_cast<std::size_t>(std::ceil((angle_max_ - angle_min_) / angle_increment_));
    const float default_range = use_inf_ ?
      std::numeric_limits<float>::infinity() :
      static_cast<float>(range_max_ + inf_epsilon_);
    scan_msg.ranges.assign(range_count, default_range);

    try {
      sensor_msgs::PointCloud2ConstIterator<float> iter_x(*cloud_msg, "x");
      sensor_msgs::PointCloud2ConstIterator<float> iter_y(*cloud_msg, "y");
      sensor_msgs::PointCloud2ConstIterator<float> iter_z(*cloud_msg, "z");

      for (; iter_x != iter_x.end(); ++iter_x, ++iter_y, ++iter_z) {
        const double x = *iter_x;
        const double y = *iter_y;
        const double z = *iter_z;

        if (!std::isfinite(x) || !std::isfinite(y) || !std::isfinite(z)) {
          continue;
        }
        if (z < min_height_ || z > max_height_) {
          continue;
        }

        const double range = std::hypot(x, y);
        if (range < range_min_ || range > range_max_) {
          continue;
        }

        const double angle = std::atan2(y, x);
        if (angle < angle_min_ || angle > angle_max_) {
          continue;
        }

        const auto index = static_cast<std::size_t>((angle - angle_min_) / angle_increment_);
        if (index >= scan_msg.ranges.size()) {
          continue;
        }

        const float range_f = static_cast<float>(range);
        if (!std::isfinite(scan_msg.ranges[index]) || range_f < scan_msg.ranges[index]) {
          scan_msg.ranges[index] = range_f;
        }
      }
    } catch (const std::runtime_error & error) {
      RCLCPP_ERROR_THROTTLE(
        get_logger(),
        *get_clock(),
        5000,
        "Input PointCloud2 must contain float32 fields x, y and z: %s",
        error.what());
      return;
    }

    scan_pub_->publish(scan_msg);
  }

  std::string input_topic_;
  std::string output_topic_;
  std::string output_frame_id_;
  double min_height_;
  double max_height_;
  double angle_min_;
  double angle_max_;
  double angle_increment_;
  double scan_time_;
  double range_min_;
  double range_max_;
  bool use_inf_;
  double inf_epsilon_;

  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr cloud_sub_;
  rclcpp::Publisher<sensor_msgs::msg::LaserScan>::SharedPtr scan_pub_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<PointCloudToLaserScanNode>());
  rclcpp::shutdown();
  return 0;
}
