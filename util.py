# util.py
def is_in_bounds(pos, min_pos, max_pos):
    """Return True if all coordinates of pos are between min_pos and max_pos."""
    return all(min_pos <= pos[i] <= max_pos for i in range(3))

def lerp_color(c1, c2, t):
    """Linearly interpolate between two RGB colors."""
    return (c1[0] * (1 - t) + c2[0] * t,
            c1[1] * (1 - t) + c2[1] * t,
            c1[2] * (1 - t) + c2[2] * t)
