#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker


class ScanBoxFilterMarker(Node):

    def __init__(self):
        super().__init__('scan_box_filter_marker')

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
        timer_period = 1.0 / max(float(self.publish_rate), 0.1)
        self.timer = self.create_timer(timer_period, self.publish_marker)

        self.get_logger().info(
            f'Publishing scan box marker on {self.marker_topic} in frame {self.box_frame}'
        )

    def publish_marker(self):
        marker = Marker()
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.header.frame_id = self.box_frame
        marker.ns = 'scan_box_filter'
        marker.id = 0
        marker.type = Marker.CUBE
        marker.action = Marker.ADD

        marker.pose.position.x = (self.min_x + self.max_x) * 0.5
        marker.pose.position.y = (self.min_y + self.max_y) * 0.5
        marker.pose.position.z = (self.min_z + self.max_z) * 0.5
        marker.pose.orientation.w = 1.0

        marker.scale.x = max(self.max_x - self.min_x, 0.001)
        marker.scale.y = max(self.max_y - self.min_y, 0.001)
        marker.scale.z = max(self.max_z - self.min_z, 0.001)

        marker.color.r = 1.0
        marker.color.g = 0.2
        marker.color.b = 0.0
        marker.color.a = 0.35
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
