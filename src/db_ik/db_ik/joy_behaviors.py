import py_trees 
import numpy as np
from sensor_msgs.msg import JointState
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
    Active: X(0)
'''

class GoalMsg:
    def __init__(self):
        self.jointAngle = None
        self.targetCell = None

    def __str__(self):
        return str(self.__dict__)


class AxesCommand(py_trees.behaviour.Behaviour):
    def __init__(self, name, axes):
        super().__init__(name)
        self.axes = axes
        self.check_indices = [2, 3, 5]  # Indices of the axes to check

    def update(self):
        for i in self.check_indices:
            if abs(self.axes[i]) >= 0.1:  # Threshold for axis movement
                return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
    
class ButtonsCommand(py_trees.behaviour.Behaviour):
    def __init__(self, name, buttons):
        super().__init__(name)
        self.buttons = buttons
        self.check_indices = [0, 1, 2, 4, 6]  # Added index 0 for Active button

    def update(self):
        for i in self.check_indices:
            if i < len(self.buttons) and self.buttons[i] != 0:
                return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
    
class ExecuteMoveCommand(py_trees.behaviour.Behaviour):
    def __init__(self, name, joint_publisher, topic):
        super().__init__(name)
        self.joint_publisher = joint_publisher
        self.reader = py_trees.blackboard.Client(name=f"GoalReader")
        self.reader.register_key(key=topic, access=py_trees.common.Access.READ)
        

    def update(self):
        # Implementation for executing move command
        rmsg = self.reader.moveGoalMsg 
        if rmsg and rmsg.jointAngle and rmsg.targetCell:
            msg = JointState()
            msg.name = ["joint2_to_joint1",
                "joint3_to_joint2",
                "joint4_to_joint3",
                "joint5_to_joint4",
                "joint6_to_joint5",
                "joint6output_to_joint6"]
            msg.position = rmsg.jointAngle
            self.joint_publisher.publish(msg)
            print(f"[ExecuteMoveCommand] move to position: {rmsg.targetCell}")
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
    


class QueryDBCommand(py_trees.behaviour.Behaviour):
    def __init__(self, name, db_cursor, position, topic):
        super().__init__(name)
        self.cursor = db_cursor
        self.position = position
        self.resolution = 0.04  # Voxel resolution in the z-axis
        self.move_writer = py_trees.blackboard.Client(name="moveGoalPublisher")
        self.move_writer.register_key(key=topic, access=py_trees.common.Access.WRITE)

       
    def get_nearest_voxel(self, position):
        x, y, z = position
        # filter by x and y as well for efficiency, and then find nearest voxel in the filtered results

        sql_query = f"""
            SELECT id,x,y,z FROM voxels WHERE (z>={z - self.resolution} and z<={z + self.resolution});
        """
        self.cursor.execute(sql_query)
        results = self.cursor.fetchall()

        nearest_voxel_id = None
        min_distance = float('inf')

        for voxel in results:
            voxel_id, voxel_x, voxel_y, voxel_z = voxel
            distance = ((voxel_x - x) ** 2 + (voxel_y - y) ** 2 + (voxel_z - z) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_voxel_id = voxel_id

        return nearest_voxel_id

    
    def get_joint_values_from_db(self, voxel_id):     
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

    def update(self):
        nearest_voxel_id = self.get_nearest_voxel(self.position)
        
        # print(f"Nearest voxel ID: {nearest_voxel_id}, Position: {self.position}")

        joints = self.get_joint_values_from_db(nearest_voxel_id)
        if joints:
            self.move_writer.moveGoalMsg = GoalMsg()
            self.move_writer.moveGoalMsg.jointAngle = joints
            self.move_writer.moveGoalMsg.targetCell = self.position

            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
    

class SendGoalCommand(py_trees.behaviour.Behaviour):
    def __init__(self, name, position, topic):
        super().__init__(name)
        self.position = position
        self.move_writer = py_trees.blackboard.Client(name="sendGoalPublisher")
        self.move_writer.register_key(key=topic, access=py_trees.common.Access.WRITE)

    # def update(self):
        
    
    
class MoveCommand(py_trees.behaviour.Behaviour):
    def __init__(self, name, axes, position):
        super().__init__(name)
        self.axes = axes
        self.position = position
        self.gains = [0.001, 0.001, 0.01]  # Gains for x, y, z movements

    def update(self):
        self.position[0] = np.clip(self.position[0] - self.axes[2] * self.gains[0], -0.28, 0.28)
        self.position[1] = np.clip(self.position[1] + self.axes[3] * self.gains[1], -0.28, 0.28)
        self.position[2] = np.clip(self.position[2] + self.axes[5] * self.gains[2], -0.28, 0.28)
        return py_trees.common.Status.SUCCESS
    
    def terminate(self, new_status):
        # print(f"Updated position: {self.position}")
        return super().terminate(new_status)

class ButtonBehavior(py_trees.behaviour.Behaviour):
    def __init__(self, name, buttons, position, topic):
        super().__init__(name)
        self.buttons = buttons
        self.position = position
        self.move_writer = py_trees.blackboard.Client(name="buttonGoalPublisher")
        self.move_writer.register_key(key=topic, access=py_trees.common.Access.WRITE)


    def update(self):
        
        if self.buttons[4] != 0:  # Check if button LB is pressed
            print("Button LB pressed: Reset action triggered")  
            self.position[0] = 0.0
            self.position[1] = 0.0
            self.position[2] = 0.15

            self.move_writer.moveGoalMsg = GoalMsg()
            self.move_writer.moveGoalMsg.jointAngle = [0, 0, 0, 0, 0, 0]  # Assuming reset means all joints to 0
            self.move_writer.moveGoalMsg.targetCell = self.position
               # FIX: Use slice assignment to update original list
            return py_trees.common.Status.SUCCESS
        elif self.buttons[0] != 0:  # Check if button X is pressed
            print("Button X pressed: Active action triggered")
            # 0.0199999999999999	-0.1	0.14
            self.position[0] = 0.02
            self.position[1] = -0.1
            self.position[2] = 0.14
            self.move_writer.moveGoalMsg = GoalMsg()
            self.move_writer.moveGoalMsg.jointAngle = [-0.689613319777275,	0.948615463940899,	-2.51692935543461,	-0.00988565457426034,	0.00351946893085185,	0.444380898340641]  # Assuming active means all joints to 0
            self.move_writer.moveGoalMsg.targetCell = self.position
            return py_trees.common.Status.SUCCESS   
        else:
            return py_trees.common.Status.FAILURE
        
def get_joy_behavior_tree(axes, buttons, position, db_cursor, joint_publisher):
    # Use Parallel to allow Both movement AND button presses at the same time
    joy_root = py_trees.composites.Selector("Joystick Control", memory=False)
                                    
    
    axes_sequence = py_trees.composites.Sequence("Axes Sequence", memory=False)
    buttons_sequence = py_trees.composites.Sequence("Buttons Sequence", memory=False)

    topic = "moveGoalMsg"
    axes_command = AxesCommand("Check Axes", axes)
    buttons_command = ButtonsCommand("Check Buttons", buttons)
    move_command = MoveCommand("Move Robot", axes, position)
    button_behavior = ButtonBehavior("Button Actions", buttons, position, topic)

    db_query = QueryDBCommand("Query DB", db_cursor=db_cursor, position=position, topic=topic)  # db_cursor will be set later when we have access to it
    execute_move = ExecuteMoveCommand("Execute Move", joint_publisher=joint_publisher, topic=topic)  # joint_publisher will be set later when we have access to it
    
    axes_sequence.add_children([axes_command, move_command, db_query])
    buttons_sequence.add_children([buttons_command, button_behavior])

    joy_root.add_children([axes_sequence, buttons_sequence])

    root = py_trees.composites.Sequence("Root Sequence", memory=False)
    root.add_children([joy_root, execute_move])
      
    return root


def get_send_goal_behavior_tree(position, db_cursor, joint_publisher):
    topic = "moveGoalMsg"

    db_query = QueryDBCommand("Query DB", db_cursor=db_cursor, position=position, topic=topic)  # db_cursor will be set later when we have access to it
    execute_move = ExecuteMoveCommand("Execute Move", joint_publisher=joint_publisher, topic=topic)  # joint_publisher will be set later when we have access to it
    
    root = py_trees.composites.Sequence("Root Sequence", memory=False)
    root.add_children([db_query, execute_move])
      
    return root

