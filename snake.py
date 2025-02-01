# snake.py
import random
import numpy as np
from math import pi, cos, sin
from config import MIN_POS, MAX_POS, MAX_ITER
from util import is_in_bounds, lerp_color

class Snake:
    def __init__(self, color, start_pos):
        self.color = color  # For example: (1, 0, 0) for red or (0, 0, 1) for blue.
        self.body = [np.array(start_pos)]
        self.direction = np.array(random.choice([
            [1, 0, 0], [-1, 0, 0],
            [0, 1, 0], [0, -1, 0],
            [0, 0, 1], [0, 0, -1]
        ]))
        self.grow_count = 0
        self.speed_boost_timer = 0

    def move(self, other):
        head = self.body[0]
        new_head = head + self.direction
        iter_count = 0
        while not is_in_bounds(new_head, MIN_POS, MAX_POS) and iter_count < MAX_ITER:
            # If no food information is available, pass None.
            self.change_direction(other, None, None, None)
            new_head = head + self.direction
            iter_count += 1
        if not is_in_bounds(new_head, MIN_POS, MAX_POS):
            safe = [d for d in ([np.array([1, 0, 0]), np.array([-1, 0, 0]),
                                  np.array([0, 1, 0]), np.array([0, -1, 0]),
                                  np.array([0, 0, 1]), np.array([0, 0, -1])])
                    if is_in_bounds(head + d, MIN_POS, MAX_POS)]
            self.direction = random.choice(safe) if safe else np.array([0, 0, 0])
            new_head = head + self.direction

        iter_count = 0
        while any(np.array_equal(new_head, seg) for seg in other.body) and iter_count < MAX_ITER:
            self.change_direction(other, None, None, None)
            new_head = head + self.direction
            iter_count += 1
        if any(np.array_equal(new_head, seg) for seg in other.body):
            new_head = head  # Fallback: do not move.
        self.body.insert(0, new_head)
        if self.grow_count > 0:
            self.grow_count -= 1
        else:
            self.body.pop()

    def grow(self, amount=1):
        self.grow_count += amount

    def change_direction(self, other, green_foods, orange_foods, purple_foods):
        possible_directions = [np.array([1, 0, 0]), np.array([-1, 0, 0]),
                               np.array([0, 1, 0]), np.array([0, -1, 0]),
                               np.array([0, 0, 1]), np.array([0, 0, -1])]
        head = self.body[0]

        # BOOST MODE: When speed boost is active, target food aggressively.
        if self.speed_boost_timer > 0 and green_foods is not None:
            target_food = None
            if orange_foods:
                target_food = min(orange_foods, key=lambda food: np.linalg.norm(food.position - head))
            elif green_foods:
                target_food = min(green_foods, key=lambda food: np.linalg.norm(food.position - head))
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
                if not is_in_bounds(new_pos, MIN_POS, MAX_POS):
                    continue
                if any(np.array_equal(new_pos, seg) for seg in self.body[1:]):
                    continue
                if any(np.array_equal(new_pos, seg) for seg in other.body):
                    continue
                chosen = candidate
                break
            if chosen is None:
                safe_dirs = [d for d in possible_directions if is_in_bounds(head + d, MIN_POS, MAX_POS) and
                             not any(np.array_equal(head + d, seg) for seg in self.body[1:]) and
                             not any(np.array_equal(head + d, seg) for seg in other.body)]
                if safe_dirs:
                    chosen = min(safe_dirs, key=lambda d: sum(abs(target_food.position - (head + d))))
            if chosen is not None:
                self.direction = chosen
            return

        # NORMAL MODE: Select target based on food availability and snake lengths.
        target_food = None
        if green_foods is not None:
            if purple_foods and len(self.body) + 3 <= len(other.body):
                target_food = min(purple_foods, key=lambda food: np.linalg.norm(food.position - head))
            elif orange_foods:
                target_food = min(orange_foods, key=lambda food: np.linalg.norm(food.position - head))
            elif green_foods:
                target_food = min(green_foods, key=lambda food: np.linalg.norm(food.position - head))
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

    def draw(self):
        """Draw the snake using the sphere drawing function from graphics.py."""
        from OpenGL.GL import glColor3f, glColor3fv, glPushMatrix, glTranslatef, glPopMatrix
        # Choose head color based on the snake's primary color.
        head_color = (0.5, 0, 0) if self.color == (1, 0, 0) else (0, 0, 0.5)
        if self.speed_boost_timer > 0:
            boost_color = (1, 0, 1) if self.color == (1, 0, 0) else (0, 1, 1)
            for i, segment in enumerate(self.body):
                t = i / (len(self.body) - 1) if len(self.body) > 1 else 0
                col = lerp_color(boost_color, self.color, t)
                if i == 0:
                    col = head_color
                glColor3f(*col)
                glPushMatrix()
                glTranslatef(*segment)
                # Import the sphere drawing function here to avoid circular imports.
                from graphics import draw_sphere
                draw_sphere(0.5 if i == 0 else 0.4)
                glPopMatrix()
        else:
            for i, segment in enumerate(self.body):
                col = head_color if i == 0 else self.color
                glColor3fv(col)
                glPushMatrix()
                glTranslatef(*segment)
                from graphics import draw_sphere
                draw_sphere(0.5 if i == 0 else 0.4)
                glPopMatrix()
