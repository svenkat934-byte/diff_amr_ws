import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


# robot_description rviz
description_rviz_config_path = os.path.join(
    get_package_share_directory("diff_amr_description"),
    'rviz',
    'display.rviz'
)
# # Path to SLAM configuration 
# slam_rviz_config_path = os.path.join(
#     get_package_share_directory("diff_amr_mapping"),
#     'rviz',
#     'slam.rviz'
# )

# # Path to Localization configuration
# localization_rviz_config_path = os.path.join(
#     get_package_share_directory("diff_amr_localization"),
#     'rviz',
#     'global_localization.rviz'
# )


def generate_launch_description():

    gazebo = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("diff_amr_description"),
            "launch",
            "gazebo.launch.py"
        ),
        launch_arguments={
            "world_name": "empty",
        }.items()
    )

    controller = IncludeLaunchDescription(
        os.path.join(
            get_package_share_directory("diff_amr_controller"),
            "launch", 
            "controller.launch.py"
        ),
    )

    # web_socket = IncludeLaunchDescription(
    #     os.path.join(
    #         get_package_share_directory("diff_amr_controller"),
    #         "launch",
    #         "web_control.launch.py"
    #     ),
    # )

    # slam = IncludeLaunchDescription(
    #     os.path.join(
    #         get_package_share_directory("diff_amr_mapping"),
    #         "launch",
    #         "slam.launch.py"
    #     ),
    #     launch_arguments={
    #         "use_sim_time": "True"
    #     }.items()
    # )

    # global_localization = IncludeLaunchDescription(
    #     os.path.join(
    #         get_package_share_directory("diff_amr_localization"),
    #         "launch",
    #         "global_localization.launch.py"
    #     ),
        
    # )

    # navigation = IncludeLaunchDescription(
    #     os.path.join(
    #         get_package_share_directory("diff_amr_navigation"),
    #         "launch",
    #         "navigation.launch.py"
    #     ),
    # )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz",
        output="screen",
        arguments=["-d", description_rviz_config_path]
        # arguments=['-d', slam_rviz_config_path] # For Mapping
        # arguments=['-d', localization_rviz_config_path] # For Localization
    )


    return LaunchDescription([
        gazebo,
        controller,
        # web_socket,
        # #slam,
        # global_localization,
        rviz,
        # #navigation
     
    ])