import py_trees 
import numpy as np

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
        print(f"Updated position: {self.position}")
        return super().terminate(new_status)

class ButtonBehavior(py_trees.behaviour.Behaviour):
    def __init__(self, name, buttons, position):
        super().__init__(name)
        self.buttons = buttons
        self.position = position

    def update(self):
        if self.buttons[1] != 0:  # Check if button A is pressed
            print("Button A pressed: Pick action triggered")
            return py_trees.common.Status.SUCCESS
        elif self.buttons[2] != 0:  # Check if button B is pressed
            print("Button B pressed: Place action triggered")
            return py_trees.common.Status.SUCCESS
        elif self.buttons[4] != 0:  # Check if button LB is pressed
            print("Button LB pressed: Reset action triggered")  
            self.position[0] = 0.0
            self.position[1] = 0.0
            self.position[2] = 0.0
               # FIX: Use slice assignment to update original list
            return py_trees.common.Status.SUCCESS
        elif self.buttons[6] != 0:  # Check if button LT is pressed
            print("Button LT pressed: Home action triggered")
            return py_trees.common.Status.SUCCESS
        elif self.buttons[0] != 0:  # Check if button X is pressed
            print("Button X pressed: Active action triggered")
            self.position[0] = 0.0
            self.position[1] = 0.0
            self.position[2] = 0.15
            return py_trees.common.Status.SUCCESS   
        else:
            return py_trees.common.Status.FAILURE
        
def get_joy_behavior_tree(axes, buttons, position):
    # Use Parallel to allow Both movement AND button presses at the same time
    root = py_trees.composites.Parallel("Joystick Control", 
                                        policy=py_trees.common.ParallelPolicy.SuccessOnAll())
    
    axes_sequence = py_trees.composites.Sequence("Axes Sequence", memory=False)
    buttons_sequence = py_trees.composites.Sequence("Buttons Sequence", memory=False)

    axes_command = AxesCommand("Check Axes", axes)
    buttons_command = ButtonsCommand("Check Buttons", buttons)
    move_command = MoveCommand("Move Robot", axes, position)
    button_behavior = ButtonBehavior("Button Actions", buttons, position)
   
    axes_sequence.add_children([axes_command, move_command])
    buttons_sequence.add_children([buttons_command, button_behavior])

    root.add_children([axes_sequence, buttons_sequence])
    
    return root

