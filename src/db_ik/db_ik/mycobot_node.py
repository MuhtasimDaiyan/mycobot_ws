from geometry_msgs import msg
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Point
from sensor_msgs.msg import JointState, Joy
import sqlite3
from typing import Tuple, Optional
import sys
from db_ik.joy_behaviors import get_joy_behavior_tree, get_send_goal_behavior_tree
import py_trees

'''
logitech f710 joystick map
axes:
    x-axis movement: -axes(2) 
    y-axis movement: axes(3)
    z-axis movement: axes(5) top arrow: 1, bottom arrow: -1
buttons:
    Reset: LB(4)
    Home: LT(6)
    Pick: A(1)
    Place: B(2)
'''

class ik_planner(Node):

    def __init__(self, db_path: str):
        super().__init__('ik_planner')
        print(f'Starting node with DB: {db_path}')
        sys.stdout.flush()
        self.get_logger().info(f'Minimal Subscriber node has been started. Listening on /goal_pose...')
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.goal_pose_subscriber = self.create_subscription(
            PoseStamped,
            '/goal_pose',
            self.goal_pose_subscriber_callback,
            10)
        self.goal_pose_subscriber  # prevent unused variable warning

        self.position = [0.0, 0.0, 0.0]  # Initial position for the MoveCommand

        self.joystick_subscriber = self.create_subscription(
            Joy,
            '/joy',
            self.joystick_subscriber_callback,
            10)
        self.joystick_subscriber  # prevent unused variable warning

        self.joint_publisher = self.create_publisher(JointState, '/joint_states', 10)   
    
    

    def joystick_subscriber_callback(self, msg):
        old_position = self.position.copy()  # Store old position for comparison
        behavior_tree = get_joy_behavior_tree(msg.axes, msg.buttons, self.position, self.cursor, self.joint_publisher)
        if behavior_tree.tick_once() == py_trees.common.Status.FAILURE:
            self.position = old_position  # Revert to old position if behavior tree fails
    
    def goal_pose_subscriber_callback(self, msg):
        old_position = self.position.copy()
        x, y, z = msg.pose.position.x, msg.pose.position.y, msg.pose.position.z
        behavior_tree = get_send_goal_behavior_tree([x, y, z], self.cursor, self.joint_publisher)
        if behavior_tree.tick_once() == py_trees.common.Status.FAILURE:
            self.position = old_position

def main(args=None):
    print("Main called")
    sys.stdout.flush()
    rclpy.init(args=args)
    print("ROS 2 Python node initialized.")
    sys.stdout.flush()

    Planner = ik_planner("/home/airlab/mycobot_ws/src/airlab_cobot/config/my_cobot.db")

    print("Entering spin...")
    sys.stdout.flush()

    try:
        rclpy.spin(Planner)
    except KeyboardInterrupt:
        pass
    finally:
        # Destroy the node explicitly
        # (optional - otherwise it will be done automatically
        # when the garbage collector destroys the node object)
        Planner.destroy_node()
        rclpy.shutdown()
        print("Shutdown complete.")


if __name__ == '__main__':
    main()