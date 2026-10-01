
#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped

import numpy as np


class ObstacleAvoidNode(Node):

    def __init__(self):
        super().__init__('obstacle_avoider')

        self.laser_reading = None

        self.laser_subs_ = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        self.cmdvel_pub_ = self.create_publisher(
            TwistStamped,
            '/wheel_controller/cmd_vel',
            10
        )

        self._timer_ = self.create_timer(
            0.1,
            self.move_straight
        )

        self.get_logger().info("Obstacle avoider started")

    def scan_callback(self, msg):

        ranges = np.array(msg.ranges)

        # Convert each LiDAR index to its actual angle
        angles = (
            msg.angle_min
            + np.arange(len(ranges)) * msg.angle_increment
        )

        # Replace invalid readings with NaN
        valid = (
            np.isfinite(ranges)
            & (ranges >= msg.range_min)
            & (ranges <= msg.range_max)
        )

        ranges[~valid] = np.nan

        # Convert angles to degrees
        angles_deg = np.degrees(angles)

        def sector_mean(start, end):
            mask = (
                (angles_deg >= start)
                & (angles_deg <= end)
            )

            values = ranges[mask]

            if np.all(np.isnan(values)):
                return float('inf')

            return float(np.nanmean(values))

        # Front: -20 to +20 degrees
        front = sector_mean(-20, 20)

        # Left-front: 20 to 60 degrees
        left_front = sector_mean(20, 60)

        # Left: 60 to 90 degrees
        left = sector_mean(60, 90)

        # Right: -90 to -60 degrees
        right = sector_mean(-90, -60)

        # Right-front: -60 to -20 degrees
        right_front = sector_mean(-60, -20)

        self.laser_reading = [
            front,
            left_front,
            left,
            right,
            right_front
        ]

    def move_straight(self):

        cmd_vel = TwistStamped()
        cmd_vel.header.stamp = self.get_clock().now().to_msg()
        cmd_vel.header.frame_id = 'base_link'

        # Wait until the first LiDAR message arrives
        if self.laser_reading is None:
            self.cmdvel_pub_.publish(cmd_vel)
            return

        front, left_front, left, right, right_front = (
            self.laser_reading
        )

        threshold = 1.5

        # Obstacle directly ahead
        if front <= threshold:

            self.get_logger().info(
                f"Front obstacle: {front:.2f} m. Turning right"
            )

            cmd_vel.twist.linear.x = 0.0
            cmd_vel.twist.angular.z = -0.34

        # Obstacle on left-front or left
        elif left_front <= threshold or left <= threshold:

            self.get_logger().info(
                "Obstacle on left. Turning right"
            )

            cmd_vel.twist.linear.x = 0.0
            cmd_vel.twist.angular.z = -0.34

        # Obstacle on right-front or right
        elif right_front <= threshold or right <= threshold:

            self.get_logger().info(
                "Obstacle on right. Turning left"
            )

            cmd_vel.twist.linear.x = 0.0
            cmd_vel.twist.angular.z = 0.34

        # No obstacle in monitored sectors
        else:

            cmd_vel.twist.linear.x = 0.3
            cmd_vel.twist.angular.z = 0.0

        self.cmdvel_pub_.publish(cmd_vel)


def main(args=None):

    rclpy.init(args=args)

    node = ObstacleAvoidNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
