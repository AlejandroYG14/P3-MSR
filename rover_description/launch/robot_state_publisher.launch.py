# ros2 launch rover_description robot_state_publisher.launch.py world_name:=urjc_excavation_msr


import os
from os.path import join
from ament_index_python.packages import get_package_share_directory, get_package_prefix

from launch import LaunchDescription
from launch.actions import SetEnvironmentVariable, IncludeLaunchDescription, OpaqueFunction
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import launch_ros.descriptions
from launch.actions import DeclareLaunchArgument


def start_gzserver(context, *args, **kwargs):

    pkg_path = get_package_share_directory('urjc_excavation_world')

    world_name = LaunchConfiguration('world_name').perform(context)

    world = join(pkg_path, 'worlds', world_name + '.world')

    start_gazebo_server_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': '-r -s -v 4 ' + world
        }.items()
    )

    start_gazebo_client_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': '-g'
        }.items()
    )

    return [start_gazebo_server_cmd, start_gazebo_client_cmd]


start_gazebo_server_cmd = OpaqueFunction(function=start_gzserver)

def get_model_paths(packages_names):
    model_paths = ""
    for package_name in packages_names:
        if model_paths != "":
            model_paths += os.pathsep

        package_path = get_package_prefix(package_name)
        model_paths += join(package_path, "share")

    if 'GZ_SIM_RESOURCE_PATH' in os.environ:
        model_paths += os.pathsep + os.environ['GZ_SIM_RESOURCE_PATH']

    return model_paths


def generate_launch_description():
    # Declare arguments
    description_file = LaunchConfiguration("description_file", default="robot.urdf.xacro")
    prefix = LaunchConfiguration("prefix", default="")
    use_sim_time = LaunchConfiguration('use_sim_time' , default='true')

    model_path = ''
    resource_path = ''
    pkg_share = get_package_share_directory('rover_description')
    rviz_config = os.path.join(pkg_share, 'rviz', 'rover.rviz')

    resource_path += pkg_share + model_path

    declare_world = DeclareLaunchArgument(
        'world_name',
        default_value='urjc_excavation_msr',
        description='World name'
    )

    if 'GZ_SIM_MODEL_PATH' in os.environ:
        model_path += os.pathsep+os.environ['GZ_SIM_MODEL_PATH']
    if 'GZ_SIM_RESOURCE_PATH' in os.environ:
        resource_path += os.pathsep+os.environ['GZ_SIM_RESOURCE_PATH']

    model_path = get_model_paths(['rover_description'])


    robot_description_content = Command([
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([FindPackageShare("rover_description"),"robots", description_file]),
    ])

    robot_description_param = launch_ros.descriptions.ParameterValue(robot_description_content, value_type=str)

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        #namespace=robot_id,
        output='screen',
        parameters=[{
          'use_sim_time': use_sim_time,
          'robot_description': robot_description_param,
          'publish_frequency': 100.0,
          'frame_prefix': prefix,
        }],
    )

    declare_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation time'
    )

    start_gazebo_server_cmd = OpaqueFunction(function=start_gzserver)

    gazebo_spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-model", "rover",
            "-topic", "robot_description",
            "-x", "-0.3",
            "-y", "0.0",
            "-z", "-5.5",
            "-use_sim_time", "True",
        ],
    )
    robot_description_launcher = IncludeLaunchDescription(
        PathJoinSubstitution(
            [FindPackageShare("rover_moveit_config"), "launch",
            "rsp.launch.py"]
        ),
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='bridge_ros_gz',
        parameters=[
            {
                'config_file': join(
                    pkg_share, 'config', 'rover_bridge.yaml'
                ),
                'use_sim_time': True,
            }
        ],
        output='screen',
    )

    gz_image_bridge_node = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=[
            "/front_camera_image",
            "/arm_camera_image"
        ],
        output="screen",
        parameters=[
            {'use_sim_time': True,
            'camera.image.compressed.jpeg_quality': 75},
        ],
    )

    twist_stamped = Node(
        package="twist_stamper",
        executable="twist_stamper",
        name="twist_stamper",
        output="screen",
        parameters=[
            {
                "use_sim_time": True,
            }],
        remappings={('cmd_vel_out', '/rover_base_control/cmd_vel'),
            ('cmd_vel_in', '/cmd_vel')},
    )


    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    '''joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )'''

    ld = LaunchDescription()
    ld.add_action(declare_world)
    ld.add_action(SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', model_path))
    ld.add_action(SetEnvironmentVariable('GZ_SIM_MODEL_PATH', model_path))
    ld.add_action(start_gazebo_server_cmd)
    ld.add_action(robot_description_launcher)
    ld.add_action(declare_sim_time)
    ld.add_action(bridge)
    ld.add_action(gz_image_bridge_node)
    ld.add_action(rviz_node)
    ld.add_action(gazebo_spawn_robot)
    ld.add_action(twist_stamped)
    ld.add_action(robot_state_publisher_node)
    #ld.add_action(joint_state_publisher_gui_node)
    return ld
