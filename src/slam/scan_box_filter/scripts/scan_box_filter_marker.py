#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker


class ScanBoxFilterMarker(Node):

    def __init__(self):
        super().__init__('scan_box_filter_marker')

        # 这里的六个边界参数要和 LaserScanBoxFilter 的过滤盒子保持一致。
        # 含义是在 box_frame 坐标系下：
        #   x 轴范围 [min_x, max_x]
        #   y 轴范围 [min_y, max_y]
        #   z 轴范围 [min_z, max_z]
        # LaserScanBoxFilter 用这些 min/max 判断点是否落在盒子里；
        # 本脚本只是把同一个盒子画到 RViz 里，方便确认过滤范围。
        self.box_frame = self.declare_parameter('box_frame', 'laser_up').value
        self.min_x = self.declare_parameter('min_x', -0.25).value
        self.max_x = self.declare_parameter('max_x', 0.25).value
        self.min_y = self.declare_parameter('min_y', -0.20).value
        self.max_y = self.declare_parameter('max_y', 0.20).value
        self.min_z = self.declare_parameter('min_z', -0.05).value
        self.max_z = self.declare_parameter('max_z', 0.05).value
        self.marker_topic = self.declare_parameter(
            'marker_topic',
            '/scan_box_filter/box_marker',
        ).value
        self.publish_rate = self.declare_parameter('publish_rate', 5.0).value

        self.publisher = self.create_publisher(Marker, self.marker_topic, 1)

        # publish_rate 是 Hz，Timer 需要的是周期秒数。
        # max(..., 0.1) 用来避免参数被写成 0 或负数时出现除零。
        timer_period = 1.0 / max(float(self.publish_rate), 0.1)
        self.timer = self.create_timer(timer_period, self.publish_marker)

        self.get_logger().info(
            f'Publishing scan box marker on {self.marker_topic} in frame {self.box_frame}'
        )

    def publish_marker(self):
        marker = Marker()
        marker.header.stamp = self.get_clock().now().to_msg()
        # Marker 会被画在 box_frame 坐标系下；这里必须和过滤器的 box_frame 一致，
        # 否则 RViz 中看到的盒子位置会和真正过滤的位置不一致。
        marker.header.frame_id = self.box_frame
        marker.ns = 'scan_box_filter'
        marker.id = 0
        marker.type = Marker.CUBE
        marker.action = Marker.ADD

        # LaserScanBoxFilter 的参数是盒子的最小/最大边界；
        # 但 RViz 的 CUBE Marker 不接收 min/max，它需要：
        #   pose.position = 盒子中心点
        #   scale = 盒子在 x/y/z 方向上的完整长度
        #
        # 例如 x 方向范围是 [-0.25, 0.25]：
        #   中心 x = (-0.25 + 0.25) / 2 = 0
        #   长度 x = 0.25 - (-0.25) = 0.5
        marker.pose.position.x = (self.min_x + self.max_x) * 0.5
        marker.pose.position.y = (self.min_y + self.max_y) * 0.5
        marker.pose.position.z = (self.min_z + self.max_z) * 0.5
        # 单位四元数，表示盒子不旋转，直接按 box_frame 的 x/y/z 轴对齐。
        marker.pose.orientation.w = 1.0

        # scale 是 CUBE 的边长，不是半径，也不是从原点到边界的距离。
        # 给一个最小值 0.001，避免 min/max 相等或写反时 RViz 因尺寸 <= 0 而不显示。
        # 如果这里触发最小值，只是为了让 Marker 仍然可见，实际过滤参数仍应检查。
        marker.scale.x = max(self.max_x - self.min_x, 0.001)
        marker.scale.y = max(self.max_y - self.min_y, 0.001)
        marker.scale.z = max(self.max_z - self.min_z, 0.001)

        # 半透明橙红色：alpha 越小越透明，便于同时看到盒子里的激光点/机器人模型。
        marker.color.r = 1.0
        marker.color.g = 0.2
        marker.color.b = 0.0
        marker.color.a = 0.35
        # Marker 1 秒后自动过期；节点按 publish_rate 反复发布，所以正常运行时会持续显示。
        # 如果节点停止，旧 Marker 会自动从 RViz 消失。
        marker.lifetime.sec = 1

        self.publisher.publish(marker)


def main(args=None):
    rclpy.init(args=args)
    node = ScanBoxFilterMarker()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
