import rclpy
import sys

def main():
    print("Initializing rclpy...")
    sys.stdout.flush()
    rclpy.init()
    print("rclpy initialized.")
    sys.stdout.flush()
    node = rclpy.create_node('test_node')
    print("Node created.")
    sys.stdout.flush()
    node.destroy_node()
    rclpy.shutdown()
    print("Shutdown complete.")

if __name__ == '__main__':
    main()
