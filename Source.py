import tkinter as tk
import math
import random
import time
import gc
import sys

root = tk.Tk()
root.title("Force-Directed Graph Drawing")
nodes = []
lines = []
canvas = tk.Canvas(root, width=800, height=500, bg="yellow")
canvas.pack(side=tk.LEFT)


class Node:
    def __init__(self, name, color, radius, coords):
        self.name = name
        self.color = color
        self.radius = radius
        self.coords = coords
        self.circle = None
        self.text = None
        self.lines = []
        nodes.append(self)
        self.forces = []
        self.isMoving = False
        self.startX = 0
        self.startY = 0

    def make_circle(self):
        self.circle = canvas.create_oval(self.coords[0], self.coords[1],
                                         self.coords[0] + self.radius * 2, self.coords[1] + self.radius * 2,
                                         fill=self.color)
        canvas.tag_bind(self.circle, "<ButtonPress-1>", self.start_move)
        canvas.tag_bind(self.circle, "<B1-Motion>", self.moving)
        canvas.tag_bind(self.circle, "<ButtonRelease-1>", self.end_move)
        self.make_text()

    def start_move(self, event):
        self.isMoving = True
        self.startX = event.x
        self.startY = event.y

    def moving(self, event):
        if self.isMoving:
            self.move_circle(event.x - self.startX, event.y - self.startY)
            self.startX = event.x
            self.startY = event.y

    def end_move(self, event):
        self.isMoving = False
        canvas.delete("hidden")

    def move_circle(self, x, y):
        canvas.coords(self.circle,
                      self.coords[0] + x, self.coords[1] + y,
                      self.coords[0] + x + self.radius * 2, self.coords[1] + y + self.radius * 2)
        self.coords = self.get_coords()[0:2]
        for line in self.lines:
            line.calculate_line(line.nodes[0], line.nodes[1])
        canvas.itemconfig(self.text, state=tk.HIDDEN)
        canvas.addtag_withtag("hidden", self.text)
        self.make_text()

    def make_text(self):
        self.text = canvas.create_text(self.coords[0] + self.radius, self.coords[1] + self.radius, text=self.name)
        canvas.tag_bind(self.text, "<ButtonPress-1>", self.start_move)
        canvas.tag_bind(self.text, "<B1-Motion>", self.moving)
        canvas.tag_bind(self.text, "<ButtonRelease-1>", self.end_move)

    def get_adjacent_nodes(self):
        adjacent_nodes = []
        for line in lines:
            if line.nodes[0] == self:
                if line.nodes[1] not in adjacent_nodes:
                    adjacent_nodes.append(line.nodes[1])
            elif line.nodes[1] == self:
                if line.nodes[0] not in adjacent_nodes:
                    adjacent_nodes.append(line.nodes[0])
        return adjacent_nodes

    def get_coords(self):
        self.coords = canvas.coords(self.circle)
        coords = []
        for coord in self.coords:
            coords.append(round(coord))
        self.coords = coords
        return self.coords

    def get_centre(self):
        coords = canvas.coords(self.circle)
        return [coords[0] + (coords[2] - coords[0]) / 2, coords[1] + (coords[3] - coords[1]) / 2]

    def apply_forces(self):
        self.forces = []
        factor = 1.3 * (len(nodes) * 0.01) * (self.radius / 10)
        for particular_node in nodes:
            if particular_node == self:
                continue
            particular_node.forces = []
            self_centre = self.get_centre()
            particular_node_centre = particular_node.get_centre()
            x_difference = self_centre[0] - particular_node_centre[0]
            y_difference = self_centre[1] - particular_node_centre[1]
            bearing = math.atan2(x_difference, y_difference)
            while math.degrees(bearing) < 0:
                bearing += math.radians(360)
            while math.degrees(bearing) > 360:
                bearing -= math.radians(360)
            difference = math.sqrt(math.pow(x_difference, 2) + math.pow(y_difference, 2))
            if difference < limit:
                difference *= 0.0018
            if difference == 0:
                difference = math.pow(10, -3)
            force = Force(factor * (120 / difference), bearing)
            self.forces.append(force)
            force.magnitude = -force.magnitude
            particular_node.forces.append(force)
            force = add_forces(particular_node.forces)
            x_force = 0.0
            y_force = 0.0
            quadrant = int(force.bearing / 90) + 1
            # reference lines are positive and negative y and x axes
            angle_to_previous_ref_line = force.bearing % 90
            if quadrant == 1:
                x_force += force.magnitude * math.sin(angle_to_previous_ref_line)
                y_force += force.magnitude * math.cos(angle_to_previous_ref_line)
            elif quadrant == 2:
                x_force += force.magnitude * math.cos(angle_to_previous_ref_line)
                y_force -= force.magnitude * math.sin(angle_to_previous_ref_line)
            elif quadrant == 3:
                x_force -= force.magnitude * math.sin(angle_to_previous_ref_line)
                y_force -= force.magnitude * math.cos(angle_to_previous_ref_line)
            else:
                x_force -= force.magnitude * math.cos(angle_to_previous_ref_line)
                y_force += force.magnitude * math.sin(angle_to_previous_ref_line)
            particular_node.move_circle(factor * x_force, factor * y_force)
            self.move_circle(factor * -x_force, factor * -y_force)
            if self.get_coords()[0] < 0:
                self.move_circle(60, 0)
            elif self.get_coords()[2] > 800:
                self.move_circle(-60, 0)
            if self.get_coords()[1] < 0:
                self.move_circle(0, 60)
            elif self.get_coords()[3] > 500:
                self.move_circle(0, -60)

    def __repr__(self):
        return str(self.name)


class Line:
    def __init__(self, first_node, second_node):
        first_node.lines.append(self)
        second_node.lines.append(self)
        self.nodes = [first_node, second_node]
        self.line = None
        self.coords = []
        self.first_node_position = None
        self.calculate_line(first_node, second_node)  # please note that every time the position of any node changes,
        # this function must be called and only this function
        self.length = self.calculate_length()
        self.bearing = self.calculate_bearing()
        self.force = Force(0, 0)
        lines.append(self)

    def calculate_length(self):
        return math.sqrt(math.pow(self.coords[2] - self.coords[0], 2) + math.pow(self.coords[3] - self.coords[1], 2))

    def calculate_bearing(self):
        x_difference = self.coords[2] - self.coords[0]
        y_difference = self.coords[3] - self.coords[1]
        bearing = math.atan2(y_difference, x_difference) - math.radians(90)  # this gives the bearing on the...
        # ...lower node
        while math.degrees(bearing) < 0:
            bearing += math.radians(360)
        while math.degrees(bearing) > 360:
            bearing -= math.radians(360)
        return bearing

    def calculate_line(self, first_node, second_node):
        # coordinates are only north and south for simplicity
        # adding east and west later?
        if self.line is not None:
            canvas.delete(self.line)
        first_node_coords = first_node.get_coords()
        second_node_coords = second_node.get_coords()
        if first_node.get_centre()[1] < second_node_coords[1]:
            self.first_node_position = "north"
        else:
            self.first_node_position = "south"
        # elif first_node_coords[0] > second_node_coords[2]:
        #     self.first_node_position = "east"
        # else:
        #     self.first_node_position = "west"
        if self.first_node_position == "north":
            self.line = canvas.create_line(first_node_coords[0] + first_node.radius,
                                           first_node_coords[3],
                                           second_node_coords[0] + second_node.radius,
                                           second_node_coords[1])
        else:
            self.line = canvas.create_line(second_node_coords[0] + second_node.radius,
                                           second_node_coords[3],
                                           first_node_coords[0] + first_node.radius,
                                           first_node_coords[1])
        # elif self.first_node_position == "east":
        #     self.line = canvas.create_line(first_node_coords[0],
        #                                    first_node_coords[1] + first_node.radius,
        #                                    second_node_coords[2],
        #                                    second_node_coords[1] + second_node.radius)
        # else:
        #     self.line = canvas.create_line(second_node_coords[0],
        #                                    second_node_coords[1] + second_node.radius,
        #                                    first_node_coords[2],
        #                                    first_node_coords[1] + first_node.radius)
        self.coords = canvas.coords(self.line)
        self.length = self.calculate_length()
        self.bearing = self.calculate_bearing()
        self.force = Force(self.length, self.bearing)

    def apply_forces(self):
        force = self.force
        x_force = 0.0
        y_force = 0.0
        quadrant = int(force.bearing / 90) + 1
        # reference lines are positive and negative y and x axes
        angle_to_previous_ref_line = force.bearing % 90
        if quadrant == 1:
            x_force += force.magnitude * math.sin(angle_to_previous_ref_line)
            y_force += force.magnitude * math.cos(angle_to_previous_ref_line)
        elif quadrant == 2:
            x_force += force.magnitude * math.cos(angle_to_previous_ref_line)
            y_force -= force.magnitude * math.sin(angle_to_previous_ref_line)
        elif quadrant == 3:
            x_force -= force.magnitude * math.sin(angle_to_previous_ref_line)
            y_force -= force.magnitude * math.cos(angle_to_previous_ref_line)
        else:
            x_force -= force.magnitude * math.cos(angle_to_previous_ref_line)
            y_force += force.magnitude * math.sin(angle_to_previous_ref_line)
        factor = 0.000006 + self.length * 0.000025
        if self.first_node_position == "north":
            self.nodes[0].move_circle(factor * -x_force, factor * y_force)
            self.nodes[1].move_circle(factor * x_force, factor * -y_force)
        else:
            self.nodes[0].move_circle(factor * x_force, factor * -y_force)
            self.nodes[1].move_circle(factor * -x_force, factor * y_force)

    def __repr__(self):
        return str(self.coords)


class Force:
    def __init__(self, magnitude=None, bearing=None):
        self.magnitude = magnitude if math.fabs(magnitude) > 0.001 else 0  # this magic number shouldn't be a magic no.
        self.bearing = bearing if self.magnitude != 0 else 0

    def __repr__(self):
        return str(self.magnitude) + ", " + str(math.degrees(self.bearing))


def add_forces(forces):
    x_force = 0
    y_force = 0
    for force in forces:
        if force.magnitude == 0:
            continue
        elif force.magnitude < 0:
            force.magnitude = abs(force.magnitude)
            force.bearing += 180
        while force.bearing < 0:
            force.bearing += 360
        force.bearing %= 360
        quadrant = int(force.bearing / 90) + 1
        # reference lines are positive and negative y and x axes
        angle_to_previous_ref_line = force.bearing % 90
        if quadrant == 1:
            x_force += force.magnitude * math.sin(angle_to_previous_ref_line)
            y_force += force.magnitude * math.cos(angle_to_previous_ref_line)
        elif quadrant == 2:
            x_force += force.magnitude * math.cos(angle_to_previous_ref_line)
            y_force -= force.magnitude * math.sin(angle_to_previous_ref_line)
        elif quadrant == 3:
            x_force -= force.magnitude * math.sin(angle_to_previous_ref_line)
            y_force -= force.magnitude * math.cos(angle_to_previous_ref_line)
        else:
            x_force -= force.magnitude * math.cos(angle_to_previous_ref_line)
            y_force += force.magnitude * math.sin(angle_to_previous_ref_line)
    if x_force == 0:
        resultant_force = Force(y_force, 0 if y_force > 0 else 180)
        return resultant_force
    elif y_force == 0:
        resultant_force = Force(x_force, 90 if x_force > 0 else 270)
        return resultant_force
    bearing = math.atan2(x_force, y_force)
    while math.degrees(bearing) < 0:
        bearing += math.radians(360)
    while math.degrees(bearing) > 360:
        bearing -= math.radians(360)
    resultant_force = Force(math.sqrt(math.pow(x_force, 2) + math.pow(y_force, 2)), bearing)
    return resultant_force

if len(sys.argv) == 1:  # first started -- replace this with file read
    for i in range(15):
        Node(i, "green", 10, [random.randint(0, 800), random.randint(0, 500)]).make_circle()
    tuple_lines = []
    for i in range(len(nodes) - 1):
        Line(nodes[i], nodes[i + 1])
        tuple_lines.append([i, i + 1])
    while len(lines) < (len(nodes) * (len(nodes) - 1)) / 2:
        a, b = random.randint(0, len(nodes) - 1), random.randint(0, len(nodes) - 1)
        if a == b:
            continue
        for tuple_line in tuple_lines:
            if [a, b] == tuple_line:
                continue
        tuple_lines.append([a, b])
        Line(nodes[tuple_lines[-1][0]], nodes[tuple_lines[-1][1]])
else:
    with open("data.txt", "r") as file:
        contents = file.readlines()
        for i in range(len(contents)):
            Node(i, "green", 10, [0, 0]).make_circle()
        for content in contents:
            content = content.strip("\n").split(":")
            adjacent_nodes = content[1][1:-1].split(", ")
            for adjacent_node in adjacent_nodes:
                Line(nodes[int(content[0])], nodes[int(adjacent_node)])
            content[2] = content[2][1:-1].split(", ")
            nodes[int(content[0])].move_circle(int(content[2][0]), int(content[2][1]))

# ==== testing force
# forceOne = Force(8, math.radians(290))
# forceTwo = Force(20, math.radians(350))
# forceThree = Force(10, math.radians(300))
# forceList = [forceOne, forceTwo, forceThree]
# balancingForce = add_forces(forceList)
# balancingForce.magnitude = -balancingForce.magnitude
# forceList.append(balancingForce)
# if add_forces(forceList).magnitude == 0:
#     print("no resultant force")
# ====

limit = 70  # the minimum number of units between the centre of 2 nodes -- not strictly followed
for i in range(50):
    canvas.update_idletasks()
    canvas.update()
    time.sleep(0.15)
    for node in nodes:
        node.apply_forces()
    for line in lines:
        line.apply_forces()
# ====
with open("data.txt", "w") as file:
    for node in nodes:
        data = str(node.name)
        data += ":" + str(node.get_adjacent_nodes())
        data += ":" + str(node.get_coords())
        file.write(data)
        if node != nodes[:-1]:
            file.write("\n")
if len(sys.argv) > 1:
    if sys.argv[1] == "end":
        root.mainloop()
