import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    gazebo = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("diff_amr_description"),
            "launch",
            "gazebo.launch.py"
        ),
        launch_arguments={
            "world_name": "maze_world"
        }.items()
    )

    controller = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("diff_amr_controller"),
            "launch", 
            "controller.launch.py"
        ),
    )

    web_socket = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("rosbridge_server"),
            "launch",
            "rosbridge_websocket_launch.xml"
        ),
    )

        # Website HTTP server
    web_directory = os.path.join(
        get_package_share_directory("diff_amr_web_control"),
        "web"
    )

    web_server = ExecuteProcess(
        cmd=[
            "python3",
            "-m",
            "http.server",
            "8000",
            "--directory",
            web_directory
        ],
        output="screen"
    )

    return LaunchDescription([
        gazebo,
        controller,
        web_socket,
        web_server,
    ])