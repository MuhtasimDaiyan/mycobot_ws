#!/home/airlab/mycobot_ws/.venv/bin/python
import subprocess
import argparse
'''
ros2 topic pub --once /goal_pose geometry_msgs/msg/PoseStamped "{header: {stamp: {sec: 0, nanosec: 0}, frame_id: 'map'}, 
pose: {position: {x: 0.2, y: 0.2, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}"
'''

# def send_goal(x, y):
#     cmd = f"ros2 topic pub --once /goal_pose geometry_msgs/msg/PoseStamped \"{{header: {{stamp: {{sec: 0, nanosec: 0}}, frame_id: 'map'}}, pose: {{position: {{x: {x}, y: {y}, z: 0.0}}, orientation: {{x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}}}}\""
#     subprocess.run(cmd, shell=True)


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description='Send a goal position to the robot.')
#     parser.add_argument('x', type=float, help='X coordinate of the goal position')
#     parser.add_argument('y', type=float, help='Y coordinate of the goal position')
#     args = parser.parse_args()

#     send_goal(args.x, args.y)

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
import sys

class GoalPublisher(Node):
    def __init__(self, x, y):
        super().__init__('minimal_goal_pub')
        self.publisher_ = self.create_publisher(PoseStamped, '/goal_pose', 10)
        
        # Give DDS a moment to discover subscribers
        self.get_logger().info('Waiting for subscribers...')
        while self.publisher_.get_subscription_count() == 0:
            rclpy.spin_once(self, timeout_sec=0.1)

        msg = PoseStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.position.x = x
        msg.pose.position.y = y
        msg.pose.orientation.w = 1.0

        self.publisher_.publish(msg)
        self.get_logger().info(f'Published goal: x={x}, y={y}')

def main():
    if len(sys.argv) < 3:
        return
    
    rclpy.init()
    node = GoalPublisher(float(sys.argv[1]), float(sys.argv[2]))
    # Brief sleep to ensure the message clears the buffer before shutdown
    import time
    time.sleep(0.5) 
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()