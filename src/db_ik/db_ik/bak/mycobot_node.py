from geometry_msgs import msg
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Point
from sensor_msgs.msg import JointState, Joy
import sqlite3
from typing import Tuple, Optional
import sys
from db_ik.joy_behaviors import get_joy_behavior_tree


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
    
    def get_nearest_voxel(self, position):
        x, y, z = position

        sql_query = f"""
            SELECT id,x,y FROM voxels WHERE (z>={z} and z<={z+0.04});
        """
        self.cursor.execute(sql_query)
        results = self.cursor.fetchall()

        nearest_voxel_id = None
        min_distance = float('inf')

        for voxel in results:
            voxel_id, voxel_x, voxel_y = voxel
            distance = ((voxel_x - x) ** 2 + (voxel_y - y) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_voxel_id = voxel_id

        return nearest_voxel_id

    
    def get_joint_values_from_db(self, end_effector) -> Optional[Tuple[float, float, float, float, float, float]]:
        """
        end_effector must have attributes: x, y, z
        """

        voxel_id = self.get_nearest_voxel((end_effector.x, end_effector.y, end_effector.z))
        self.get_logger().info(f'Nearest voxel ID: {voxel_id} for position: ({end_effector.x}, {end_effector.y}, {end_effector.z})')

        sql_query = f"""
            SELECT j1, j2, j3, j4, j5, j6
            FROM joints
            WHERE voxel_id = {voxel_id}
        """

        self.cursor.execute(sql_query)
        result = self.cursor.fetchone()

        if result:
            # result is already a tuple of 6 values
            joints = tuple(float(value) for value in result)
            return joints

        return None
    


    def goal_pose_subscriber_callback(self, msg):
        p = msg.pose.position
        p.z = 0.1
        self.get_logger().info(f'Position: x={p.x}, y={p.y}, z={p.z}')
        # self.get_logger().info(f'I heard: "{msg}"')
        joints = self.get_joint_values_from_db(p)
        if joints:
            self.get_logger().info(f'Joint values: {joints}')
            msg = JointState()
            msg.name = ["joint2_to_joint1",
                "joint3_to_joint2",
                "joint4_to_joint3",
                "joint5_to_joint4",
                "joint6_to_joint5",
                "joint6output_to_joint6"]
            msg.position = joints
            self.joint_publisher.publish(msg)

    def joystick_subscriber_callback(self, msg):
        # self.get_logger().info(f'Joystick message received: {msg}')
        old_position = self.position.copy()  # Store old position for comparison
        behavior_tree = get_joy_behavior_tree(msg.axes, msg.buttons, self.position)
        behavior_tree.tick_once()
        if any(p != o for p, o in zip(self.position, old_position)):
            self.get_logger().info(f'Position updated to: {self.position}')
            p = Point()
            p.x = self.position[0]
            p.y = self.position[1]
            p.z = self.position[2]
            joints = self.get_joint_values_from_db(p)
            msg = JointState()
            msg.name = ["joint2_to_joint1",
                "joint3_to_joint2",
                "joint4_to_joint3",
                "joint5_to_joint4",
                "joint6_to_joint5",
                "joint6output_to_joint6"]
            if joints:
                self.get_logger().info(f'Joint values from joystick: {joints}')
        
                msg.position = joints
                self.joint_publisher.publish(msg)

            else:
                self.get_logger().info(f'No joint values found for position: {old_position}, {self.position}')
                msg.position = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                self.joint_publisher.publish(msg)
                # self.get_logger().info(f'Position is at initial state, no joint values to publish.')
                # self.position = old_position
                
                # total = sum (self.position)
                # if total == 0.0:
                #     msg.position = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                #     self.joint_publisher.publish(msg)
                #     self.get_logger().info(f'Position is at initial state, no joint values to publish.')
                # else:
                #     self.position = old_position  # Revert to old position if no joint values found
                #     self.get_logger().info(f'No joint values found for position: {self.position}')


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