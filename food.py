# food.py
import random
import numpy as np
from config import MIN_POS, MAX_POS
from graphics import diamond_list, draw_diamond

class Food:
    def __init__(self, bonus=False, color=None):
        self.position = self.generate_food_position()
        self.bonus = bonus
        self.color = color if color is not None else ('orange' if bonus else 'green')
    
    def generate_food_position(self):
        return np.array([random.randint(MIN_POS, MAX_POS) for _ in range(3)])
    
    def draw(self):
        from OpenGL.GL import glColor3f, glPushMatrix, glTranslatef, glCallList, glPopMatrix
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
