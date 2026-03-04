import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import JointState
import sqlite3
from typing import Tuple, Optional
import sys



class MinimalSubscriber(Node):

    def __init__(self, db_path: str):
        super().__init__('minimal_subscriber')
        print(f'Starting node with DB: {db_path}')
        sys.stdout.flush()
        self.get_logger().info(f'Minimal Subscriber node has been started. Listening on /goal_pose...')
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.subscription = self.create_subscription(
            PoseStamped,
            '/goal_pose',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

        self.joint_publisher = self.create_publisher(JointState, '/joint_states', 10)   
    def get_joint_values_from_db(self, end_effector) -> Optional[Tuple[float, float, float, float, float, float]]:
        """
        end_effector must have attributes: x, y, z
        """

        

        sql_query = """
            SELECT j1, j2, j3, j4, j5, j6
            FROM joints
            JOIN voxels ON voxel_id = voxels.id
            WHERE
                x >= ? AND x < ? AND
                y >= ? AND y < ? AND
                z >= ? AND z < ?
            LIMIT 1
        """

        params = (
            end_effector.x,
            end_effector.x + 0.04,
            end_effector.y,
            end_effector.y + 0.04,
            end_effector.z,
            end_effector.z + 0.04
        )

        self.cursor.execute(sql_query, params)
        result = self.cursor.fetchone()

        if result:
            # result is already a tuple of 6 values
            joints = tuple(float(value) for value in result)
            return joints

        return None

    def listener_callback(self, msg):
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



def main(args=None):
    print("Main called")
    sys.stdout.flush()
    rclpy.init(args=args)
    print("ROS 2 Python node initialized.")
    sys.stdout.flush()

    minimal_subscriber = MinimalSubscriber("/home/airlab/mycobot_ws/src/airlab_cobot/config/my_cobot.db")

    print("Entering spin...")
    sys.stdout.flush()

    try:
        rclpy.spin(minimal_subscriber)
    except KeyboardInterrupt:
        pass
    finally:
        # Destroy the node explicitly
        # (optional - otherwise it will be done automatically
        # when the garbage collector destroys the node object)
        minimal_subscriber.destroy_node()
        rclpy.shutdown()
        print("Shutdown complete.")


if __name__ == '__main__':
    main()