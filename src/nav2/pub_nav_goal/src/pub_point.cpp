#include <cmath>
#include <functional>
#include <memory>
#include <string>

#include "geometry_msgs/msg/quaternion.hpp"
#include "nav2_msgs/action/navigate_to_pose.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"

/*
    需求: 发布一次导航航点,并持续接收导航反馈
    流程:
        1.包含头文件
        2.初始化ros2客户端
        3.自定义节点类 
            3-1.声明并读取航点参数
            3-2.创建NavigateToPose动作客户端
            3-3.等待服务端就绪后发送一次航点
            3-4.通过反馈回调连续接收导航状态
            3-5.通过结果回调接收导航结果
        4.调用spin函数,并传入节点对象指针
        5.释放资源
*/

using namespace std::chrono_literals; //使用时间命名空间
using namespace std::placeholders; //占位符命名空间

class PubPointNode : public rclcpp::Node
{
public:
  using NavigateToPose = nav2_msgs::action::NavigateToPose;
  using GoalHandleNavigateToPose = rclcpp_action::ClientGoalHandle<NavigateToPose>;

  PubPointNode(std::string str1): Node(str1)
  {
    RCLCPP_INFO(this->get_logger(), "namespace:  node: %s 节点创建成功", str1.c_str());

    action_name_ = this->declare_parameter<std::string>("action_name", "navigate_to_pose");
    frame_id_ = this->declare_parameter<std::string>("frame_id", "map");
    goal_x_ = this->declare_parameter<double>("goal_x", 0.0);
    goal_y_ = this->declare_parameter<double>("goal_y", 0.0);
    goal_yaw_ = this->declare_parameter<double>("goal_yaw", 0.0);
    behavior_tree_ = this->declare_parameter<std::string>("behavior_tree", "");

    nav_to_pose_client_ = rclcpp_action::create_client<NavigateToPose>(this, action_name_);

    timer_ = this->create_wall_timer(500ms, std::bind(&PubPointNode::send_goal_once, this));

    RCLCPP_INFO(
      this->get_logger(),
      "等待动作服务端: %s, 航点参数 frame_id=%s x=%.3f y=%.3f yaw=%.3f",
      action_name_.c_str(),
      frame_id_.c_str(),
      goal_x_,
      goal_y_,
      goal_yaw_);
  }

private:
  //四元数转换函数
  geometry_msgs::msg::Quaternion yaw_to_quaternion(double yaw)
  {
    geometry_msgs::msg::Quaternion quaternion;
    quaternion.x = 0.0;
    quaternion.y = 0.0;
    quaternion.z = std::sin(yaw * 0.5);
    quaternion.w = std::cos(yaw * 0.5);
    return quaternion;
  }

  //发送一次航点
  void send_goal_once()
  {
    if (goal_sent_) {
      return;
    }

    if (!nav_to_pose_client_->action_server_is_ready()) {
      RCLCPP_INFO_THROTTLE(
        this->get_logger(),
        *this->get_clock(),
        2000,
        "动作服务端 %s 未就绪,继续等待...",
        action_name_.c_str());
      return;
    }

    goal_sent_ = true;
    timer_->cancel();

    NavigateToPose::Goal goal_msg;
    goal_msg.pose.header.stamp = this->now();
    goal_msg.pose.header.frame_id = frame_id_;
    goal_msg.pose.pose.position.x = goal_x_;
    goal_msg.pose.pose.position.y = goal_y_;
    goal_msg.pose.pose.position.z = 0.0;
    goal_msg.pose.pose.orientation = yaw_to_quaternion(goal_yaw_);
    goal_msg.behavior_tree = behavior_tree_;

    auto send_goal_options = rclcpp_action::Client<NavigateToPose>::SendGoalOptions();
    send_goal_options.goal_response_callback =
      std::bind(&PubPointNode::goal_response_callback, this, _1);
    send_goal_options.feedback_callback =
      std::bind(&PubPointNode::feedback_callback, this, _1, _2);
    send_goal_options.result_callback =
      std::bind(&PubPointNode::result_callback, this, _1);

    nav_to_pose_client_->async_send_goal(goal_msg, send_goal_options);

    RCLCPP_INFO(
      this->get_logger(),
      "已发布一次导航航点: frame_id=%s x=%.3f y=%.3f yaw=%.3f",
      frame_id_.c_str(),
      goal_x_,
      goal_y_,
      goal_yaw_);
  }

  //目标响应回调函数
  void goal_response_callback(const GoalHandleNavigateToPose::SharedPtr & goal_handle)
  {
    if (!goal_handle) {
      RCLCPP_ERROR(this->get_logger(), "导航航点被动作服务端拒绝");
      rclcpp::shutdown();
      return;
    }

    RCLCPP_INFO(this->get_logger(), "导航航点已被动作服务端接收");
  }

  //连续反馈回调函数
  void feedback_callback(
    GoalHandleNavigateToPose::SharedPtr,
    const std::shared_ptr<const NavigateToPose::Feedback> feedback)
  {
    RCLCPP_INFO(
      this->get_logger(),
      "导航反馈: 当前位姿(%.3f, %.3f), 剩余距离 %.3f m, 已用时 %d s, 预估剩余 %d s, 恢复次数 %d",
      feedback->current_pose.pose.position.x,
      feedback->current_pose.pose.position.y,
      feedback->distance_remaining,
      feedback->navigation_time.sec,
      feedback->estimated_time_remaining.sec,
      feedback->number_of_recoveries);
  }

  //结果回调函数
  void result_callback(const GoalHandleNavigateToPose::WrappedResult & result)
  {
    switch (result.code) {
      case rclcpp_action::ResultCode::SUCCEEDED:
        RCLCPP_INFO(this->get_logger(), "导航任务执行成功");
        break;
      case rclcpp_action::ResultCode::ABORTED:
        RCLCPP_ERROR(this->get_logger(), "导航任务被中止");
        break;
      case rclcpp_action::ResultCode::CANCELED:
        RCLCPP_WARN(this->get_logger(), "导航任务被取消");
        break;
      default:
        RCLCPP_ERROR(this->get_logger(), "导航任务返回未知结果");
        break;
    }

    rclcpp::shutdown();
  }

  std::string action_name_;
  std::string frame_id_;
  std::string behavior_tree_;
  double goal_x_;
  double goal_y_;
  double goal_yaw_;
  bool goal_sent_ = false;

  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp_action::Client<NavigateToPose>::SharedPtr nav_to_pose_client_;
};

int main(int argc, char * argv[])
{
  //初始化ros2客户端
  rclcpp::init(argc, argv);

  //调用spin函数,使用自定义类对象指针
  rclcpp::spin(std::make_shared<PubPointNode>("pub_point_node_cpp"));  //node_name, (namespace可选)

  //释放资源
  rclcpp::shutdown();
  return 0;
}
