# main.py
import pygame
import time
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

from config import DISPLAY_SIZE, WINNING_LENGTH, MAX_GREEN_FOOD, MAX_ORANGE_FOOD, MAX_PURPLE_FOOD
from graphics import init_opengl, compile_diamond, compile_cube_list, draw_arena, \
                     draw_text_top_left, draw_text_top_right, draw_text_top_center, \
                     draw_text_bottom_center, draw_text_center
from food import spawn_green_food, spawn_orange_food, spawn_purple_food
from snake import Snake

# Initialize OpenGL and Pygame.
init_opengl()
compile_diamond()
compile_cube_list()

# Set up fonts.
# Using score_font for both scores and legend.
score_font = pygame.font.SysFont("Arial", 48, bold=True)
title_font = pygame.font.SysFont("Arial", 40, bold=True)
goal_font = pygame.font.SysFont("Arial", 36, bold=True)
win_font = pygame.font.SysFont("Arial", 36, bold=True)

# Delay and initialize audio.
print("Starting in 10 seconds...")
time.sleep(10)
pygame.mixer.init()
pygame.mixer.music.load("empressoflight.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

# Game variables.
mouse_dragging = False
green_food_eaten = 0
purple_cooldown = 0

# Initialize food lists.
green_foods = [spawn_green_food() for _ in range(MAX_GREEN_FOOD)]
orange_foods = []
purple_foods = []

# Create two snakes.
snake1 = Snake((1, 0, 0), [0, 0, 0])   # Red snake.
snake2 = Snake((0, 0, 1), [2, 2, 2])     # Blue snake.

clock = pygame.time.Clock()
running = True
winner = None

# Main game loop.
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

    # Update light position based on snake1's head.
    head_pos = snake1.body[0]
    glLightfv(GL_LIGHT0, GL_POSITION, [head_pos[0], head_pos[1], head_pos[2], 1.0])

    # Have each snake decide a new direction and then move.
    snake1.change_direction(snake2, green_foods, orange_foods, purple_foods)
    snake2.change_direction(snake1, green_foods, orange_foods, purple_foods)
    snake1.move(snake2)
    snake2.move(snake1)

    # Set thresholds for food collision.
    thresh1 = 1.5 if snake1.speed_boost_timer > 0 else 0.5
    thresh2 = 1.5 if snake2.speed_boost_timer > 0 else 0.5

    # Check for collisions with green food.
    for food in green_foods[:]:
        if (np.linalg.norm(snake1.body[0] - food.position) < thresh1 or
            np.linalg.norm(snake2.body[0] - food.position) < thresh2):
            if np.linalg.norm(snake1.body[0] - food.position) < thresh1:
                snake1.grow()
            else:
                snake2.grow()
            green_foods.remove(food)
            green_food_eaten += 1
            if green_food_eaten % 2 == 0 and len(orange_foods) < MAX_ORANGE_FOOD:
                orange_foods.append(spawn_orange_food())

    # Check for collisions with orange food.
    for food in orange_foods[:]:
        if (np.linalg.norm(snake1.body[0] - food.position) < thresh1 or
            np.linalg.norm(snake2.body[0] - food.position) < thresh2):
            if np.linalg.norm(snake1.body[0] - food.position) < thresh1:
                snake1.grow(3)
            else:
                snake2.grow(3)
            orange_foods.remove(food)

    # Check for collisions with purple food.
    for food in purple_foods[:]:
        if (np.linalg.norm(snake1.body[0] - food.position) < thresh1 or
            np.linalg.norm(snake2.body[0] - food.position) < thresh2):
            if np.linalg.norm(snake1.body[0] - food.position) < thresh1:
                snake1.speed_boost_timer = 30
            else:
                snake2.speed_boost_timer = 30
            purple_foods.remove(food)

    # Spawn purple food based on length difference.
    if abs(len(snake1.body) - len(snake2.body)) > 3 and not purple_foods and purple_cooldown <= 0:
        purple_foods.append(spawn_purple_food())
        purple_cooldown = 50

    # Ensure there is always enough green food.
    while len(green_foods) < MAX_GREEN_FOOD:
        green_foods.append(spawn_green_food())

    # If a snake is boosted, move it an extra time.
    if snake1.speed_boost_timer > 0:
        for _ in range(2):
            snake1.move(snake2)
        snake1.speed_boost_timer -= 1
    if snake2.speed_boost_timer > 0:
        for _ in range(2):
            snake2.move(snake1)
        snake2.speed_boost_timer -= 1

    # Check for a win.
    if len(snake1.body) >= WINNING_LENGTH:
        winner = "Red Snake Won!"
        running = False
    elif len(snake2.body) >= WINNING_LENGTH:
        winner = "Blue Snake Won!"
        running = False

    # Draw the scene.
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    draw_arena()
    snake1.draw()
    snake2.draw()
    for food in green_foods:
        food.draw()
    for food in orange_foods:
        food.draw()
    for food in purple_foods:
        food.draw()

    # Set up orthographic projection for overlay text.
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, DISPLAY_SIZE[0], 0, DISPLAY_SIZE[1])
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)

    # Draw scores.
    red_score_text = f"Red: {len(snake1.body)}"
    blue_score_text = f"Blue: {len(snake2.body)}"
    red_text_height = score_font.size(red_score_text)[1]

    draw_text_top_left(red_score_text, 20, 20, score_font, (255, 0, 0, 255))
    draw_text_top_left(blue_score_text, 20, 20 + red_text_height + 10, score_font, (0, 0, 255, 255))
    
    # Draw legend with larger, better formatted text.
    # We'll use score_font (48px) and 60-pixel vertical spacing.
    legend_x_offset = 10
    legend_y_offset = 10
    line_spacing = 60
    draw_text_top_right("Legend:", legend_x_offset, legend_y_offset, score_font, (255, 255, 255, 255))
    draw_text_top_right("Green: +1", legend_x_offset, legend_y_offset + line_spacing, score_font, (0, 255, 0, 255))
    draw_text_top_right("Orange: +3", legend_x_offset, legend_y_offset + 2 * line_spacing, score_font, (255, 165, 0, 255))
    draw_text_top_right("Purple: BOOST", legend_x_offset, legend_y_offset + 3 * line_spacing, score_font, (128, 0, 128, 255))
    
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

# Victory screen.
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, DISPLAY_SIZE[0], 0, DISPLAY_SIZE[1])
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
