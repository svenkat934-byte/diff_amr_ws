
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
)
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():

    controller_pkg = get_package_share_directory(
        "diff_amr_controller"
    )

    web_pkg = get_package_share_directory(
        "diff_amr_web_control"
    )

    # Simulated time
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="True",
        description="Use simulated time",
    )

    # ROSBRIDGE WEBSOCKET
    rosbridge_launch = IncludeLaunchDescription(
    AnyLaunchDescriptionSource(
        os.path.join(
            get_package_share_directory("rosbridge_server"),
            "launch",
            "rosbridge_websocket_launch.xml",
        )
    ),
    launch_arguments={
        "address": "0.0.0.0",
        "port": "9090",
    }.items(),
)
    # WEBSITE HTTP SERVER
    web_directory = os.path.join(
        web_pkg,
        "web",
    )

    web_server = ExecuteProcess(
        cmd=[
            "python3",
            "-m",
            "http.server",
            "8000",
            "--directory",
            web_directory,
            "--bind",
            "0.0.0.0",
        ],
        output="screen",
    )

    # TWIST MUX
    twist_mux_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("twist_mux"),
                "launch",
                "twist_mux_launch.py",
            )
        ),
        launch_arguments={
            "cmd_vel_out":
                "wheel_controller/cmd_vel",

            "config_topics": os.path.join(
                controller_pkg,
                "config",
                "twist_mux_topics.yaml",
            ),

            "config_locks": os.path.join(
                controller_pkg,
                "config",
                "twist_mux_locks.yaml",
            ),

            "use_sim_time":
                LaunchConfiguration("use_sim_time"),
        }.items(),
    )

    return LaunchDescription([
        use_sim_time_arg,
        rosbridge_launch,
        web_server,
        twist_mux_launch,
    ])
