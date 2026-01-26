from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    # Package paths
    mycobot_description = get_package_share_directory('mycobot_description')
    mycobot_280 = get_package_share_directory('mycobot_280')
    airlab_cobot = get_package_share_directory('airlab_cobot')
    db_path = os.path.join(airlab_cobot, 'config', 'my_cobot.db')

    # Launch arguments

    model_arg = DeclareLaunchArgument(
        "model",
        default_value=os.path.join(
            get_package_share_directory("mycobot_description"),
            "urdf/mycobot_280_m5/mycobot_280_m5_with_pump.urdf"
        )
    )

    rviz_arg = DeclareLaunchArgument(
        'rvizconfig',
        default_value=os.path.join(
            mycobot_280,
            'config/mycobot.rviz'
        ),
        description='RViz config file'
    )

    gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='false',
        description='GUI flag (unused, kept for compatibility)'
    )

    # Robot description (xacro)
    robot_description = {
        'robot_description': Command([
            'xacro ',
            LaunchConfiguration('model')
        ])
    }

    # Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[robot_description],
        output='screen'
    )

    # RViz
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz',
        arguments=['-d', LaunchConfiguration('rvizconfig')],
        output='screen'
    )

    # airlab_cobot_qt_control node (GUI)
    qt_gui = Node(
        package='airlab_cobot',
        executable='airlab_cobot_qt_control',
        name='airlab_cobot_qt_control',
        output='screen',
        parameters=[{'db_path': db_path}]
    )

    return LaunchDescription([
        model_arg,
        rviz_arg,
        gui_arg,
        robot_state_publisher_node,
        rviz_node, 
        qt_gui
    ])
