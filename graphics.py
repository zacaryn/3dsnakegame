# graphics.py
import time
import pygame
import numpy as np
from math import pi, cos, sin
from OpenGL.GL import *
from OpenGL.GLU import *
from config import GRID_SIZE, DISPLAY_SIZE

# Global variables to hold display lists.
diamond_list = None
cube_list = None

def draw_diamond(size=0.3):
    """Draw an octahedron that represents a food item."""
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

def compile_diamond():
    """Compile a display list for the diamond if possible."""
    global diamond_list
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

def compile_cube():
    """Draw the arena cube with white, thick borders."""
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
    # Define edges of the cube.
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7)
    ]
    # Use a thicker line width.
    glLineWidth(5.0)
    # Draw white lines.
    glColor3f(1, 1, 1)
    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(vertices[vertex])
    glEnd()

def compile_cube_list():
    """Compile a display list for the arena cube if possible."""
    global cube_list
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

def draw_arena():
    """Draw the arena cube using white, thick borders."""
    glPushAttrib(GL_CURRENT_BIT | GL_LINE_BIT)
    # Override color and line width to ensure the cube is always white and thick.
    glColor3f(1, 1, 1)
    glLineWidth(5.0)
    if cube_list is not None:
        glCallList(cube_list)
    else:
        compile_cube_list()
    glPopAttrib()

def draw_cube():
    """Draw the arena cube with lighting disabled, then re-enable lighting."""
    glPushAttrib(GL_CURRENT_BIT)
    glColor3f(1, 1, 1)
    glDisable(GL_LIGHTING)
    if cube_list is not None:
        glCallList(cube_list)
    else:
        compile_cube()
    glEnable(GL_LIGHTING)
    glPopAttrib()

def draw_sphere(radius=0.4, segments=6):
    """Draw a sphere with lower resolution for performance."""
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

# ----- Text Drawing Functions -----
def draw_text_top_left(text, x_offset, y_offset, font, color):
    surf = font.render(text, True, color)
    data = pygame.image.tostring(surf, "RGBA", True)
    x = x_offset
    y = DISPLAY_SIZE[1] - y_offset - surf.get_height()
    glWindowPos2d(x, y)
    glDrawPixels(surf.get_width(), surf.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)

def draw_text_top_right(text, x_offset, y_offset, font, color):
    surf = font.render(text, True, color)
    data = pygame.image.tostring(surf, "RGBA", True)
    x = DISPLAY_SIZE[0] - x_offset - surf.get_width()
    y = DISPLAY_SIZE[1] - y_offset - surf.get_height()
    glWindowPos2d(x, y)
    glDrawPixels(surf.get_width(), surf.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)

def draw_text_top_center(text, y_offset, font, color):
    surf = font.render(text, True, color)
    data = pygame.image.tostring(surf, "RGBA", True)
    x = (DISPLAY_SIZE[0] - surf.get_width()) // 2
    y = DISPLAY_SIZE[1] - y_offset - surf.get_height()
    glWindowPos2d(x, y)
    glDrawPixels(surf.get_width(), surf.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)

def draw_text_bottom_center(text, y_offset, font, color):
    surf = font.render(text, True, color)
    data = pygame.image.tostring(surf, "RGBA", True)
    x = (DISPLAY_SIZE[0] - surf.get_width()) // 2
    y = y_offset
    glWindowPos2d(x, y)
    glDrawPixels(surf.get_width(), surf.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)

def draw_text_center(text, font, color):
    surf = font.render(text, True, color)
    data = pygame.image.tostring(surf, "RGBA", True)
    x = (DISPLAY_SIZE[0] - surf.get_width()) // 2
    y = (DISPLAY_SIZE[1] - surf.get_height()) // 2
    glWindowPos2d(x, y)
    glDrawPixels(surf.get_width(), surf.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)

def init_opengl():
    """Set up OpenGL and Pygame display settings."""
    pygame.init()
    pygame.display.set_caption("3D Snake Game")
    pygame.display.set_mode(DISPLAY_SIZE, pygame.DOUBLEBUF | pygame.OPENGL)
    
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    
    gluPerspective(45, (DISPLAY_SIZE[0] / DISPLAY_SIZE[1]), 0.1, 100.0)
    glTranslatef(0.0, 0.0, -40)
    
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.2, 0.2, 0.2, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  [0.8, 0.8, 0.8, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
