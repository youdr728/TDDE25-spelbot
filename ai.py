import math
import pymunk
from pymunk import Vec2d
import gameobjects
from collections import defaultdict, deque

# NOTE: use only 'map0' during development!

MIN_ANGLE_DIF = math.radians(3) # 3 degrees, a bit more than we can turn each tick



def angle_between_vectors(vec1, vec2):
    """ Since Vec2d operates in a cartesian coordinate space we have to
        convert the resulting vector to get the correct angle for our space.
    """
    vec = vec1 - vec2
    vec = vec.perpendicular()
    return vec.angle

def periodic_difference_of_angles(angle1, angle2):
    return  (angle1% (2*math.pi)) - (angle2% (2*math.pi))


class Ai:
    """ A simple ai that finds the shortest path to the target using
    a breadth first search. Also capable of shooting other tanks and or wooden
    boxes. """

    def __init__(self, tank,  game_objects_list, tanks_list, space, currentmap):
        self.tank               = tank
        self.game_objects_list  = game_objects_list
        self.tanks_list         = tanks_list
        self.space              = space
        self.currentmap         = currentmap
        self.flag = None
        self.MAX_X = currentmap.width - 1
        self.MAX_Y = currentmap.height - 1
        self.path = deque()
        self.move_cycle = self.move_cycle_gen()
        self.update_grid_pos()

    def update_grid_pos(self):
        """ This should only be called in the beginning, or at the end of a move_cycle. """
        self.grid_pos = self.get_tile_of_position(self.tank.body.position)

    def decide(self):
        """ Main decision function that gets called on every tick of the game. """
        self.maybe_shoot()
        next(self.move_cycle)


    def maybe_shoot(self):
        """ Makes a raycast query in front of the tank. If another tank
            or a wooden box is found, then we shoot.
        """
        angle = self.tank.body.angle + math.pi/2

        start = Vec2d(0.5*math.cos(angle), 0.5*math.sin(angle))
        end = Vec2d(self.MAX_X*math.cos(angle), (self.MAX_Y*math.sin))
        print(start, end)
        box_or_tank = self.space.segment_query_first(start, end, 0, pymunk.ShapeFilter())

        if hasattr(box_or_tank, "shape"):
            if hasattr(box_or_tank.shape, "parent"):
                if isinstance(box_or_tank.shape.parent, gameobjects.Box):
                    if box_or_tank.shape.parent.destructable:
                        self.tank.shoot(self.space)
                        print("box")
                elif isinstance(box_or_tank.shape.parent, gameobjects.Tank):
                    print("tank")
                    self.tank.shoot(self.space)

    def move_cycle_gen (self):
        """
        A generator that iteratively goes through all the required steps
        to move to our goal.
        """
        self.find_shortest_path()
        while True:
            self.update_grid_pos()
            path = self.find_shortest_path()
            if not path:
                yield
                continue
            next_coord = path.popleft()
            target_angle = angle_between_vectors(self.tank.body.position, next_coord + (0.5, 0.5))
            periodic_angle = periodic_difference_of_angles(self.tank.body.angle, target_angle)

            if 0<periodic_angle < math.pi:
                self.tank.turn_left()
                yield
            elif -2*math.pi < periodic_angle < -math.pi:
                self.tank.turn_left()
                yield
            else:
                self.tank.turn_right()
                yield

            while abs(periodic_angle) > MIN_ANGLE_DIF:
                periodic_angle = periodic_difference_of_angles(self.tank.body.angle, target_angle)
                yield
            self.tank.stop_turning()
            self.tank.accelerate()

            distance = self.tank.body.position.get_distance(next_coord+(0.5, 0.5))
            while distance > 0.1:
                distance = self.tank.body.position.get_distance(next_coord+(0.5, 0.5))
                yield
            self.tank.stop_moving()
            yield

    def find_shortest_path(self):
        """ A simple Breadth First Search using integer coordinates as our nodes.
            Edges are calculated as we go, using an external function.
        """
        shortest_path = []
        start = self.grid_pos
        queue = deque()
        queue.append([start])
        visited_nodes = set()

        while queue:
            path = queue.popleft()
            node = path[-1]
            if node == self.get_target_tile():
                path.popleft()
                return path
            for neighbor in self.get_tile_neighbors(node):
                if neighbor.int_tuple not in visited_nodes:
                    new_path = deque(path)
                    new_path.append(neighbor)
                    queue.append(new_path)
                    visited_nodes.add(neighbor.int_tuple)

    def get_target_tile(self):
        """ Returns position of the flag if we don't have it. If we do have the flag,
            return the position of our home base.
        """
        if self.tank.flag != None:
            x, y = self.tank.start_position
        else:
            self.get_flag() # Ensure that we have initialized it.
            x, y = self.flag.x, self.flag.y
        return Vec2d(int(x), int(y))

    def get_flag(self):
        """ This has to be called to get the flag, since we don't know
            where it is when the Ai object is initialized.
        """
        if self.flag == None:
        # Find the flag in the game objects list
            for obj in self.game_objects_list:
                if isinstance(obj, gameobjects.Flag):
                    self.flag = obj
                    break
        return self.flag

    def get_tile_of_position(self, position_vector):
        """ Converts and returns the float position of our tank to an integer position. """
        x, y = position_vector
        return Vec2d(int(x), int(y))

    def get_tile_neighbors(self, coord_vec):
        """ Returns all bordering grid squares of the input coordinate.
            A bordering square is only considered accessible if it is grass
            or a wooden box.
        """

        neighbors = [] # Find the coordinates of the tiles' four neighbors
        neighbors.append(coord_vec+Vec2d(0,1))
        neighbors.append(coord_vec+Vec2d(0,-1))
        neighbors.append(coord_vec+Vec2d(1,0))
        neighbors.append(coord_vec+Vec2d(-1,0))

        return filter(self.filter_tile_neighbors, neighbors)

    def filter_tile_neighbors (self, coord):
        if coord[0] <= self.MAX_X and coord[0] >= 0:
            if coord[1] <= self.MAX_Y and coord[1] >= 0:
                if self.currentmap.boxAt(coord[0], coord[1]) == 0:
                    return True
        return False


SimpleAi = Ai # Legacy
