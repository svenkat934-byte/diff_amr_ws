#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped

import numpy as np 

class WallFollowingNode(Node):
    def __init__(self):
        super().__init__('wall_follower')

        self.laser_reading = None

        self.laser_subs_ = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)

        self.cmdvel_pub_ = self.create_publisher(TwistStamped, '/wheel_controller/cmd_vel', 10)

        self._timer_ = self.create_timer(0.1, self.move_along_with_wall)

        self.get_logger().info("Wall Follwer Started")

    def scan_callback(self, msg):
        ranges = np.array(msg.ranges)

        # Convert each LiDAR index to its actual angle
        angles = (msg.angle_min + np.arange(len(ranges)) * msg.angle_increment)

        # Replace invalid readings with NaN
        valid = ( np.isfinite(ranges) & (ranges >= msg.range_min) & (ranges <= msg.range_max))

        ranges[~valid] = np.nan

        # Convert angles to degrees
        angles_deg = np.degrees(angles)

        def sector_mean(start, end):
            mask = ( 
                (angles_deg >=  start)
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


    def move_along_with_wall(self):

        cmd_vel = TwistStamped()
        cmd_vel.header.stamp = self.get_clock().now().to_msg()
        cmd_vel.header.frame_id = 'base_link'

        # Wait until the LiDAR message arrvives
        if self.laser_reading is None:
            self.cmdvel_pub_.publish(cmd_vel)
            return 

        front, left_front, left, right, right_front = (
                    self.laser_reading
                )

        threshold = 0.5

        cmd_vel.twist.linear.x = 0.5
        cmd_vel.twist.angular.z = 0.0

        # condition if amr_bot is detect robot in front
        if (front <= 1.0 or right_front < threshold or left_front > threshold ):
            # condition if amr_bot has detect obstactle at front_right is increaseing distance
            if (right_front < threshold or left_front > threshold):
                 if ((right <= threshold ) or (left >= threshold )):
                    cmd_vel.twist.linear.x = 0.2
                    cmd_vel.twist.angular.z = 0.5
                
            elif (left_front < threshold or right_front > threshold):
                if ( (left <= threshold ) or (right >= threshold)):
                    cmd_vel.twist.linear.x = 0.2
                    cmd_vel.twist.angular.z = -0.5

            else:
                cmd_vel.twist.linear.x = 0.5
                cmd_vel.twist.angular.z = 0.0

    
        self.cmdvel_pub_.publish(cmd_vel)
        

def main(args=None):
    rclpy.init(args=args)
    node = WallFollowingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__  == "__main__":
    main()
