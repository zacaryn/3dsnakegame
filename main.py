import pygame, random, numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from math import pi, cos, sin

pygame.display.set_caption("3D Snake Game")


# ----- Helper Functions -----
def is_in_bounds(pos):
    return all(MIN_POS <= pos[i] <= MAX_POS for i in range(3))

def lerp_color(c1, c2, t):
    # Linear interpolation between two RGB colors.
    return (c1[0]*(1-t) + c2[0]*t,
            c1[1]*(1-t) + c2[1]*t,
            c1[2]*(1-t) + c2[2]*t)

# Draw a diamond (an octahedron) for food.
def draw_diamond(size=0.3):
    v0 = [0, 0, size]
    v1 = [size, 0, 0]
    v2 = [0, size, 0]
    v3 = [-size, 0, 0]
    v4 = [0, -size, 0]
    v5 = [0, 0, -size]
    faces = [
        (v0, v1, v2),
        (v0, v2, v3),
        (v0, v3, v4),
        (v0, v4, v1),
        (v5, v2, v1),
        (v5, v3, v2),
        (v5, v4, v3),
        (v5, v1, v4)
    ]
    glBegin(GL_TRIANGLES)
    for face in faces:
        a, b, c = face
        ab = np.subtract(b, a)
        ac = np.subtract(c, a)
        n = np.cross(ab, ac)
        glNormal3fv(n)
        for vertex in face:
            glVertex3fv(vertex)
    glEnd()

# Compile display list for diamond (food) if possible.
try:
    diamond_list = glGenLists(1)
    if diamond_list == 0:
        raise Exception("glGenLists returned 0")
    glNewList(diamond_list, GL_COMPILE)
    draw_diamond(0.3)
    glEndList()
except Exception as e:
    print("Display lists not available for diamond; using immediate mode.")
    diamond_list = None

# Compile display list for the arena cube.
def compile_cube():
    size = GRID_SIZE // 2
    vertices = [
        [-size, -size, -size],
        [ size, -size, -size],
        [ size,  size, -size],
        [-size,  size, -size],
        [-size, -size,  size],
        [ size, -size,  size],
        [ size,  size,  size],
        [-size,  size,  size]
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7)
    ]
    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(vertices[vertex])
    glEnd()

try:
    cube_list = glGenLists(1)
    if cube_list == 0:
        raise Exception("glGenLists returned 0")
    glNewList(cube_list, GL_COMPILE)
    compile_cube()
    glEndList()
except Exception as e:
    print("Display lists not available for cube; using immediate mode.")
    cube_list = None

# Lower the resolution for snake spheres for performance.
def draw_sphere(radius=0.4, segments=6):
    for i in range(segments):
        lat0 = pi * (-0.5 + (i / segments))
        z0 = sin(lat0) * radius
        zr0 = cos(lat0) * radius
        lat1 = pi * (-0.5 + ((i + 1) / segments))
        z1 = sin(lat1) * radius
        zr1 = cos(lat1) * radius
        glBegin(GL_TRIANGLE_STRIP)
        for j in range(segments + 1):
            lng = 2 * pi * (j / segments)
            x = cos(lng)
            y = sin(lng)
            glNormal3f(x * cos(lat0), y * cos(lat0), sin(lat0))
            glVertex3f(x * zr0, y * zr0, z0)
            glNormal3f(x * cos(lat1), y * cos(lat1), sin(lat1))
            glVertex3f(x * zr1, y * zr1, z1)
        glEnd()

# ----- Setup OpenGL & Overlay Fonts -----
pygame.init()
display = (1920, 1080)
pygame.display.set_mode(display, pygame.DOUBLEBUF | pygame.OPENGL)
title_font = pygame.font.SysFont("Arial", 36, bold=True)
goal_font = pygame.font.SysFont("Arial", 24, bold=True)
win_font = pygame.font.SysFont("Arial", 36, bold=True)
small_font = pygame.font.SysFont("Arial", 18)

glClearColor(0.1, 0.1, 0.1, 1.0)
glEnable(GL_DEPTH_TEST)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glEnable(GL_LINE_SMOOTH)
glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
gluPerspective(45, (display[0] / display[1]), 0.1, 100.0)
glTranslatef(0.0, 0.0, -40)
glEnable(GL_LIGHTING)
glEnable(GL_LIGHT0)
glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.2, 0.2, 0.2, 1.0])
glLightfv(GL_LIGHT0, GL_DIFFUSE,  [0.8, 0.8, 0.8, 1.0])
glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
glEnable(GL_COLOR_MATERIAL)
glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

# ----- Game Constants & Variables -----
GRID_SIZE = 15
MIN_POS = -GRID_SIZE // 2 + 1
MAX_POS = GRID_SIZE // 2 - 1
WINNING_LENGTH = 100
mouse_dragging = False
green_food_eaten = 0
purple_cooldown = 0
max_green_food = 5
max_orange_food = 1
max_purple_food = 1

# ----- Food Class & Functions (using diamond) -----
class Food:
    def __init__(self, bonus=False, color=None):
        self.position = self.generate_food_position()
        self.bonus = bonus
        self.color = color if color is not None else ('orange' if bonus else 'green')
    def generate_food_position(self):
        return np.array([random.randint(MIN_POS, MAX_POS) for _ in range(3)])
    def draw(self):
        if self.color == 'green':
            glColor3f(0, 1, 0)
        elif self.color == 'orange':
            glColor3f(1, 0.5, 0)
        elif self.color == 'purple':
            glColor3f(0.5, 0, 0.5)
        glPushMatrix()
        glTranslatef(*self.position)
        if diamond_list is not None:
            glCallList(diamond_list)
        else:
            draw_diamond(0.3)
        glPopMatrix()

def spawn_green_food():
    return Food(bonus=False)
def spawn_orange_food():
    return Food(bonus=True)
def spawn_purple_food():
    return Food(bonus=False, color='purple')

green_foods = []
orange_foods = []
purple_foods = []
for _ in range(max_green_food):
    green_foods.append(spawn_green_food())

def get_closest_food(food_list, head):
    if not food_list:
        return None
    return min(food_list, key=lambda food: np.linalg.norm(food.position - head))

# ----- Snake Class with Optimized Boundary Checks -----
MAX_ITER = 10  # maximum iterations for boundary or collision safe-check

class Snake:
    def __init__(self, color, start_pos):
        self.color = color  # e.g. (1, 0, 0) or (0, 0, 1)
        self.body = [np.array(start_pos)]
        self.direction = np.array(random.choice([
            [1, 0, 0], [-1, 0, 0],
            [0, 1, 0], [0, -1, 0],
            [0, 0, 1], [0, 0, -1]
        ]))
        self.grow_count = 0
        self.speed_boost_timer = 0

    def move(self):
        head = self.body[0]
        new_head = head + self.direction
        # Use a maximum iteration count to avoid infinite loops.
        iter_count = 0
        while not is_in_bounds(new_head) and iter_count < MAX_ITER:
            self.change_direction()
            new_head = head + self.direction
            iter_count += 1
        if not is_in_bounds(new_head):
            # fallback: choose a random safe direction from head
            safe = [d for d in ([np.array([1,0,0]), np.array([-1,0,0]),
                                  np.array([0,1,0]), np.array([0,-1,0]),
                                  np.array([0,0,1]), np.array([0,0,-1])])
                    if is_in_bounds(head + d)]
            self.direction = random.choice(safe) if safe else np.array([0,0,0])
            new_head = head + self.direction

        # Check collision with the other snake.
        other = snake2 if self == snake1 else snake1
        iter_count = 0
        while any(np.array_equal(new_head, seg) for seg in other.body) and iter_count < MAX_ITER:
            self.change_direction()
            new_head = head + self.direction
            iter_count += 1
        if any(np.array_equal(new_head, seg) for seg in other.body):
            new_head = head  # fallback: do not move
        self.body.insert(0, new_head)
        if self.grow_count > 0:
            self.grow_count -= 1
        else:
            self.body.pop()

    def grow(self, amount=1):
        self.grow_count += amount

    def change_direction(self):
        global green_foods, orange_foods, purple_foods
        possible_directions = [np.array([1, 0, 0]), np.array([-1, 0, 0]),
                               np.array([0, 1, 0]), np.array([0, -1, 0]),
                               np.array([0, 0, 1]), np.array([0, 0, -1])]
        head = self.body[0]
        other = snake2 if self == snake1 else snake1

        # BOOST MODE: Use Manhattan logic.
        if self.speed_boost_timer > 0:
            target_food = get_closest_food(orange_foods, head) if orange_foods else get_closest_food(green_foods, head)
            if target_food is None:
                return
            diff = target_food.position - head
            if np.linalg.norm(diff) == 0:
                return
            axes = np.argsort(-np.abs(diff))
            chosen = None
            for axis in axes:
                candidate = np.zeros(3, dtype=int)
                candidate[axis] = 1 if diff[axis] > 0 else -1
                new_pos = head + candidate
                if not is_in_bounds(new_pos):
                    continue
                if any(np.array_equal(new_pos, seg) for seg in self.body[1:]):
                    continue
                if any(np.array_equal(new_pos, seg) for seg in other.body):
                    continue
                chosen = candidate
                break
            if chosen is None:
                safe_dirs = [d for d in possible_directions if is_in_bounds(head + d) and
                             not any(np.array_equal(head + d, seg) for seg in self.body[1:]) and
                             not any(np.array_equal(head + d, seg) for seg in other.body)]
                if safe_dirs:
                    chosen = min(safe_dirs, key=lambda d: sum(abs(target_food.position - (head + d))))
            if chosen is not None:
                self.direction = chosen
            return

        # NORMAL MODE: Use dot product logic.
        if self == snake1 and len(snake1.body) + 3 <= len(snake2.body) and purple_foods:
            target_food = get_closest_food(purple_foods, head)
        elif self == snake2 and len(snake2.body) + 3 <= len(snake1.body) and purple_foods:
            target_food = get_closest_food(purple_foods, head)
        else:
            target_food = get_closest_food(orange_foods, head) if orange_foods else get_closest_food(green_foods, head)
        if target_food is None:
            return
        vec_to_target = target_food.position - head
        distance = np.linalg.norm(vec_to_target)
        vec_to_target_norm = vec_to_target / distance if distance != 0 else vec_to_target
        grab_threshold = 1.5

        best_direction = self.direction
        best_score = -float('inf')
        for new_direction in possible_directions:
            new_position = head + new_direction
            if any(np.linalg.norm(new_position - seg) < 0.5 for seg in self.body[1:]):
                continue
            if any(np.array_equal(new_position, seg) for seg in other.body):
                continue
            penalty = 0 if distance < grab_threshold else (0 if np.array_equal(new_direction, self.direction) else 0.5)
            score = np.dot(new_direction, vec_to_target_norm) - penalty
            for seg in self.body[1:]:
                d = np.linalg.norm(new_position - seg)
                if d < 1.0:
                    score -= (1.0 - d)
            if score > best_score:
                best_score = score
                best_direction = new_direction
        self.direction = best_direction

# ----- Drawing Functions for Static Geometry -----
def draw_cube():
    glPushAttrib(GL_CURRENT_BIT)  # Save current color state.
    glColor3f(1, 0.7, 1)  # Set the cube’s color to your desired light pink/purple.
    if cube_list is not None:
        glCallList(cube_list)
    else:
        compile_cube()
    glPopAttrib()

def draw_sphere(radius=0.4, segments=6):
    for i in range(segments):
        lat0 = pi * (-0.5 + (i / segments))
        z0 = sin(lat0) * radius
        zr0 = cos(lat0) * radius
        lat1 = pi * (-0.5 + ((i + 1) / segments))
        z1 = sin(lat1) * radius
        zr1 = cos(lat1) * radius
        glBegin(GL_TRIANGLE_STRIP)
        for j in range(segments + 1):
            lng = 2 * pi * (j / segments)
            x = cos(lng)
            y = sin(lng)
            glNormal3f(x * cos(lat0), y * cos(lat0), sin(lat0))
            glVertex3f(x * zr0, y * zr0, z0)
            glNormal3f(x * cos(lat1), y * cos(lat1), sin(lat1))
            glVertex3f(x * zr1, y * zr1, z1)
        glEnd()

def draw_snake(snake):
    if snake.speed_boost_timer > 0:
        if snake.color == (1, 0, 0):
            boost_color = (1, 0, 1)
        elif snake.color == (0, 0, 1):
            boost_color = (0, 1, 1)
        else:
            boost_color = (0.5, 0, 0.5)
        for i, segment in enumerate(snake.body):
            t = i / (len(snake.body) - 1) if len(snake.body) > 1 else 0
            col = lerp_color(boost_color, snake.color, t)
            glColor3f(*col)
            glPushMatrix()
            glTranslatef(*segment)
            draw_sphere()
            glPopMatrix()
    else:
        glColor3fv(snake.color)
        for segment in snake.body:
            glPushMatrix()
            glTranslatef(*segment)
            draw_sphere()
            glPopMatrix()

def draw_text_top_left(text, x_offset, y_offset, font, color):
    surf = font.render(text, True, color)
    data = pygame.image.tostring(surf, "RGBA", True)
    x = x_offset
    y = display[1] - y_offset - surf.get_height()
    glWindowPos2d(x, y)
    glDrawPixels(surf.get_width(), surf.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)

def draw_text_top_right(text, x_offset, y_offset, font, color):
    surf = font.render(text, True, color)
    data = pygame.image.tostring(surf, "RGBA", True)
    x = display[0] - x_offset - surf.get_width()
    y = display[1] - y_offset - surf.get_height()
    glWindowPos2d(x, y)
    glDrawPixels(surf.get_width(), surf.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)

def draw_text_top_center(text, y_offset, font, color):
    surf = font.render(text, True, color)
    data = pygame.image.tostring(surf, "RGBA", True)
    x = (display[0] - surf.get_width()) // 2
    y = display[1] - y_offset - surf.get_height()
    glWindowPos2d(x, y)
    glDrawPixels(surf.get_width(), surf.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)

def draw_text_bottom_center(text, y_offset, font, color):
    surf = font.render(text, True, color)
    data = pygame.image.tostring(surf, "RGBA", True)
    x = (display[0] - surf.get_width()) // 2
    y = y_offset
    glWindowPos2d(x, y)
    glDrawPixels(surf.get_width(), surf.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)

def draw_text_center(text, font, color):
    surf = font.render(text, True, color)
    data = pygame.image.tostring(surf, "RGBA", True)
    x = (display[0] - surf.get_width()) // 2
    y = (display[1] - surf.get_height()) // 2
    glWindowPos2d(x, y)
    glDrawPixels(surf.get_width(), surf.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)

# ----- Initialize Game Objects -----
snake1 = Snake((1, 0, 0), [0, 0, 0])   # Red snake.
snake2 = Snake((0, 0, 1), [2, 2, 2])     # Blue snake.
clock = pygame.time.Clock()
running = True
winner = None

# ----- Main Game Loop -----
while running:
    pygame.time.delay(120)
    if purple_cooldown > 0:
        purple_cooldown -= 1
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            mouse_dragging = False
        elif event.type == pygame.MOUSEMOTION and mouse_dragging:
            dx, _ = pygame.mouse.get_rel()
            glRotatef(dx * 0.5, 0, 1, 0)
    if not mouse_dragging:
        glRotatef(1.0, 0, 1, 0)
    
    head_pos = snake1.body[0]
    glLightfv(GL_LIGHT0, GL_POSITION, [head_pos[0], head_pos[1], head_pos[2], 1.0])
    
    snake1.change_direction()
    snake2.change_direction()
    snake1.move()
    snake2.move()
    
    # Use larger collision thresholds when boosted.
    thresh1 = 1.5 if snake1.speed_boost_timer > 0 else 0.5
    thresh2 = 1.5 if snake2.speed_boost_timer > 0 else 0.5

    for food in green_foods[:]:
        if (np.linalg.norm(snake1.body[0] - food.position) < thresh1 or
            np.linalg.norm(snake2.body[0] - food.position) < thresh2):
            if np.linalg.norm(snake1.body[0] - food.position) < thresh1:
                snake1.grow()
            else:
                snake2.grow()
            green_foods.remove(food)
            green_food_eaten += 1
            if green_food_eaten % 2 == 0 and len(orange_foods) < max_orange_food:
                orange_foods.append(spawn_orange_food())
    for food in orange_foods[:]:
        if (np.linalg.norm(snake1.body[0] - food.position) < thresh1 or
            np.linalg.norm(snake2.body[0] - food.position) < thresh2):
            if np.linalg.norm(snake1.body[0] - food.position) < thresh1:
                snake1.grow(3)
            else:
                snake2.grow(3)
            orange_foods.remove(food)
    for food in purple_foods[:]:
        if (np.linalg.norm(snake1.body[0] - food.position) < thresh1 or
            np.linalg.norm(snake2.body[0] - food.position) < thresh2):
            if np.linalg.norm(snake1.body[0] - food.position) < thresh1:
                snake1.speed_boost_timer = 30
            else:
                snake2.speed_boost_timer = 30
            purple_foods.remove(food)
    
    if abs(len(snake1.body) - len(snake2.body)) > 3 and not purple_foods and purple_cooldown <= 0:
        purple_foods.append(spawn_purple_food())
        purple_cooldown = 50

    while len(green_foods) < max_green_food:
        green_foods.append(spawn_green_food())
    
    if snake1.speed_boost_timer > 0:
        for _ in range(2):
            snake1.move()
        snake1.speed_boost_timer -= 1
    if snake2.speed_boost_timer > 0:
        for _ in range(2):
            snake2.move()
        snake2.speed_boost_timer -= 1
    
    if len(snake1.body) >= WINNING_LENGTH:
        winner = "Red Snake Won!"
        running = False
    elif len(snake2.body) >= WINNING_LENGTH:
        winner = "Blue Snake Won!"
        running = False

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    if cube_list is not None:
        glCallList(cube_list)
    else:
        compile_cube()
    draw_snake(snake1)
    draw_snake(snake2)
    for food in green_foods:
        food.draw()
    for food in orange_foods:
        food.draw()
    for food in purple_foods:
        food.draw()
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, display[0], 0, display[1])
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    red_score_text = f"Red: {len(snake1.body)}"
    blue_score_text = f"Blue: {len(snake2.body)}"
    draw_text_top_left(red_score_text, 10, 10, small_font, (255, 0, 0, 255))
    red_text_height = small_font.size(red_score_text)[1]
    draw_text_top_left(blue_score_text, 10, 10 + red_text_height + 10, small_font, (0, 0, 255, 255))
    
    draw_text_top_right("Legend:", 10, 10, small_font, (255, 255, 255, 255))
    draw_text_top_right("Green: +1", 10, 30, small_font, (0, 255, 0, 255))
    draw_text_top_right("Orange: +3", 10, 50, small_font, (255, 165, 0, 255))
    draw_text_top_right("Purple: BOOST", 10, 70, small_font, (128, 0, 128, 255))
    
    draw_text_top_center("3D Snake Game", 10, title_font, (255, 255, 255, 255))
    draw_text_bottom_center("Goal: 100", 10, goal_font, (255, 255, 255, 255))
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    pygame.display.flip()
    clock.tick(10)

# ----- Victory Screen -----
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, display[0], 0, display[1])
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    draw_text_top_center("3D Snake Game", 10, title_font, (255, 255, 255, 255))
    win_color = (255, 0, 0, 255) if "Red" in winner else (0, 0, 255, 255) if "Blue" in winner else (255, 255, 255, 255)
    draw_text_center(winner, win_font, win_color)
    draw_text_bottom_center("Goal: 100", 10, goal_font, (255, 255, 255, 255))
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    pygame.display.flip()
    clock.tick(10)
