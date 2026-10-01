#!/usr/bin/env python3

import math 
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from sensor_msgs.msg import  Imu
from nav_msgs.msg import Odometry

from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point

class PolygonDrawer(Node):
    def __init__(self):
        super().__init__('polygon_drawer')

        # Default parameters
        self.declare_parameter('polygon_sides', 3)
        self.declare_parameter('side_length', 3.0)

        # getting parameters
        self.polygon_sides = self.get_parameter('polygon_sides').get_parameter_value().integer_value
        self.side_length = self.get_parameter('side_length').get_parameter_value().double_value

        self.create_subscription(Imu, '/imu/out', self.imu_callback, 10)
        self.create_subscription(Odometry, '/wheel_controller/odom', self.odom_callback, 10)

        self.vel_pub = self.create_publisher(TwistStamped, '/wheel_controller/cmd_vel', 10)
        self.marker_pub = self.create_publisher(Marker, '/polygon_marker', 10)

        self.create_timer(0.1, self.control_loop)

        # Robot state variables
        self.current_x = None
        self.current_y = None

        self.start_x = None
        self.start_y = None

        self.current_yaw_pose = None
        self.start_pose = None
        self.state = "WAIT"
        self.sides_drawn = 0

        # Adding Tolerance 
        self.distance_tolerance = 0.01  # meters
        self.angle_tolerance = 0.01  # radians

        # Control gains ( tune for smoothness)
        self.k_linear = 0.5
        self.k_angular = 1.0

        # Speed limits 
        self.max_linear_speed = 1.0  # m/s
        self.max_angular_speed = 1.5  # rad/s


        # marker for visualization
        self.path_marker = Marker()
        self.path_marker.header.frame_id = "odom"
        self.path_marker.ns = "polygon"
        self.path_marker.id = 0

        self.path_marker.type = Marker.LINE_STRIP
        self.path_marker.action = Marker.ADD

        self.path_marker.scale.x = 0.05  # Line width
        self.path_marker.color.a = 1.0  # Alpha
        self.path_marker.color.r = 1.0  # Red
        self.path_marker.color.g = 0.0  # Green
        self.path_marker.color.b = 0.0  # Blue

        self.get_logger().info(f"Polygon Drawer (Closed Loop) Started: sides={self.polygon_sides}, length={self.side_length}")

    def odom_callback(self, msg):

        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        # Add current position to the path marker
        point = Point()
        point.x = self.current_x
        point.y = self.current_y
        point.z = 0.05

        self.path_marker.points.append(point)
        self.path_marker.header.stamp = self.get_clock().now().to_msg()
        self.marker_pub.publish(self.path_marker)

    def imu_callback(self, msg):
        # Convert quaternion to yaw angle
        x = msg.orientation.x
        y = msg.orientation.y
        z = msg.orientation.z
        w = msg.orientation.w
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        self.current_yaw_pose = math.atan2(siny_cosp, cosy_cosp)


    def control_loop(self):

        if self.current_yaw_pose is None:
            return  # Wait until IMU data is available

        if self.current_x is None or self.current_y is None:
            return  # Wait until odometry data is available

    

        # velocity command
        vel_msg = TwistStamped()
        vel_msg.header.stamp = self.get_clock().now().to_msg()
        vel_msg.header.frame_id = 'base_link'

        if self.state == "WAIT":
            # start drawing the polygon
            self.start_x = self.current_x
            self.start_y = self.current_y

            self.start_pose = self.current_yaw_pose
            self.state = "FORWARD"
            
            self.get_logger().info("Starting First Side....")

        elif self.state == "FORWARD":
            # Calculate reamining distance to travel
            distance = math.sqrt((self.current_x - self.start_x) ** 2 + (self.current_y - self.start_y) ** 2)
            error_distance = self.side_length - distance

            if error_distance <= self.distance_tolerance:
                vel_msg.twist.linear.x = 0.0
                self.vel_pub.publish(vel_msg)
                self.start_pose = self.current_yaw_pose
                self.state = "TURN"
                self.get_logger().info(f"side {self.sides_drawn + 1} completed, Turning.....")

            else: 
                # Proportional control for linear speed
                speed = self.k_linear * error_distance
                vel_msg.twist.linear.x = min(speed, self.max_linear_speed)

        elif self.state == "TURN":
            # Calculate target_yaw for next turn 

            turn_start_yaw = self.start_pose

            angle_turned = self.normalize_angle(
                self.current_yaw_pose - turn_start_yaw
            )

            required_turn = (2 * math.pi) / self.polygon_sides

            error_angle = required_turn - angle_turned

            if abs(error_angle) <= self.angle_tolerance:
                vel_msg.twist.angular.z = 0.0
                self.vel_pub.publish(vel_msg)
                self.sides_drawn += 1

                if self.sides_drawn >= self.polygon_sides:
                    self.state = "STOP"
                    self.get_logger().info("Polygon Drawing Completed!")
                   
                else:
                    self.start_pose = self.current_yaw_pose
                    self.start_x = self.current_x
                    self.start_y = self.current_y

                    self.state = "FORWARD"
                    self.get_logger().info(f"Turn completed, starting side {self.sides_drawn + 1}....")
            else:
                # Proportional control for angular speed
                speed = self.k_angular * error_angle
                vel_msg.twist.angular.z = max(min(speed, self.max_angular_speed), -self.max_angular_speed)

        elif self.state == "STOP":
            vel_msg.twist.linear.x = 0.0
            vel_msg.twist.angular.z = 0.0

        # Publish velocity command
        self.vel_pub.publish(vel_msg)

    def normalize_angle(self, angle):
        # Normalize angle to [-pi, pi]
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle


def main(args=None):
    rclpy.init(args=args)
    node = PolygonDrawer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

        

